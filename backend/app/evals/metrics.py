"""Métricas del arnés de evaluación: recall@k, groundedness, abstention_precision, answer_match."""

from __future__ import annotations


def recall_at_k(expected_chunk_ids: list[str], retrieved_chunk_ids: list[str]) -> float:
    if not expected_chunk_ids:
        return 1.0
    hits = sum(1 for cid in expected_chunk_ids if cid in retrieved_chunk_ids)
    return hits / len(expected_chunk_ids)


def groundedness(claims_with_citations: list[bool]) -> float:
    if not claims_with_citations:
        return 1.0
    return sum(claims_with_citations) / len(claims_with_citations)


def abstention_precision(abstained_correctly: list[bool]) -> float:
    if not abstained_correctly:
        return 1.0
    return sum(abstained_correctly) / len(abstained_correctly)


def answer_match(answer: str, expected_terms: list[str]) -> float:
    if not expected_terms:
        return 1.0
    lowered = answer.lower()
    hits = sum(1 for term in expected_terms if term.lower() in lowered)
    return hits / len(expected_terms)
