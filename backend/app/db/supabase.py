"""Única capa con I/O de persistencia. rag/ nunca importa esto directamente."""

from __future__ import annotations

from app.rag.chunking import Chunk


def save_chunks(chunks: list[Chunk]) -> None:
    raise NotImplementedError


def load_chunks(source: str | None = None) -> list[Chunk]:
    raise NotImplementedError
