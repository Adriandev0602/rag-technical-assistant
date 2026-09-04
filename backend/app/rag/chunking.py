"""Documento -> chunks con metadata estable. Función pura: no conoce el modelo de embeddings."""

from __future__ import annotations

from typing import TypedDict


class Chunk(TypedDict):
    chunk_id: str
    text: str
    source: str
    section: str
    page: int
    token_count: int


def chunk_document(
    text: str,
    *,
    source: str,
    section: str,
    page: int,
    target_tokens: int = 500,
    overlap_ratio: float = 0.15,
) -> list[Chunk]:
    """Parte `text` en chunks con chunk_id estable: <source>__<section>__<índice>.

    Reingestar el mismo documento sin cambios debe producir exactamente los mismos ids.
    """
    raise NotImplementedError
