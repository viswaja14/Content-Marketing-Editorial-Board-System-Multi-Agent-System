
import os
import json
import time
from datetime import datetime
from typing import TypedDict
from langgraph.graph import StateGraph, END
import google.genai as genai

# Import your existing Gemini agents
from Language_Detector_Agent import LanguageDetectorAgent
from Translator_Agent import TranslationAgent
from Content_Writer_Agent import ContentWriterAgent
from Editor_Agent import EditorAgent
from Fact_Checker_Agent import FactCheckerAgent
from SEO_Specialist_Agent import SEOSpecialistAgent
from Synthesis_Agent import SynthesisAgent
from Brand_Voice_Agent import BrandVoiceAgent
from utils.logger import AgentLogger
from utils.report_generator import ReportGenerator

from dotenv import load_dotenv
load_dotenv()
api_key=os.getenv("GOOGLE_API_KEY")

# ==========================================
# 1. Define the State (The Shared Memory)
# ==========================================
class EditorialState(TypedDict):
    query: str
    output_language: str
    detected_lang: str
    english_query: str
    draft: str
    seo_keywords: list
    # --- Fact Checking Loop Variables ---
    fact_issues_resolved: int
    accuracy_score: int
    fact_issues: list
    retry_count: int
    # ------------------------------------
    brand_score: int
    editor_notes: list
    quality_score: int
    final_content: str
    pipeline_start: float


