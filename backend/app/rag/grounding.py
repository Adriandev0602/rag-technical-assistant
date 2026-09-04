"""Validador de citas — la capa 2 de la regla no negociable (CLAUDE.md §2).

Rechaza toda respuesta que cite un chunk_id que no está en el contexto recuperado.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.chunking import Chunk


@dataclass
class GroundingResult:
    is_grounded: bool
    ungrounded_chunk_ids: list[str]


def validate_grounding(answer_chunk_ids: list[str], retrieved_chunks: list[Chunk]) -> GroundingResult:
    """Verifica que cada chunk_id citado en la respuesta esté entre los recuperados."""
    retrieved_ids = {chunk["chunk_id"] for chunk in retrieved_chunks}
    ungrounded = [cid for cid in answer_chunk_ids if cid not in retrieved_ids]
    return GroundingResult(is_grounded=not ungrounded, ungrounded_chunk_ids=ungrounded)
