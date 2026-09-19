from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)  # references Django's User.id
    filename: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(30))
    source_code: Mapped[str] = mapped_column(Text)
    parsed_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class KnowledgeChunk(Base):
    """
    A single retrievable piece of the RAG knowledge base — a testing
    convention, a framework idiom, a style-guide rule. Embeddings are
    stored as JSON floats for portability; swap to a pgvector column
    (`Vector(EMBEDDING_DIM)`) once corpus size makes brute-force cosine
    similarity in Python too slow.
    """
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    language: Mapped[str] = mapped_column(String(30), index=True)
    source: Mapped[str] = mapped_column(String(255))  # e.g. "pytest docs", "pep8"
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON)


class TestGenerationResult(Base):
    __tablename__ = "test_generation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("code_submissions.id"), index=True)
    generated_tests: Mapped[str] = mapped_column(Text)
    suggestions: Mapped[list] = mapped_column(JSON)
    model_used: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

