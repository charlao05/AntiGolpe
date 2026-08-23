from backend.tests.provider_gate.scoring import DeterministicScores, EvaluativeScores


def test_score_shapes_start_unresolved():
    assert DeterministicScores().d1 is None
    assert EvaluativeScores().e1 is None
