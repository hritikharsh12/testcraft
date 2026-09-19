from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ANTHROPIC_MODEL
from app.core.logging import get_logger
from app.core.rate_limiter import limiter
from app.core.security import CurrentUser, get_current_user
from app.db.models import CodeSubmission, TestGenerationResult
from app.db.session import get_db
from app.models.schemas import GenerateResponse
from app.services.prompts.llm_client import LLMGenerationError, generate_tests_and_suggestions
from app.services.prompts.prompt_builder import build_prompt
from app.services.rag.retriever import retrieve_context

router = APIRouter()
logger = get_logger("app.generate")


@router.post("/generate/{submission_id}", response_model=GenerateResponse)
@limiter.limit("5/minute")  # LLM calls are expensive; tighter limit than upload
async def generate_tests(
    request: Request,
    submission_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    submission = await db.get(CodeSubmission, submission_id)
    if submission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found.")
    if submission.user_id != user.user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not own this submission.")

    summary = submission.parsed_summary
    query_text = f"{submission.language} {' '.join(f['name'] for f in summary.get('functions', []))}"
    retrieved_context = await retrieve_context(db, query_text=query_text, language=submission.language)

    prompt = build_prompt(
        "test_gen.jinja",
        language=submission.language,
        filename=submission.filename,
        source_code=submission.source_code,
        retrieved_context=retrieved_context,
        function_count=len(summary.get("functions", [])),
        class_count=len(summary.get("classes", [])),
        warnings=summary.get("warnings", []),
    )

    try:
        result = await generate_tests_and_suggestions(prompt)
    except LLMGenerationError as exc:
        logger.error("generation_failed submission_id=%s error=%s", submission_id, str(exc))
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Test generation failed: {exc}")

    record = TestGenerationResult(
        submission_id=submission.id,
        generated_tests=result["tests"],
        suggestions=result["suggestions"],
        model_used=ANTHROPIC_MODEL,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    logger.info(
        "generation_complete submission_id=%s user_id=%s suggestions_count=%d",
        submission_id, user.user_id, len(result["suggestions"]),
    )

    return GenerateResponse(
        submission_id=submission.id,
        generated_tests=record.generated_tests,
        suggestions=record.suggestions,
        model_used=record.model_used,
        created_at=record.created_at,
    )
