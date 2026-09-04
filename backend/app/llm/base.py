"""Interfaz abstracta del proveedor de LLM. Nada fuera de llm/ importa un SDK concreto."""

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
