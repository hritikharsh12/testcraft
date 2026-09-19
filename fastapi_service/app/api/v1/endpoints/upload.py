from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES
from app.core.logging import get_logger
from app.core.rate_limiter import limiter
from app.core.security import CurrentUser, get_current_user
from app.db.models import CodeSubmission
from app.db.session import get_db
from app.models.schemas import UploadResponse
from app.services.code_parser import detect_language, parse_code

router = APIRouter()
logger = get_logger("app.upload")


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_code(
    request: Request,          # required by slowapi to read the rate-limit key
    file: UploadFile,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds the {MAX_UPLOAD_SIZE_BYTES // 1024} KB limit.",
        )

    try:
        source_code = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be UTF-8 text.")

    summary = parse_code(file.filename, source_code)

    submission = CodeSubmission(
        user_id=user.user_id,
        filename=file.filename,
        language=detect_language(file.filename),
        source_code=source_code,
        parsed_summary=summary.model_dump(),
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    logger.info(
        "upload_id=%s user_id=%s filename=%s language=%s functions=%d classes=%d warnings=%d",
        submission.id, user.user_id, file.filename, summary.language,
        len(summary.functions), len(summary.classes), len(summary.warnings),
    )

    return UploadResponse(
        submission_id=submission.id,
        filename=submission.filename,
        language=submission.language,
        summary=summary,
        created_at=submission.created_at,
    )
