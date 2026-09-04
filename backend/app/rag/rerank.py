"""Top-k reordering. Stretch goal.

Only implement if the evaluation harness shows recall@5 is good but the final
answer is still wrong — that's the specific symptom reranking fixes.
"""

from __future__ import annotations

from app.rag.chunking import Chunk


def rerank(query: str, candidates: list[tuple[Chunk, float]]) -> list[tuple[Chunk, float]]:
    raise NotImplementedError
