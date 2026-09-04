"""Consulta -> chunks candidatos + scores. Único módulo de rag/ (junto a answer.py) con I/O."""

from __future__ import annotations

from app.rag.chunking import Chunk


def retrieve(query: str, *, top_k: int = 5) -> list[tuple[Chunk, float]]:
    """Devuelve hasta `top_k` chunks candidatos ordenados por score descendente."""
    raise NotImplementedError
