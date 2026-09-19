"""
The functions here ARE the FastAPI endpoints' logic, called directly instead
of over HTTP. This is the point of putting MCP next to the REST API rather
than as a separate project: analyze_code / generate_tests / suggest_improvements
use the exact same parser, retriever, prompt templates, and LLM client as
`/api/v1/upload` and `/api/v1/generate` — an MCP client (Claude Desktop, an
agent, whatever) gets identical behavior to the REST API, not a parallel
reimplementation that can drift out of sync.
"""

from app.core.config import MCP_GENERATE_RATE_LIMIT, MCP_RATE_LIMIT_WINDOW_SECONDS
from app.core.rate_limiter import check_rate_limit
from app.core.security import verify_token_string
from app.db.models import CodeSubmission, TestGenerationResult
from app.db.session import AsyncSessionLocal
from app.services.code_parser import detect_language, parse_code
from app.services.prompts.llm_client import (
    LLMGenerationError,
    generate_suggestions_only,
    generate_tests_and_suggestions,
)
from app.services.prompts.prompt_builder import build_prompt
from app.services.rag.retriever import retrieve_context


class MCPToolError(Exception):
    """Raised for any tool-level failure; the MCP server layer turns this into a tool error result."""


async def _authorize(access_token: str):
    try:
        return verify_token_string(access_token)
    except Exception as exc:
        raise MCPToolError(f"Authentication failed: {exc}")


async def _enforce_rate_limit(user_id: int, scope: str):
    allowed = await check_rate_limit(
        key=f"mcp:{scope}:user:{user_id}",
        max_calls=MCP_GENERATE_RATE_LIMIT,
        window_seconds=MCP_RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise MCPToolError(
            f"Rate limit exceeded: max {MCP_GENERATE_RATE_LIMIT} '{scope}' calls "
            f"per {MCP_RATE_LIMIT_WINDOW_SECONDS}s."
        )


async def analyze_code(source_code: str, filename: str) -> dict:
    """
    Pure static analysis — no LLM call, no auth required, since it costs
    nothing and reveals nothing about any particular user's data.
    """
    summary = parse_code(filename, source_code)
    return summary.model_dump()


async def generate_tests(access_token: str, source_code: str, filename: str) -> dict:
    """
    Full pipeline: parse -> retrieve RAG context -> build prompt -> call the
    LLM -> persist -> return. Requires a valid access token issued by the
    Django auth service, and is rate-limited per user just like the REST
    endpoint, using the same knowledge base and prompt templates.
    """
    user = await _authorize(access_token)
    await _enforce_rate_limit(user.user_id, scope="generate_tests")

    language = detect_language(filename)
    summary = parse_code(filename, source_code)

    async with AsyncSessionLocal() as db:
        query_text = f"{language} {' '.join(f.name for f in summary.functions)}"
        retrieved_context = await retrieve_context(db, query_text=query_text, language=language)

        prompt = build_prompt(
            "test_gen.jinja",
            language=language,
            filename=filename,
            source_code=source_code,
            retrieved_context=retrieved_context,
            function_count=len(summary.functions),
            class_count=len(summary.classes),
            warnings=summary.warnings,
        )

        try:
            result = await generate_tests_and_suggestions(prompt)
        except LLMGenerationError as exc:
            raise MCPToolError(f"Test generation failed: {exc}")

        submission = CodeSubmission(
            user_id=user.user_id,
            filename=filename,
            language=language,
            source_code=source_code,
            parsed_summary=summary.model_dump(),
        )
        db.add(submission)
        await db.flush()  # assigns submission.id without a full commit yet

        db.add(
            TestGenerationResult(
                submission_id=submission.id,
                generated_tests=result["tests"],
                suggestions=result["suggestions"],
                model_used="mcp-tool-call",
            )
        )
        await db.commit()

    return {
        "submission_id": submission.id,
        "tests": result["tests"],
        "suggestions": result["suggestions"],
    }


async def suggest_improvements(access_token: str, source_code: str, filename: str) -> dict:
    """
    Lighter-weight than generate_tests: code-review-style suggestions only,
    no test file written, nothing persisted. Useful for a quick "is this
    worth testing more thoroughly" pass before committing to full generation.
    """
    user = await _authorize(access_token)
    await _enforce_rate_limit(user.user_id, scope="suggest_improvements")

    language = detect_language(filename)

    async with AsyncSessionLocal() as db:
        query_text = f"{language} code review best practices"
        retrieved_context = await retrieve_context(db, query_text=query_text, language=language)

    prompt = build_prompt(
        "code_review.jinja",
        language=language,
        filename=filename,
        source_code=source_code,
        retrieved_context=retrieved_context,
    )

    try:
        result = await generate_suggestions_only(prompt)
    except LLMGenerationError as exc:
        raise MCPToolError(f"Suggestion generation failed: {exc}")

    return {"suggestions": result["suggestions"]}
