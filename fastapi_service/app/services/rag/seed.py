"""
Populates the knowledge_chunks table with a small starter corpus of testing
conventions. Run once after migrations:

    python -m app.services.rag.seed

In a real system this corpus would grow from your team's actual style
guide, past code reviews, and framework docs — the seeding mechanism
stays the same either way.
"""

import asyncio

from app.db.models import KnowledgeChunk
from app.db.session import AsyncSessionLocal
from app.services.rag.embeddings import get_embedder

_SEED_CHUNKS = [
    ("python", "pytest conventions", "Use pytest fixtures for setup/teardown instead of unittest's setUp/tearDown; prefer plain assert statements over self.assertEqual."),
    ("python", "pytest conventions", "Parametrize tests with @pytest.mark.parametrize instead of writing near-duplicate test functions for each input case."),
    ("python", "edge cases", "For any function taking a collection, test the empty collection, a single-element collection, and duplicate elements."),
    ("python", "edge cases", "For numeric functions, test zero, negative numbers, and boundary values (e.g. the max/min of the expected range), not just typical positive inputs."),
    ("python", "error handling", "Test that invalid input raises the documented exception type, not just that valid input returns the right value."),
    ("python", "docstrings", "Every public function should have a docstring describing parameters, return value, and any exceptions raised."),
    ("python", "async testing", "Async functions should be tested with pytest-asyncio and @pytest.mark.asyncio, awaiting the coroutine under test directly."),
    ("general", "naming", "Test names should describe the scenario and expected outcome, e.g. test_divide_by_zero_raises_value_error, not test_1 or test_divide."),
    ("general", "coverage", "Prioritize testing branches with conditional logic and error paths over straight-line code with no decisions."),
]


async def seed() -> None:
    embedder = get_embedder()

    # Assumes "alembic upgrade head" has already run — the entrypoint
    # does this before seeding.
    async with AsyncSessionLocal() as db:
        for language, source, content in _SEED_CHUNKS:
            db.add(
                KnowledgeChunk(
                    language=language,
                    source=source,
                    content=content,
                    embedding=embedder.embed(content),
                )
            )
        await db.commit()

    print(f"Seeded {len(_SEED_CHUNKS)} knowledge chunks.")


if __name__ == "__main__":
    asyncio.run(seed())
