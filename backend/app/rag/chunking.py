"""Document -> chunks with stable metadata. Pure function: knows nothing about the embedding model."""

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
    """Split `text` into chunks with a stable chunk_id: <source>__<section>__<index>.

    Re-ingesting the same document with no changes must produce exactly the same ids.
    """
    raise NotImplementedError
