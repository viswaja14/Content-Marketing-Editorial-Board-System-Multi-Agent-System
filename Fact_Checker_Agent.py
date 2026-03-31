"""
Fact Checker Agent
==================
Verifies factual claims in the content. Uses Gemini's native Google Search 
grounding to validate statistics, dates, and assertions.
Flags inaccuracies and suggests corrections.
"""

import json
import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT = """You are a rigorous fact-checking journalist with expertise in verifying 
marketing content accuracy.

Your job is to:
1. Identify all factual claims in the content (statistics, dates, company claims, research citations)
2. Evaluate each claim's accuracy based on your knowledge and search results.
3. Flag any claims that are:
   - Outdated (use old statistics)
   - Exaggerated or unsupported
   - Potentially misleading
   - Missing context
4. Provide corrected versions of flagged claims
5. Add appropriate hedging language to uncertain claims ("studies suggest", "according to research")

Use your built-in Google Search tool to verify specific statistics and recent data when needed.

Respond ONLY with a JSON object using the following structure:
{
  "content": "<content with corrections applied>",
  "issues": [
    {"claim": "original claim", "issue": "why it's problematic", "severity": "low|medium|high"}
  ],
  "corrections": [
    {"original": "wrong claim", "corrected": "accurate claim", "source": "source info"}
  ],
  "summary": "<2-sentence summary of fact-checking results>",
  "accuracy_score": <1-10>
}
"""

class FactCheckerAgent:
    """
    Agent 5: Fact Checker
    Verifies claims and corrects inaccuracies using Google Search Grounding.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Fact Checker Agent"
        # gemini-3.1-pro-preview is required here. It is best equipped to handle the complex 
        # cross-referencing required between the draft text and web search results.
        self.model_name = "gemini-3.1-pro-preview"
        # Initialize the client once
        self.client = genai.Client(api_key="")

    def check(self, content: str) -> dict:
        """
        Fact-check the content.

        Args:
            content: SEO-optimized article content

        Returns:
            dict with corrected content, issues, corrections, and summary
        """
        self.logger.agent_start(self.agent_name, "Verifying factual claims in content via Google Search")

        user_prompt = f"""Fact-check this marketing article. 
Verify key statistics, claims, and assertions. Use your Google Search tool for recent data.

Content to fact-check:
{content}"""

        try:
            # Enforce JSON output and manage generation config using chat-style contents
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,  # Keep temperature very low to prevent hallucinated facts
                    max_output_tokens=8192,
                    tools=[{"google_search": {}}],  # This enables native web search access
                )
            )

            raw = response.text.strip()
            result = json.loads(raw)

            if isinstance(result,list):
                result=result[0] if len(result) >0 else{}
            
            issues_count = len(result.get("issues", []))
            corrections_count = len(result.get("corrections", []))
            
            self.logger.agent_end(
                self.agent_name,
                f"Fact-check complete. Issues: {issues_count}, Corrections: {corrections_count} | "
                f"Accuracy score: {result.get('accuracy_score', 'N/A')}/10",
            )
            return result

        except json.JSONDecodeError:
            self.logger.agent_end(self.agent_name, "JSON parse failed, returning unchanged content")
            return {
                "content": content,
                "issues": [],
                "corrections": [],
                "summary": "Fact check completed, but failed to format response properly. Content unchanged.",
                "accuracy_score": 0,
            }
        except Exception as e:
            self.logger.agent_end(self.agent_name, f"Fact-checking failed: {str(e)}")
            return {
                "content": content,
                "issues": [],
                "corrections": [],
                "summary": f"Fact check skipped due to API error: {str(e)}",
                "accuracy_score": 0,
            }
