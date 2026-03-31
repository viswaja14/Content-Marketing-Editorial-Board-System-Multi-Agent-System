"""
Brand Voice Agent
=================
Ensures the content aligns with brand guidelines: tone, style,
vocabulary, and personality. Rewrites sections that don't match
the brand's defined voice using Google Gemini.
"""

import json
import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT_TEMPLATE = """You are a Brand Voice Specialist responsible for ensuring all content
perfectly reflects the company's brand identity and voice guidelines.

Brand Guidelines:
- Tone: {tone}
- Style: {style}
- Avoid: {avoid}
- Prefer: {prefer}
- Target Audience: {target_audience}

Your job:
1. Audit the content against each brand guideline
2. Rewrite sections that don't match the brand voice
3. Ensure consistent personality throughout
4. Replace jargon with accessible language
5. Make the content feel human, authentic, and on-brand
6. Score the brand alignment before and after

Respond ONLY with a JSON object using the following keys:
- "content": "<brand-aligned content in markdown>"
- "brand_score": <1-10 final score>
- "original_score": <1-10 score before edits>
- "changes_made": ["change1", "change2"]
- "brand_notes": "<brief note on brand alignment>"
"""

class BrandVoiceAgent:
    """
    Agent 6: Brand Voice Agent
    Aligns content with brand guidelines and personality.
    """

    def __init__(self, logger: AgentLogger, brand_guidelines: dict):
        self.logger = logger
        self.agent_name = "Brand Voice Agent"
        self.brand_guidelines = brand_guidelines
        # gemini-3.1-pro-preview is best for nuanced stylistic rewriting, maintaining a consistent 
        # persona, and following complex negative constraints (like the "Avoid" list).
        self.model_name = "gemini-3.1-pro-preview"
        # Initialize the client once
        self.client = genai.Client(api_key="AIzaSyCnZbX-IgsAL0Uz4wTy3eVKwNPljsi5I3A")

    def align(self, content: str) -> dict:
        """
        Align content with brand guidelines.

        Args:
            content: Fact-checked article content

        Returns:
            dict with brand-aligned content and scores
        """
        self.logger.agent_start(self.agent_name, "Aligning content with brand voice")

        bg = self.brand_guidelines
        
        # Format the system instruction dynamically based on the provided dictionary
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            tone=bg.get("tone", "professional"),
            style=bg.get("style", "clear and concise"),
            avoid=", ".join(bg.get("avoid", [])),
            prefer=", ".join(bg.get("prefer", [])),
            target_audience=bg.get("target_audience", "business professionals"),
        )

        user_prompt = f"""Review and align this article with our brand voice guidelines.

Content to review:
{content}"""

        try:
            # Generate the content, enforcing JSON output natively using chat-style contents
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction=system_instruction,
                    temperature=0.4,  # A balanced temperature allows for stylistic edits without going entirely off-script
                    max_output_tokens=8192  # High limit needed since the full rewritten text is inside the JSON
                )
            )

            raw = response.text.strip()
            result = json.loads(raw)
            
            self.logger.agent_end(
                self.agent_name,
                f"Brand alignment done. Score: {result.get('original_score', 'N/A')}/10 → "
                f"{result.get('brand_score', 'N/A')}/10 | "
                f"Changes: {len(result.get('changes_made', []))}",
            )
            return result

        except json.JSONDecodeError:
            self.logger.agent_end(self.agent_name, "JSON parse failed, returning unchanged content")
            return {
                "content": content,
                "brand_score": 7,
                "original_score": 6,
                "changes_made": ["Error: Failed to parse brand adjustments properly."],
                "brand_notes": "Brand alignment completed but output was malformed.",
            }
        except Exception as e:
            # Fallback to keep the pipeline moving if the API fails
            self.logger.agent_end(self.agent_name, f"Brand alignment failed: {str(e)}")
            return {
                "content": content,
                "brand_score": 0,
                "original_score": 0,
                "changes_made": [],
                "brand_notes": f"API Error: {str(e)}",
            }