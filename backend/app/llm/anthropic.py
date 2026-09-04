"""Implementación de LLMProvider sobre el SDK de Anthropic."""

from __future__ import annotations

from app.llm.base import Completion, Message, Tool


class AnthropicProvider:
    def complete(self, messages: list[Message], *, tools: list[Tool] | None = None) -> Completion:
        raise NotImplementedError

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
