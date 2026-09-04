from app.rag.grounding import validate_grounding


def _chunk(chunk_id: str) -> dict:
    return {
        "chunk_id": chunk_id,
        "text": "some text",
        "source": "rulebook.pdf",
        "section": "3.2",
        "page": 1,
        "token_count": 10,
    }


def test_grounded_when_all_citations_are_retrieved():
    retrieved = [_chunk("rulebook__3.2__004")]
    result = validate_grounding(["rulebook__3.2__004"], retrieved)
    assert result.is_grounded
    assert result.ungrounded_chunk_ids == []


def test_not_grounded_when_citation_is_hallucinated():
    retrieved = [_chunk("rulebook__3.2__004")]
    result = validate_grounding(["rulebook__9.9__999"], retrieved)
    assert not result.is_grounded
    assert result.ungrounded_chunk_ids == ["rulebook__9.9__999"]


def test_grounded_when_no_citations_claimed():
    result = validate_grounding([], [])
    assert result.is_grounded
