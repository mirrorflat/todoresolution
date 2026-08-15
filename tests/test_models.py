from src.models import Task, clamp


def test_score_formula():
    task = Task(title="t", urgency=3.0, importance=5.0, resolution=2.0)
    # importance^2 * (urgency + 0.5*(10-resolution)) = 25 * (3 + 0.5*8) = 25 * 7 = 175
    assert task.score == 175.0


def test_score_zero_importance():
    task = Task(title="t", urgency=10.0, importance=0.0, resolution=0.0)
    assert task.score == 0.0


def test_clamp():
    assert clamp(-5) == 0.0
    assert clamp(15) == 10.0
    assert clamp(4.2) == 4.2
