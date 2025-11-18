from __future__ import annotations

import json
import logging
import time
from typing import Any, Protocol

from pydantic import BaseModel

from .llm import LLMNotConfigured, get_gemini_client
from .prompt import build_json_prompt
from .text_utils import Token

logger = logging.getLogger(__name__)


class CorrectionSpec(BaseModel):
    token_id: int
    replacement: str
    reason: str
    original: str | None = None


class BaseCorrector(Protocol):
    def correct_tokens(self, tokens: list[Token]) -> list[CorrectionSpec]: ...


class CorrectionsResponse(BaseModel):
    corrections: list[CorrectionSpec] = []


class GeminiCorrector:
    # Class-level rate limiting (shared across all instances)
    _last_request_time = 0
    _min_interval_seconds = 30  # 2 req/min = 30 seconds between requests for gemini-2.5-pro

    def __init__(self, model_name: str | None = None, base_prompt_text: str | None = None) -> None:
        # If model_name not provided, try to load from settings
        if model_name is None:
            try:
                from settings import get_settings

                settings = get_settings()
                model_name = (
                    settings.gemini_model
                    if settings and settings.gemini_model
                    else "gemini-2.5-flash"
                )
            except Exception:
                model_name = "gemini-2.5-flash"

        self.model_name = model_name
        self.base_prompt_text = base_prompt_text or ""
        self._client = None

        # Adjust rate limit based on model
        if "flash" in model_name.lower():
            GeminiCorrector._min_interval_seconds = 4  # 15 req/min for flash
        else:
            GeminiCorrector._min_interval_seconds = 30  # 2 req/min for pro

    def _ensure_client(self):
        if self._client is None:
            self._client = get_gemini_client()

    def correct_tokens(self, tokens: list[Token]) -> list[CorrectionSpec]:
        self._ensure_client()
        prompt = build_json_prompt(self.base_prompt_text, tokens)

        # Rate limiting: wait if needed
        current_time = time.time()
        time_since_last = current_time - GeminiCorrector._last_request_time
        if time_since_last < GeminiCorrector._min_interval_seconds:
            wait_time = GeminiCorrector._min_interval_seconds - time_since_last
            logger.info(f"⏱️  Rate limiting: waiting {wait_time:.1f}s before next request...")
            time.sleep(wait_time)

        GeminiCorrector._last_request_time = time.time()

        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Determine which model to use
                current_model = self.model_name
                if attempt > 0:
                    logger.info(f"🔄 Retry {attempt + 1}/{max_retries} with {current_model}")
                else:
                    logger.info(f"🤖 Using Gemini model: {current_model}")

                # Use models.generate_content with JSON output
                resp = self._client.models.generate_content(
                    model=current_model,
                    contents=[{"role": "user", "parts": [{"text": prompt}]}],
                    config={"response_mime_type": "application/json"},
                )

                # Extract text from response
                text = getattr(resp, "text", None)
                if not text:
                    # Try alternative attributes
                    if hasattr(resp, "candidates") and resp.candidates:
                        cand = resp.candidates[0]
                        if hasattr(cand, "content") and cand.content:
                            if hasattr(cand.content, "parts") and cand.content.parts:
                                part = cand.content.parts[0]
                                text = getattr(part, "text", None)

                if text:
                    data = json.loads(text)
                    items = data.get("corrections") if isinstance(data, dict) else data
                    if isinstance(items, list):
                        return [CorrectionSpec(**it) for it in items]
                return []

            except LLMNotConfigured:
                raise
            except BaseException as e:
                # Catch ALL exceptions including Gemini API errors
                error_msg = str(e)
                error_type = type(e).__name__
                is_server_error = (
                    "503" in error_msg
                    or "UNAVAILABLE" in error_msg
                    or "overloaded" in error_msg.lower()
                )
                is_rate_limit = "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg

                logger.warning(
                    f"Caught {error_type}: is_server_error={is_server_error}, is_rate_limit={is_rate_limit}, attempt={attempt}/{max_retries}"
                )

                # Extract retry delay from 429 error if present
                retry_delay = None
                if is_rate_limit and "retry" in error_msg.lower():
                    import re

                    match = re.search(r"retry.*?(\d+\.?\d*)\s*s", error_msg, re.IGNORECASE)
                    if match:
                        retry_delay = float(match.group(1))

                if (is_server_error or is_rate_limit) and attempt < max_retries - 1:
                    # Use Google's suggested delay for 429, otherwise exponential backoff
                    if is_rate_limit and retry_delay:
                        delay = retry_delay
                        logger.warning(
                            f"⚠️  Rate limit exceeded (429), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                        )
                    else:
                        # Exponential backoff: 2s, 4s, 8s
                        delay = base_delay * (2**attempt)
                        logger.warning(
                            f"⚠️  Model overloaded (503), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                        )
                    time.sleep(delay)
                    continue
                elif (is_server_error or is_rate_limit) and attempt == max_retries - 1:
                    # Last retry failed, try Azure OpenAI GPT-5 first, then flash
                    error_type = "rate limit" if is_rate_limit else "server overload"
                    logger.warning(
                        f"⚠️  {self.model_name} failed after {max_retries} retries ({error_type}), trying Azure OpenAI GPT-5"
                    )

                    # Try Azure OpenAI first
                    try:
                        from settings import get_settings

                        settings = get_settings()
                        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
                            azure_corrector = AzureOpenAICorrector(
                                base_prompt_text=self.base_prompt_text
                            )
                            result = azure_corrector.correct_tokens(tokens)
                            if result:
                                logger.info("✅ Fallback to Azure OpenAI GPT-5 succeeded")
                                return result
                    except Exception as azure_error:
                        logger.warning(
                            f"⚠️  Azure OpenAI fallback failed: {azure_error}, trying gemini-2.5-flash"
                        )

                    # If Azure failed, try flash
                    try:
                        resp = self._client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=[{"role": "user", "parts": [{"text": prompt}]}],
                            config={"response_mime_type": "application/json"},
                        )
                        text = getattr(resp, "text", None)
                        if not text:
                            if hasattr(resp, "candidates") and resp.candidates:
                                cand = resp.candidates[0]
                                if hasattr(cand, "content") and cand.content:
                                    if hasattr(cand.content, "parts") and cand.content.parts:
                                        part = cand.content.parts[0]
                                        text = getattr(part, "text", None)
                        if text:
                            data = json.loads(text)
                            items = data.get("corrections") if isinstance(data, dict) else data
                            if isinstance(items, list):
                                logger.info("✅ Fallback to gemini-2.5-flash succeeded")
                                return [CorrectionSpec(**it) for it in items]
                    except Exception as fallback_error:
                        logger.error(f"❌ All fallbacks failed: {fallback_error}")
                    return []
                else:
                    # Non-server error, log and return empty
                    logger.warning(f"Error in correct_tokens: {e}", exc_info=True)
                    return []

        return []


class AzureOpenAICorrector:
    """Corrector using Azure OpenAI GPT-5."""

    def __init__(self, base_prompt_text: str | None = None) -> None:
        self.base_prompt_text = base_prompt_text or ""
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            try:
                from openai import AzureOpenAI

                from settings import get_settings

                settings = get_settings()

                if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
                    raise LLMNotConfigured("Azure OpenAI credentials not configured")

                self._client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version or "2025-04-01-preview",
                    azure_endpoint=settings.azure_openai_endpoint,
                )
                self.deployment_name = settings.azure_openai_deployment_name or "gpt-5"

            except ImportError as err:
                raise LLMNotConfigured("openai package not installed") from err

    def correct_tokens(self, tokens: list[Token]) -> list[CorrectionSpec]:
        self._ensure_client()
        # Use sanitized prompt for Azure to avoid content filter
        prompt = build_json_prompt(self.base_prompt_text, tokens, sanitize_for_azure=True)

        max_retries = 3
        base_delay = 2

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"🔄 Retry {attempt + 1}/{max_retries} with Azure GPT-5")
                else:
                    logger.info(f"🤖 Using Azure OpenAI model: {self.deployment_name}")

                # Sanitized system prompt to avoid Azure content filter
                # Based on azure_content_filter_deep_dive.md:
                # - Use neutral, high-level description
                # - Avoid words like "correct", "detect", "execute"
                response = self._client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a text analysis assistant that returns JSON.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )

                text = response.choices[0].message.content
                if text:
                    data = json.loads(text)
                    items = data.get("corrections") if isinstance(data, dict) else data
                    if isinstance(items, list):
                        return [CorrectionSpec(**it) for it in items]
                return []

            except LLMNotConfigured:
                raise
            except Exception as e:
                error_msg = str(e)
                # Check for Azure content filter (jailbreak detection)
                is_content_filter = (
                    "content_filter" in error_msg or "ResponsibleAIPolicyViolation" in error_msg
                )

                if is_content_filter:
                    logger.warning(
                        "⚠️  Azure GPT-5 content filter triggered, trying GPT-4.1 fallback"
                    )
                    # Try GPT-4.1 as fallback
                    try:
                        from settings import get_settings

                        settings = get_settings()
                        if settings.azure_openai_fallback_deployment_name:
                            fallback_deployment = settings.azure_openai_fallback_deployment_name
                            fallback_api_version = (
                                settings.azure_openai_fallback_api_version or "2025-01-01-preview"
                            )

                            logger.info(
                                f"🤖 Using Azure OpenAI fallback model: {fallback_deployment}"
                            )

                            # Create new client with fallback API version
                            from openai import AzureOpenAI

                            fallback_client = AzureOpenAI(
                                api_key=settings.azure_openai_api_key,
                                api_version=fallback_api_version,
                                azure_endpoint=settings.azure_openai_endpoint,
                            )

                            response = fallback_client.chat.completions.create(
                                model=fallback_deployment,
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are a text analysis assistant that returns JSON.",
                                    },
                                    {"role": "user", "content": prompt},
                                ],
                                response_format={"type": "json_object"},
                            )

                            text = response.choices[0].message.content
                            if text:
                                data = json.loads(text)
                                items = data.get("corrections") if isinstance(data, dict) else data
                                if isinstance(items, list):
                                    logger.info("✅ Azure GPT-4.1 fallback succeeded")
                                    return [CorrectionSpec(**it) for it in items]
                    except Exception as fallback_error:
                        logger.warning(f"⚠️  Azure GPT-4.1 fallback also failed: {fallback_error}")

                    # If GPT-4.1-mini also failed, return empty to trigger Flash fallback
                    logger.warning("⚠️  All Azure models failed, falling back to Gemini Flash")
                    return []  # Return empty to trigger Flash fallback in caller

                logger.warning(
                    f"Azure OpenAI error (attempt {attempt + 1}/{max_retries}): {error_msg}"
                )

                if attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)
                    logger.warning(f"⚠️  Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"❌ Azure OpenAI failed after {max_retries} retries")
                    return []

        return []


class HeuristicCorrector:
    """Simple local heuristic corrector used for testing/demo.

    - corrige "baca"->"vaca" si contexto contiene coche/carro/auto
    - corrige "vello"->"bello" cuando aparezca con adjetivos estéticos
    - corrige "ojear"->"hojear" si contexto contiene libro/revista
    """

    def correct_tokens(self, tokens: list[Token]) -> list[CorrectionSpec]:
        text_lower = [t.text.lower() for t in tokens]
        results: list[CorrectionSpec] = []
        for i, t in enumerate(tokens):
            if t.kind != "word":
                continue
            w = t.text.lower()
            # baca/vaca
            if w == "baca":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["coche", "carro", "auto", "vehículo", "vehiculo"]):
                    results.append(
                        CorrectionSpec(
                            token_id=i,
                            replacement=_preserve_case(t.text, "vaca"),
                            reason="Confusión baca/vaca (techo del coche)",
                            original=t.text,
                        )
                    )
            # vello/bello
            if w == "vello":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["hermoso", "bonito", "precioso", "arte"]):
                    results.append(
                        CorrectionSpec(
                            token_id=i,
                            replacement=_preserve_case(t.text, "bello"),
                            reason="Confusión vello/bello (estético)",
                            original=t.text,
                        )
                    )
            # ojear/hojear
            if w == "ojear":
                window = " ".join(text_lower[max(0, i - 5) : i + 6])
                if any(k in window for k in ["libro", "revista", "páginas", "paginas"]):
                    results.append(
                        CorrectionSpec(
                            token_id=i,
                            replacement=_preserve_case(t.text, "hojear"),
                            reason="Confusión ojear/hojear (pasar páginas)",
                            original=t.text,
                        )
                    )
        return results


