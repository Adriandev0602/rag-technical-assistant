"""Orchestration: retrieve -> prompt -> generate -> validate. The other rag/ module (with
retrieve.py) allowed I/O, since it coordinates provider calls and the abstention threshold.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.base import LLMProvider
from app.rag.chunking import Chunk

ABSTENTION_MESSAGE = "I couldn't find this in the corpus."


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
    """If the best retrieval score falls below the threshold, abstain without calling the
    generator. Otherwise generate and validate grounding before returning the answer.
    """
    raise NotImplementedError
