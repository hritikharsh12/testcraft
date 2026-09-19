from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import RAG_TOP_K
from app.db.models import KnowledgeChunk
from app.services.rag.embeddings import cosine_similarity, get_embedder


async def retrieve_context(db: AsyncSession, query_text: str, language: str, top_k: int = RAG_TOP_K) -> list[str]:
    """
    Brute-force cosine similarity over chunks for the given language.
    Fine for a knowledge base of hundreds to low thousands of chunks;
    beyond that, move to pgvector's ANN index and let Postgres do the
    ranking instead of pulling everything into Python.
    """
    embedder = get_embedder()
    query_vector = embedder.embed(query_text)

    result = await db.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.language.in_([language, "general"]))
    )
    chunks = result.scalars().all()
    if not chunks:
        return []

    ranked = sorted(
        chunks,
        key=lambda chunk: cosine_similarity(query_vector, chunk.embedding),
        reverse=True,
    )
    return [chunk.content for chunk in ranked[:top_k]]
