import pytest
from worldcup.models import Team
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor


@pytest.fixture
def strong():
    return Team("Strong", "A", 1)


@pytest.fixture
def weak():
    return Team("Weak", "A", 80)


def test_uniform_sums_to_one(strong, weak):
    p = UniformPredictor().predict(strong, weak)
    assert abs(sum(p) - 1.0) < 1e-9


def test_uniform_equal(strong, weak):
    p = UniformPredictor().predict(strong, weak)
    assert p[0] == pytest.approx(1 / 3)
    assert p[1] == pytest.approx(1 / 3)
    assert p[2] == pytest.approx(1 / 3)


def test_ranking_sums_to_one(strong, weak):
    p = RankingPredictor().predict(strong, weak)
    assert abs(sum(p) - 1.0) < 1e-9


def test_ranking_favours_better_team(strong, weak):
    p_home, _, p_away = RankingPredictor().predict(strong, weak)
    assert p_home > p_away


def test_ranking_symmetric(strong, weak):
    p_home, p_draw, p_away = RankingPredictor().predict(strong, weak)
    p_home2, p_draw2, p_away2 = RankingPredictor().predict(weak, strong)
    assert p_home == pytest.approx(p_away2)
    assert p_draw == pytest.approx(p_draw2)
    assert p_away == pytest.approx(p_home2)


def test_ranking_equal_teams():
    a = Team("A", "X", 50)
    b = Team("B", "X", 50)
    p_home, p_draw, p_away = RankingPredictor().predict(a, b)
    assert p_home == pytest.approx(p_away)


def test_ranking_draw_rate():
    pred = RankingPredictor(draw_rate=0.3)
    a = Team("A", "X", 10)
    b = Team("B", "X", 10)
    _, p_draw, _ = pred.predict(a, b)
    assert p_draw == pytest.approx(0.3)
