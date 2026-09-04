"""Orquestación: retrieve -> prompt -> generar -> validar. Único módulo de rag/ (junto a
retrieve.py) con I/O, porque coordina llamadas a proveedor y umbral de abstención.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.chunking import Chunk

ABSTENTION_MESSAGE = "No encontré esto en el corpus."


@dataclass
class Answer:
    text: str
    cited_chunk_ids: list[str]
    abstained: bool


def answer_question(
    query: str,
    *,
    provider: LLMProvider,
    abstention_threshold: float,
) -> Answer:
    """Si el mejor score de recuperación queda por debajo del umbral, se abstiene sin llamar
    al generador. Si no, genera y valida el grounding antes de devolver la respuesta.
    """
    raise NotImplementedError
