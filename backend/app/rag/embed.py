"""Chunks -> vectores. Función pura: no sabe de dónde salieron los chunks."""

from __future__ import annotations

from app.llm.base import LLMProvider


def embed_chunks(texts: list[str], *, provider: LLMProvider) -> list[list[float]]:
    """Embebe `texts` en batch usando el proveedor dado."""
    raise NotImplementedError
