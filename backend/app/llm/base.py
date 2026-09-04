"""Abstract LLM provider interface. Nothing outside llm/ imports a concrete SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict


@dataclass
class Completion:
    text: str
    raw: dict


class LLMProvider(Protocol):
    def complete(self, messages: list[Message], *, tools: list[Tool] | None = None) -> Completion: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...
