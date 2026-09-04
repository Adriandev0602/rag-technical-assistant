"""Query -> candidate chunks + scores. One of the two rag/ modules (with answer.py) allowed I/O."""

from __future__ import annotations

from app.rag.chunking import Chunk


def retrieve(query: str, *, top_k: int = 5) -> list[tuple[Chunk, float]]:
    """Return up to `top_k` candidate chunks ordered by descending score."""
    raise NotImplementedError
