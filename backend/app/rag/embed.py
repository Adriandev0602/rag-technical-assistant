"""Chunks -> vectors. Pure function: doesn't know where the chunks came from."""

from __future__ import annotations

from app.llm.base import LLMProvider


def embed_chunks(texts: list[str], *, provider: LLMProvider) -> list[list[float]]:
    """Embed `texts` in a batch using the given provider."""
    raise NotImplementedError