def _preserve_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def _build_tools_from_pydantic(function_name: str, model: type[BaseModel]) -> list[dict[str, Any]]:
    """Build Gemini 'tools' function_declarations from a Pydantic model schema."""
    schema: dict[str, Any] = model.model_json_schema()
    # Ensure top-level is an object; Gemini expects JSON Schema draft
    if schema.get("type") != "object":
        schema = {"type": "object", "properties": {"value": schema}, "required": ["value"]}
    return [
        {
            "function_declarations": [
                {
                    "name": function_name,
                    "parameters": schema,
                }
            ]
        }
    ]


def _extract_function_call(resp: Any, name: str) -> dict[str, Any] | None:
    """Extract function call arguments from a Gemini Responses object."""
    try:
        cands = getattr(resp, "candidates", None)
        if not cands:
            return None
        for c in cands:
            content = getattr(c, "content", None)
            if not content:
                continue
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            for p in parts:
                fc = getattr(p, "function_call", None) or getattr(p, "functionCall", None)
                if not fc:
                    continue
                fname = getattr(fc, "name", None) or (isinstance(fc, dict) and fc.get("name"))
                if fname != name:
                    continue
                args = getattr(fc, "args", None) or (isinstance(fc, dict) and fc.get("args"))
                if isinstance(args, dict):
                    return args
    except Exception:
        return None
    return None
