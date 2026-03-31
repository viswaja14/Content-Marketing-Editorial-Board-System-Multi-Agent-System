import json
import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT = """You are an expert SEO specialist with deep knowledge of search engine optimization,
keyword research, and content structure for maximum organic reach.

Given a draft article, you will:
1. Identify 5-8 primary and secondary SEO keywords relevant to the topic
2. Naturally integrate keywords into the content (2-3% keyword density)
3. Optimize heading hierarchy (H1, H2, H3)
4. Add a meta description (155 characters max)
5. Improve readability (shorter sentences, transition words, bullet points where appropriate)
6. Add an FAQ section at the end with 3 common questions and answers
7. Suggest internal link anchors with [LINK: anchor text] placeholders

Respond ONLY with a JSON object using the following keys:
- "content": "<optimized article in markdown>"
- "meta_description": "<155 char meta description>"
- "keywords": ["keyword1", "keyword2"]
- "keywords_added": <number of keywords integrated>
- "readability_score": <1-10>
- "seo_improvements": ["improvement1", "improvement2"]
"""

class SEOSpecialistAgent:
    """
    Agent 4: SEO Specialist
    Optimizes draft content for search engine performance.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "SEO Specialist Agent"
        # gemini-3.1-pro-preview is crucial here. It handles large context windows and 
        # complex multi-step reasoning (editing, analyzing density, outputting JSON) 
        # much better than smaller models.
        self.model_name = "gemini-3.1-pro-preview"
        # Initialize the client once
        self.client = genai.Client(api_key="AIzaSyCnZbX-IgsAL0Uz4wTy3eVKwNPljsi5I3A")

    def optimize(self, draft: str, query: str) -> dict:
        """
        Optimize content for SEO.

        Args:
            draft: Initial content draft
            query: Original research query (for keyword context)

        Returns:
            dict with optimized content, keywords, and metadata
        """
        self.logger.agent_start(self.agent_name, "Optimizing content for SEO")

        user_prompt = f"""Optimize this marketing article for SEO.
                    
Original Topic/Query: {query}

Draft Content:
{draft}"""

        try:
            # Enforce JSON output natively using chat-style contents
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,  # Low temperature ensures strict adherence to SEO rules and JSON formatting
                    max_output_tokens=8192  # High token limit needed because the entire rewritten article is inside the JSON
                )
            )

            raw = response.text.strip()
            result = json.loads(raw)
            
            self.logger.agent_end(
                self.agent_name,
                f"SEO done. Keywords: {result.get('keywords', [])[:3]}... | "
                f"Readability: {result.get('readability_score', 'N/A')}/10",
            )
            return result

        except json.JSONDecodeError:
            self.logger.agent_end(self.agent_name, "JSON parse failed, returning raw content")
            return {
                "content": raw if 'raw' in locals() else draft,
                "meta_description": "",
                "keywords": [],
                "keywords_added": 0,
                "readability_score": 7,
                "seo_improvements": ["Error: Failed to parse SEO optimizations properly."],
            }
        except Exception as e:
            # Fallback to keep the pipeline moving if the API hits a snag
            self.logger.agent_end(self.agent_name, f"SEO optimization failed: {str(e)}")
            return {
                "content": draft, 
                "meta_description": "",
                "keywords": [],
                "keywords_added": 0,
                "readability_score": 0,
                "seo_improvements": [f"API Error: {str(e)}"],
            }