import json
import logging

import anthropic
import openai
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.core.config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
)

logger = logging.getLogger("app.llm_client")

_anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# Groq exposes an OpenAI-compatible endpoint, so the standard openai SDK
# works unchanged — just point base_url at Groq instead of OpenAI. This is
# a genuinely free tier (no credit card, rate-limited) that's a reasonable
# default for local dev and demos before Anthropic billing is set up.
_groq_client = (
    AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    if GROQ_API_KEY
    else None
)


class LLMGenerationError(Exception):
    pass


async def _call_anthropic(prompt: str) -> str:
    if _anthropic_client is None:
        raise LLMGenerationError("ANTHROPIC_API_KEY is not configured.")

    try:
        response = await _anthropic_client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError as exc:
        logger.error("llm_auth_error provider=anthropic %s", exc)
        raise LLMGenerationError("ANTHROPIC_API_KEY was rejected — check it's a valid, active key.")
    except anthropic.NotFoundError as exc:
        logger.error("llm_model_not_found provider=anthropic model=%s %s", ANTHROPIC_MODEL, exc)
        raise LLMGenerationError(f"Model '{ANTHROPIC_MODEL}' was not found — check ANTHROPIC_MODEL is a current model ID.")
    except anthropic.RateLimitError as exc:
        logger.error("llm_rate_limited provider=anthropic %s", exc)
        raise LLMGenerationError("Anthropic API rate limit hit. Wait a moment and try again.")
    except anthropic.APIStatusError as exc:
        logger.error("llm_api_status_error provider=anthropic status=%s %s", exc.status_code, exc)
        detail = "Your Anthropic credit balance may be too low." if exc.status_code == 400 else ""
        raise LLMGenerationError(f"Anthropic API returned an error (status {exc.status_code}). {detail}".strip())
    except anthropic.APIConnectionError as exc:
        logger.error("llm_connection_error provider=anthropic %s", exc)
        raise LLMGenerationError("Couldn't reach the Anthropic API — check network connectivity from the container.")

    return "".join(block.text for block in response.content if block.type == "text")


async def _call_groq(prompt: str) -> str:
    if _groq_client is None:
        raise LLMGenerationError("GROQ_API_KEY is not configured.")

    try:
        response = await _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            # Groq's OpenAI-compatible endpoint supports this the same way
            # OpenAI does — it constrains the model to emit a JSON object,
            # which meaningfully reduces "almost-JSON" parsing failures on
            # a smaller open-weight model compared to Claude.
            response_format={"type": "json_object"},
        )
    except openai.AuthenticationError as exc:
        logger.error("llm_auth_error provider=groq %s", exc)
        raise LLMGenerationError("GROQ_API_KEY was rejected — check it's valid at console.groq.com/keys.")
    except openai.NotFoundError as exc:
        logger.error("llm_model_not_found provider=groq model=%s %s", GROQ_MODEL, exc)
        raise LLMGenerationError(f"Model '{GROQ_MODEL}' was not found on Groq — check GROQ_MODEL is current.")
    except openai.RateLimitError as exc:
        logger.error("llm_rate_limited provider=groq %s", exc)
        raise LLMGenerationError(
            "Groq's free-tier rate limit was hit (30 requests/min, 14,400/day). Wait a moment and try again."
        )
    except openai.APIStatusError as exc:
        logger.error("llm_api_status_error provider=groq status=%s %s", exc.status_code, exc)
        raise LLMGenerationError(f"Groq API returned an error (status {exc.status_code}).")
    except openai.APIConnectionError as exc:
        logger.error("llm_connection_error provider=groq %s", exc)
        raise LLMGenerationError("Couldn't reach the Groq API — check network connectivity from the container.")

    return response.choices[0].message.content or ""


async def call_llm_json(prompt: str, required_keys: tuple[str, ...]) -> dict:
    """
    Calls whichever provider LLM_PROVIDER selects and parses its JSON
    response, checking that the given keys are present. Both provider
    functions convert every SDK exception into LLMGenerationError before
    it can escape — letting a raw provider exception through means the
    response goes out with no CORS headers attached, which the browser
    then reports as an opaque "Failed to fetch" instead of a real error.
    """
    if LLM_PROVIDER == "groq":
        text = await _call_groq(prompt)
    elif LLM_PROVIDER == "anthropic":
        text = await _call_anthropic(prompt)
    else:
        raise LLMGenerationError(f"Unknown LLM_PROVIDER '{LLM_PROVIDER}' — use 'groq' or 'anthropic'.")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("llm_response_not_valid_json provider=%s response_preview=%s", LLM_PROVIDER, text[:200])
        raise LLMGenerationError("Model did not return valid JSON.")

    missing = [key for key in required_keys if key not in parsed]
    if missing:
        raise LLMGenerationError(f"Model response missing required keys: {missing}")

    return parsed


async def generate_tests_and_suggestions(prompt: str) -> dict:
    """Thin wrapper over call_llm_json for the test-generation shape."""
    return await call_llm_json(prompt, required_keys=("tests", "suggestions"))


async def generate_suggestions_only(prompt: str) -> dict:
    """Thin wrapper over call_llm_json for the code-review-only shape."""
    return await call_llm_json(prompt, required_keys=("suggestions",))