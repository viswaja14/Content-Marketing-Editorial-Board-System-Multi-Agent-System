"""
Content Writer Agent
====================
Generates the initial draft of marketing content based on the research query using Google Gemini.
Produces a structured blog/article with introduction, body, and conclusion.
"""

import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT = """You are an expert content marketing writer with 10+ years of experience
writing compelling blog posts, whitepapers, and marketing articles.

When given a research topic/query, you will:
1. Write a comprehensive, well-structured article (600-900 words)
2. Include a compelling headline
3. Structure with clear sections: Introduction, 3-4 body sections, Conclusion
4. Use data-driven claims where relevant
5. Write in an engaging, readable tone (8th-grade reading level)
6. Include a clear call-to-action at the end

Format your response with markdown headings (##, ###).
Do NOT include SEO metadata yet — that will be handled by a specialist."""

class ContentWriterAgent:
    """
    Agent 3: Content Writer
    Generates the initial draft marketing content from the English query.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Content Writer Agent"
        # Using Gemini 3.1 Pro here because it excels at long-form creative generation and complex reasoning
        self.model_name = "gemini-3.1-pro-preview"
        # Initialize the client once
        self.client = genai.Client(api_key="")

    def write(self, query: str) -> str:
        """
        Generate initial content draft.

        Args:
            query: Research/marketing query in English

        Returns:
            Initial draft as markdown string
        """
        self.logger.agent_start(self.agent_name, f"Writing draft for: '{query}'")

        user_prompt = f"""Write a comprehensive marketing blog post for the following topic:

Topic: {query}

Produce a full draft with headline, introduction, body sections, and conclusion.
Include relevant statistics, examples, and actionable insights."""

        try:
            # Generate the content draft using chat-style contents
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,  # A temperature of 0.7 allows for creativity while staying on topic
                    max_output_tokens=2048
                )
            )

            draft = response.text.strip()
            word_count = len(draft.split())
            
            self.logger.agent_end(self.agent_name, f"Draft complete: {word_count} words")
            return draft

        except Exception as e:
            # Graceful error handling in case the API call fails
            self.logger.agent_end(self.agent_name, f"Content generation failed: {str(e)}")
            return f"Error generating draft. Please try again. Details: {str(e)}"