# ==========================================
# 2. Build the LangGraph Orchestrator
# ==========================================
class LangGraphOrchestrator:
    def __init__(self, brand_guidelines: dict = None):
        self.logger = AgentLogger()
        self.brand_guidelines = brand_guidelines or self._default_brand_guidelines()
        

        # Initialize Agents
        self.language_detector = LanguageDetectorAgent(self.logger)
        self.translator = TranslationAgent(self.logger)
        self.content_writer = ContentWriterAgent(self.logger)
        self.seo_specialist = SEOSpecialistAgent(self.logger)
        self.fact_checker = FactCheckerAgent(self.logger)
        self.brand_voice = BrandVoiceAgent(self.logger, self.brand_guidelines)
        self.editor = EditorAgent(self.logger)
        self.synthesis = SynthesisAgent(self.logger)
        self.report_generator = ReportGenerator()

        # Build the Graph matching the visual diagram
        self.graph = self._build_graph()

    def _default_brand_guidelines(self) -> dict:
        return {
            "tone": "professional yet approachable",
            "style": "clear, concise, and informative",
            "avoid": ["jargon", "passive voice", "overly technical language"],
            "prefer": ["active voice", "data-driven claims", "actionable insights"],
            "target_audience": "business professionals and decision-makers",
        }

    # --- Node 1 & 2 ---
    def detect_language(self, state: EditorialState):
        lang = self.language_detector.detect(state["query"])
        return {"detected_lang": lang}

    def translate_query(self, state: EditorialState):
        eng_query = self.translator.to_english(state["query"], state["detected_lang"])
        return {"english_query": eng_query}

    # --- Node 3: Content Writer (Now receives Fact-Check feedback) ---
    def write_content(self, state: EditorialState):
        query_to_use = state["english_query"]
        
        # If this is a retry loop, append the factual issues to the prompt
        if state.get("retry_count", 0) > 0 and state.get("fact_issues"):
            issues_str = json.dumps(state["fact_issues"], indent=2)
            query_to_use += f"\n\nCRITICAL FACT-CHECK ISSUES TO FIX:\n{issues_str}\n\nPlease revise the draft to ensure all claims are perfectly accurate."
            self.logger.log_step("System", f"Initiating Retry #{state['retry_count']}")

        draft = self.content_writer.write(query_to_use)
        return {"draft": draft}

    # --- Node 4 ---
    def optimize_seo(self, state: EditorialState):
        result = self.seo_specialist.optimize(state["draft"], state["english_query"])
        return {"draft": result.get("content", state["draft"]), "seo_keywords": result.get("keywords", [])}

    # --- Node 5: Fact Checker ---
    def check_facts(self, state: EditorialState):
        result = self.fact_checker.check(state["draft"])
        resolved = len(result.get("corrections", []))
        
        return {
            "draft": result.get("content", state["draft"]), 
            "fact_issues_resolved": state.get("fact_issues_resolved", 0) + resolved,
            "accuracy_score": result.get("accuracy_score", 0),
            "fact_issues": result.get("issues", []),
            "retry_count": state.get("retry_count", 0) + 1  # Increment the retry counter
        }

    # --- Node 6 & 7 ---
    def align_brand(self, state: EditorialState):
        result = self.brand_voice.align(state["draft"])
        return {"draft": result.get("content", state["draft"]), "brand_score": result.get("brand_score", 0)}

    def edit_content(self, state: EditorialState):
        result = self.editor.review(state["draft"])
        return {
            "draft": result.get("content", state["draft"]),
            "editor_notes": result.get("notes", []),
            "quality_score": result.get("quality_score", 0)
        }

    # --- Node 8 ---
    def synthesize_output(self, state: EditorialState):
        metadata = {
            "seo_keywords": state.get("seo_keywords", []),
            "fact_check_summary": f"Resolved {state.get('fact_issues_resolved', 0)} issues over {state.get('retry_count', 1)} passes.",
            "brand_alignment_score": state.get("brand_score", "N/A"),
            "editor_notes": state.get("editor_notes", [])
        }
        result = self.synthesis.synthesize(state["draft"], state["output_language"], metadata)
        return {"final_content": result["content"]}

    # --- Conditional Routing Logic (The Diamond in your diagram) ---
    def evaluate_accuracy(self, state: EditorialState):
        """
        Routes the graph based on accuracy_score and max retries.
        """
        score = state.get("accuracy_score", 0)
        retries = state.get("retry_count", 0)
        
        self.logger.log_step("Router", f"Evaluating Fact Check: Accuracy = {score}/10 | Retry Count = {retries}/3")
        
        # Pass condition: Score >= 7 OR max retries hit
        if score >= 7 or retries >= 3:
            if score < 7 and retries >= 3:
                self.logger.log_step("Router", "Max retries hit. Pushing to Brand Voice with current accuracy.")
            else:
                self.logger.log_step("Router", "Accuracy passed. Routing to Brand Voice.")
            return "pass"
        
        # Retry condition
        self.logger.log_step("Router", "Accuracy failed. Routing back to Content Writer.")
        return "retry"

    # --- Graph Assembly ---
    def _build_graph(self):
        workflow = StateGraph(EditorialState)

        # Add Nodes
        workflow.add_node("detector", self.detect_language)
        workflow.add_node("translator", self.translate_query)
        workflow.add_node("writer", self.write_content)
        workflow.add_node("seo", self.optimize_seo)
        workflow.add_node("fact_checker", self.check_facts)
        workflow.add_node("brand", self.align_brand)
        workflow.add_node("editor", self.edit_content)
        workflow.add_node("synthesis", self.synthesize_output)

        # Set linear edges for the first half
        workflow.set_entry_point("detector")
        workflow.add_edge("detector", "translator")
        workflow.add_edge("translator", "writer")
        workflow.add_edge("writer", "seo")
        workflow.add_edge("seo", "fact_checker")

        # The Conditional Diamond
        workflow.add_conditional_edges(
            "fact_checker",
            self.evaluate_accuracy,
            {
                "retry": "writer",  # Loop back
                "pass": "brand"     # Move forward
            }
        )

        # Set linear edges for the second half
        workflow.add_edge("brand", "editor")
        workflow.add_edge("editor", "synthesis")
        workflow.add_edge("synthesis", END)

        return workflow.compile()

    def run(self, query: str, output_language: str = "english") -> dict:
        # Prevent failure cases where the input query is empty or 0
        if not query or str(query).strip() in ["", "0"]:
            self.logger.log_step("System", "Error: Input query cannot be zero or empty.")
            raise ValueError("A valid research query must be provided.")

        self.logger.start_pipeline(query, output_language)
        
        initial_state = {
            "query": query,
            "output_language": output_language.lower(),
            "retry_count": 0,
            "fact_issues_resolved": 0,
            "pipeline_start": time.time()
        }

        final_state = self.graph.invoke(initial_state)

        elapsed = round(time.time() - final_state["pipeline_start"], 2)

        result = {
            "query": final_state["query"],
            "detected_language": final_state.get("detected_lang", "english"),
            "output_language": final_state["output_language"],
            "final_content": final_state.get("final_content", ""),
            "metadata": {
                "pipeline_duration_seconds": elapsed,
                "word_count": len(final_state.get("final_content", "").split()),
                "seo_keywords": final_state.get("seo_keywords", []),
                "fact_issues_resolved": final_state.get("fact_issues_resolved", 0),
                "brand_alignment_score": final_state.get("brand_score", "N/A"),
                "editor_notes": final_state.get("editor_notes", []),
                "fact_check_retries": final_state.get("retry_count", 1) - 1, # -1 because the first pass isn't a retry
                "final_accuracy_score": final_state.get("accuracy_score", "N/A"),
                "timestamp": datetime.now().isoformat(),
            },
            "agent_logs": self.logger.get_logs(),
        }

        report_path = self.report_generator.save(result)
        result["report_path"] = report_path
        
        self.logger.end_pipeline(elapsed)
        return result

if __name__ == "__main__":
    orchestrator = LangGraphOrchestrator()
    try:
        result = orchestrator.run(
            query="Write an article about the current state of quantum computing adoption in enterprise software.", 
            output_language="english"
        )
        print(f"\n✅ Graph Pipeline complete. Fact Check Retries: {result['metadata']['fact_check_retries']}")
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")