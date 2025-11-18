from __future__ import annotations

import logging
import os
from functools import lru_cache

from google import genai

LOGGER = logging.getLogger(__name__)


class LLMNotConfigured(RuntimeError):
    """Raised when the Gemini client cannot be initialised."""


def _get_google_api_key() -> str | None:
    # Prefer settings.py if available
    try:
        from settings import get_settings  # type: ignore

        settings = get_settings()
        return getattr(settings, "google_api_key", None) or os.getenv("GOOGLE_API_KEY")
    except Exception:  # pragma: no cover - optional
        return os.getenv("GOOGLE_API_KEY")


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    api_key = _get_google_api_key()
    if not api_key:
        raise LLMNotConfigured("GOOGLE_API_KEY is not set.")
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:  # pragma: no cover - depends on SDK internals
        raise LLMNotConfigured("Failed to create Gemini client.") from exc

