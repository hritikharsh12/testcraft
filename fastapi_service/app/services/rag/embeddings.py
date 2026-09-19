import math
import re
from abc import ABC, abstractmethod

from app.core.config import EMBEDDING_DIM

_TOKEN_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")


class EmbeddingClient(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        ...


class HashingEmbedder(EmbeddingClient):
    """
    A deterministic, dependency-free "embedding" using the hashing trick:
    each token votes on a handful of dimensions, and the vector is
    L2-normalized so cosine similarity behaves sensibly.

    This exists so the whole RAG pipeline is runnable out of the box with
    no external API key and no GPU. It captures keyword overlap well
    enough to demo retrieval, but it is NOT semantically aware the way a
    real embedding model is. Swap this for a hosted model (e.g. Voyage AI,
    which Anthropic commonly recommends pairing with Claude, or OpenAI's
    text-embedding-3) before relying on this in production — only the
    `embed` method needs to change, nothing downstream does.
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            idx = hash(token) % self.dim
            vector[idx] += 1.0

        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both vectors are already L2-normalized


_default_embedder: EmbeddingClient | None = None


def get_embedder() -> EmbeddingClient:
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = HashingEmbedder()
    return _default_embedder
