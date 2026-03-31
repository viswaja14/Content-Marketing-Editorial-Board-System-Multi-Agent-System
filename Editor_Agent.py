import json
import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT = """You are a senior content editor at a leading marketing agency with 15+ years 
of experience editing award-winning marketing content.

Your final editorial review includes:
1. Grammar, punctuation, and spelling corrections
2. Sentence flow and paragraph coherence
3. Logical structure and argument progression
4. Removing redundancy and filler phrases
5. Strengthening the headline and subheadings
6. Ensuring the CTA is compelling and clear
7. Final readability check (target: Flesch-Kincaid Grade 8-10)
8. Adding/removing content to hit ideal length (600-900 words)

Respond ONLY with a JSON object using the following keys:
- "content": "<final polished content in markdown>"
- "notes": ["editorial note 1", "editorial note 2"]
- "quality_score": <1-10>
- "word_count": <final word count>
- "headline": "<final optimized headline>"
- "summary": "<2-3 sentence executive summary of the article>"
"""

class EditorAgent:
    """
    Agent 7: Editor Agent
    Final editorial review, grammar, flow, and quality assurance.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Editor Agent"
        # gemini-3.1-pro-preview is the perfect fit here for comprehensive document review,
        # catching subtle grammatical errors, and restructuring long-form text.
        self.model_name = "gemini-3.1-pro-preview"
        # Initialize the client once
        self.client = genai.Client(api_key="AIzaSyCnZbX-IgsAL0Uz4wTy3eVKwNPljsi5I3A")

    def review(self, content: str) -> dict:
        """
        Perform final editorial review.
        """
        self.logger.agent_start(self.agent_name, "Performing final editorial review")

        user_prompt = f"""Perform a final editorial review on this marketing article.
Polish it to publication-ready quality.

Content to review:
{content}"""

        try:
            # Enforce JSON output and manage generation config using chat-style contents
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.3,  # Low temperature ensures strict adherence to grammar rules without overly altering the established brand voice
                    max_output_tokens=8192
                )
            )

            raw = response.text.strip()
            result = json.loads(raw)
            
            self.logger.agent_end(
                self.agent_name,
                f"Editorial review complete. Quality score: {result.get('quality_score', 'N/A')}/10 | "
                f"Word count: {result.get('word_count', 'N/A')}",
            )
            return result

        except json.JSONDecodeError:
            self.logger.agent_end(self.agent_name, "JSON parse failed, returning as-is")
            return {
                "content": content,
                "notes": ["Error: Final review completed but JSON output was malformed."],
                "quality_score": 8,
                "word_count": len(content.split()),
                "headline": "Review Complete",
                "summary": "Article review was attempted but failed to parse.",
            }
        except Exception as e:
            self.logger.agent_end(self.agent_name, f"Editorial review failed: {str(e)}")
            return {
                "content": content,
                "notes": [f"API Error: {str(e)}"],
                "quality_score": 0,
                "word_count": len(content.split()),
                "headline": "Error",
                "summary": "Failed to complete editorial review due to API error.",
            }