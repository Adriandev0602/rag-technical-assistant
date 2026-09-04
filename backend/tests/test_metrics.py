from app.evals.metrics import abstention_precision, answer_match, groundedness, recall_at_k


def test_recall_at_k_full_hit():
    assert recall_at_k(["a", "b"], ["a", "b", "c"]) == 1.0


def test_recall_at_k_partial_hit():
    assert recall_at_k(["a", "b"], ["a", "c"]) == 0.5


def test_recall_at_k_empty_expected_is_perfect():
    assert recall_at_k([], ["a"]) == 1.0


def test_groundedness_all_cited():
    assert groundedness([True, True]) == 1.0


def test_groundedness_partial():
    assert groundedness([True, False]) == 0.5


def test_abstention_precision():
    assert abstention_precision([True, True, False]) == 2 / 3


def test_answer_match_case_insensitive():
    assert answer_match("No, only with Building Cards", ["no", "building cards"]) == 1.0


def test_answer_match_missing_term():
    assert answer_match("Yes, with steel", ["no", "steel"]) == 0.5
