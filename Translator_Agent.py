import google.genai as genai
import os
import json
from utils.logger import AgentLogger

SYSTEM_PROMPT_TO_EN = """You are a professional translator. 
Translate the given text to English accurately, preserving the original meaning, context, and intent.
Return ONLY the translated text with no explanation, no preamble, no quotes."""

SYSTEM_PROMPT_FROM_EN = """You are a professional translator.
Translate the given English content to {target_language}.
Preserve all technical terms, formatting, and markdown structure.
The translation should sound natural in {target_language} — not like a literal translation.
Return ONLY the translated content."""

class TranslationAgent:
    """
    Agent 2: Translation Agent
    - Translates input query → English
    - Translates final output → user's preferred language (called by Synthesis Agent)
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Translation Agent"
        self.model_name = "gemini-3-flash-preview"
        # Initialize client once
        self.client = genai.Client(api_key="")

    def to_english(self, text: str, source_language: str) -> str:
        if source_language.lower() == "english":
            self.logger.agent_end(self.agent_name, "Already in English, no translation needed")
            return text

        self.logger.agent_start(self.agent_name, f"Translating from {source_language} → English")

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Translate this {source_language} text to English:\n\n{text}",
                config=genai.types.GenerationConfig(
                    system_instruction=SYSTEM_PROMPT_TO_EN,
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )

            translated = response.text.strip()
            self.logger.agent_end(self.agent_name, f"Translated to English: '{translated[:80]}...'")
            return translated

        except Exception as e:
            self.logger.agent_end(self.agent_name, f"Translation to English failed: {str(e)}")
            return text

    def from_english(self, text: str, target_language: str) -> str:
        if target_language.lower() == "english":
            return text

        self.logger.agent_start(self.agent_name, f"Translating from English → {target_language}")

        system_instruction = SYSTEM_PROMPT_FROM_EN.format(target_language=target_language)

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"Translate the following English content to {target_language}:\n\n{text}",
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=4096
                )
            )

            translated = response.text.strip()
            self.logger.agent_end(
                self.agent_name, f"Translated to {target_language} ({len(translated.split())} words)"
            )
            return translated

        except Exception as e:
            self.logger.agent_end(self.agent_name, f"Translation to {target_language} failed: {str(e)}")
            return text
