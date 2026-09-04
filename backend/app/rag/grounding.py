"""Citation validator — the second enforcement layer of the grounding guarantee.

Rejects any answer that cites a chunk_id not present in the retrieved context.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.rag.chunking import Chunk


@dataclass
class GroundingResult:
    is_grounded: bool
    ungrounded_chunk_ids: list[str]


def validate_grounding(answer_chunk_ids: list[str], retrieved_chunks: list[Chunk]) -> GroundingResult:
    """Check that every chunk_id cited in the answer is among the retrieved chunks."""
    retrieved_ids = {chunk["chunk_id"] for chunk in retrieved_chunks}
    ungrounded = [cid for cid in answer_chunk_ids if cid not in retrieved_ids]
    return GroundingResult(is_grounded=not ungrounded, ungrounded_chunk_ids=ungrounded)
