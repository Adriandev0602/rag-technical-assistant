"""Implementación de LLMProvider sobre el SDK de Gemini."""

from __future__ import annotations

from app.llm.base import Completion, Message, Tool


class GeminiProvider:
    def complete(self, messages: list[Message], *, tools: list[Tool] | None = None) -> Completion:
        raise NotImplementedError

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
