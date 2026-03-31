import json
import google.genai as genai
from utils.logger import AgentLogger

SYSTEM_PROMPT = """You are a language detection specialist.
Given a text input, identify its language.
Respond ONLY with a JSON object in this exact format:
{"language": "<language_name>", "language_code": "<iso_code>", "confidence": <0.0-1.0>}

Examples:
- English text → {"language": "english", "language_code": "en", "confidence": 0.99}
- Hindi text → {"language": "hindi", "language_code": "hi", "confidence": 0.98}
- Telugu text → {"language": "telugu", "language_code": "te", "confidence": 0.97}
"""

class LanguageDetectorAgent:
    """
    Agent 1: Language Detector
    Detects input language so subsequent agents know how to handle the query.
    """

    def __init__(self, logger: AgentLogger):
        self.logger = logger
        self.agent_name = "Language Detector Agent"
        
        # Initialize the Gemini client
        # gemini-3-flash-preview is ideal here: it's incredibly fast and perfect for classification
        self.model_name = "gemini-3-flash-preview"
        self.client = genai.Client(api_key="")

    def detect(self, text: str) -> str:
        """
        Detect the language of the input text.

        Args:
            text: Raw user input in any language

        Returns:
            language name as string (e.g. "english", "hindi", "telugu")
        """
        self.logger.agent_start(self.agent_name, f"Detecting language of: '{text[:60]}...'")

        try:
            # Generate content, enforcing JSON output natively
            response = self.client.models.generate_content(
            model=self.model_name,
            contents=f"Detect the language of this text:\n\n{text}",
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=200
    )
)

            raw = response.text.strip()
            raw=raw.replace("```json","").replace("```","").strip()
            parsed = json.loads(raw)
            
            language = parsed.get("language", "english").lower()
            confidence = parsed.get("confidence", 1.0)
            
            self.logger.agent_end(
                self.agent_name, f"Detected '{language}' with confidence {confidence}"
            )
            return language

        except json.JSONDecodeError:
            # Fallback if the JSON is somehow malformed
            self.logger.agent_end(self.agent_name, "Detection failed (JSON Error), defaulting to 'english'")
            return "english"
        except Exception as e:
            # Fallback for general API or network errors
            self.logger.agent_end(self.agent_name, f"Detection failed ({str(e)}), defaulting to 'english'")
            return "english"
