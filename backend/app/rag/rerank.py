"""Reordenamiento del top-k. Stretch goal — ver CLAUDE.md §7.

No implementar salvo que el arnés muestre recall@5 alto y respuesta igual mala:
ese es el síntoma específico que el reranking arregla.
"""

from __future__ import annotations

from app.rag.chunking import Chunk


def rerank(query: str, candidates: list[tuple[Chunk, float]]) -> list[tuple[Chunk, float]]:
    raise NotImplementedError
