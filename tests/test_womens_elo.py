from pathlib import Path
import pandas as pd
import pytest
from worldcup.algorithms.womens_elo import WomensEloRatingModel
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def model():
    return WomensEloRatingModel()


@pytest.fixture
def teams():
    df = pd.read_csv(_DATA_DIR / "teams.csv")
    return [Team(row["name"], row["group"], int(row["fifa_ranking"])) for _, row in df.iterrows()]


def test_rating_always_positive(model, teams):
    for team in teams:
        assert model.rate(team) > 0


def test_known_ratings(model):
    assert model.rate(Team("Spain", "H", 2)) == pytest.approx(2105.36)
    assert model.rate(Team("United States", "D", 17)) == pytest.approx(2057.92)


def test_stronger_womens_team_has_higher_rating(model):
    spain = Team("Spain", "H", 2)
    qatar = Team("Qatar", "B", 53)
    assert model.rate(spain) > model.rate(qatar)


def test_unranked_team_uses_fallback(model):
    qatar = Team("Qatar", "B", 53)
    assert model.rate(qatar) == model.fallback


def test_poisson_predict_sums_to_one(model):
    pred = PoissonGoalModel(model)
    spain = Team("Spain", "H", 2)
    qatar = Team("Qatar", "B", 53)
    p = pred.predict(spain, qatar)
    assert sum(p) == pytest.approx(1.0, abs=1e-6)


def test_first_vs_last_both_have_a_chance(model):
    pred = PoissonGoalModel(model)
    spain = Team("Spain", "H", 2)
    qatar = Team("Qatar", "B", 53)
    p_home, _, p_away = pred.predict(spain, qatar)
    assert p_home > 0
    assert p_away > 0
