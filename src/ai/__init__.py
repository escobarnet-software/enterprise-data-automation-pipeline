"""AI processing engine: Groq LLM extraction + rule-based fallback."""
from .prompts import CLASSIFY_PROMPT, EXTRACT_PROMPT
from .groq_client import GroqExtractor, RuleBasedExtractor, get_extractor

__all__ = ["CLASSIFY_PROMPT", "EXTRACT_PROMPT", "GroqExtractor", "RuleBasedExtractor", "get_extractor"]
