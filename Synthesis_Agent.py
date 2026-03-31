from Translator_Agent import TranslationAgent
from utils.logger import AgentLogger


class SynthesisAgent:
    """
    Agent 8: Synthesis Agent
    Assembles and translates the final output to the user's preferred language.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Synthesis Agent"
        self.translator = TranslationAgent(logger)

    def synthesize(self, content: str, target_language: str, metadata: dict) -> dict:
        """
        Synthesize and translate the final output.

        Args:
            content: Final English content from Editor Agent
            target_language: User's preferred output language
            metadata: Pipeline metadata (keywords, scores, notes)

        Returns:
            dict with final content (translated) and formatted output
        """
        self.logger.agent_start(
            self.agent_name, f"Synthesizing final output in '{target_language}'"
        )

        # Build the full formatted article
        keywords_str = ", ".join(metadata.get("seo_keywords", []))
        editor_notes = "; ".join(metadata.get("editor_notes", []))

        formatted_content = f"""---
**SEO Keywords:** {keywords_str}
**Fact Check:** {metadata.get('fact_check_summary', 'Verified')}
**Brand Alignment Score:** {metadata.get('brand_alignment_score', 'N/A')}/10
**Editor Notes:** {editor_notes}
---

{content}"""

        # Translate to target language if not English
        if target_language.lower() != "english":
            translated = self.translator.from_english(formatted_content, target_language)
        else:
            translated = formatted_content

        result = {
            "content": translated,
            "language": target_language,
            "word_count": len(translated.split()),
        }

        self.logger.agent_end(
            self.agent_name,
            f"Synthesis complete. Language: {target_language} | Words: {result['word_count']}",
        )
        return result