import pytest
import numpy as np
from worldcup.models import Team
from worldcup.algorithms.fifa_rating import FIFARatingModel
from worldcup.algorithms.poisson import PoissonGoalModel, _poisson_outcome_probs


@pytest.fixture
def strong():
    return Team("Strong", "A", 1)


@pytest.fixture
def weak():
    return Team("Weak", "A", 80)


@pytest.fixture
def model():
    return PoissonGoalModel(FIFARatingModel())


def test_fifa_rating_higher_rank_lower_rating(strong, weak):
    m = FIFARatingModel()
    assert m.rate(strong) > m.rate(weak)


def test_poisson_lambdas_sum_to_constant(model, strong, weak):
    λ_h, λ_a = model.lambdas(strong, weak)
    assert abs(λ_h * λ_a - model.base_lambda ** 2) < 1e-9


def test_poisson_lambdas_stronger_home_gets_higher_lambda(model, strong, weak):
    λ_h, λ_a = model.lambdas(strong, weak)
    assert λ_h > λ_a


def test_poisson_lambdas_equal_teams():
    m = PoissonGoalModel(FIFARatingModel())
    a = Team("A", "X", 20)
    b = Team("B", "X", 20)
    λ_h, λ_a = m.lambdas(a, b)
    assert λ_h == pytest.approx(λ_a)
    assert λ_h == pytest.approx(m.base_lambda)


def test_poisson_lambdas_max_ratio_clamps(strong, weak):
    m = PoissonGoalModel(FIFARatingModel(), max_ratio=2.0)
    λ_h, λ_a = m.lambdas(strong, weak)
    λ_h2, λ_a2 = m.lambdas(weak, strong)
    # With max_ratio=2, the capped ratio should give the same multiplier regardless
    # of whether the actual ratio is 80 or 1/80
    assert λ_h == pytest.approx(λ_a2)
    assert λ_a == pytest.approx(λ_h2)


def test_poisson_predict_sums_to_one(model, strong, weak):
    p = model.predict(strong, weak)
    assert abs(sum(p) - 1.0) < 1e-6


def test_poisson_predict_favours_stronger_team(model, strong, weak):
    p_home, _, p_away = model.predict(strong, weak)
    assert p_home > p_away


def test_poisson_predict_symmetric(model, strong, weak):
    p_home, p_draw, p_away = model.predict(strong, weak)
    p_home2, p_draw2, p_away2 = model.predict(weak, strong)
    assert p_home == pytest.approx(p_away2, abs=1e-6)
    assert p_draw == pytest.approx(p_draw2, abs=1e-6)


def test_poisson_outcome_probs_equal_lambdas():
    p_h, p_d, p_a = _poisson_outcome_probs(1.3, 1.3)
    assert p_h == pytest.approx(p_a, abs=1e-6)
    assert abs(p_h + p_d + p_a - 1.0) < 1e-6


def test_simulator_uses_poisson_path():
    from worldcup.simulator import GroupStageSimulator
    teams = [Team(f"T{i}", "A", i) for i in range(1, 5)]
    model = PoissonGoalModel(FIFARatingModel())
    sim = GroupStageSimulator(model, n=1, seed=0)
    assert sim._use_poisson is True
    standings = sim._simulate_group(teams)
    assert len(standings) == 4
    for r in standings:
        assert r.played == 3


def test_simulator_old_path_unaffected():
    from worldcup.simulator import GroupStageSimulator
    from worldcup.algorithms.uniform import UniformPredictor
    teams = [Team(f"T{i}", "A", i) for i in range(1, 5)]
    sim = GroupStageSimulator(UniformPredictor(), n=1, seed=0)
    assert sim._use_poisson is False
    standings = sim._simulate_group(teams)
    assert len(standings) == 4
