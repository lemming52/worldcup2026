from pathlib import Path
import pandas as pd
import pytest
from worldcup.algorithms.animaniacs import AnimaniacsRatingModel, _SONG_ORDER
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def model():
    return AnimaniacsRatingModel()


@pytest.fixture
def teams():
    df = pd.read_csv(_DATA_DIR / "teams.csv")
    return [Team(row["name"], row["group"], int(row["fifa_ranking"])) for _, row in df.iterrows()]


def test_all_teams_resolve(model, teams):
    for team in teams:
        model._song_rank(team.name)


def test_known_ranks(model):
    assert model._song_rank("United States") == 1
    assert model._song_rank("Canada") == 2
    assert model._song_rank("Cape Verde") == 193


def test_alias_ranks_match_shared_slot(model):
    assert model._song_rank("Curaçao") == model._song_rank("Netherlands")
    assert model._song_rank("Croatia") == _SONG_ORDER.index("Yugoslavia") + 1


def test_lower_rank_gives_higher_rating(model):
    usa = Team("United States", "D", 17)
    brazil = Team("Brazil", "C", 6)
    cape_verde = Team("Cape Verde", "H", 70)
    assert model.rate(usa) > model.rate(brazil) > model.rate(cape_verde)


def test_rating_always_positive(model, teams):
    for team in teams:
        assert model.rate(team) > 0


def test_midpoint_rank_gives_average_elo(model):
    mid_team = Team("Mid", "X", 1)
    mid_rank = round(model._mid_rank)
    place = _SONG_ORDER[mid_rank - 1]
    mid_team_via_alias = Team(place, "X", 1)
    assert model.rate(mid_team_via_alias) == pytest.approx(model._avg_elo, abs=model._elo_per_step)


def test_poisson_predict_sums_to_one(model):
    pred = PoissonGoalModel(model)
    usa = Team("United States", "D", 17)
    cape_verde = Team("Cape Verde", "H", 70)
    p = pred.predict(usa, cape_verde)
    assert sum(p) == pytest.approx(1.0, abs=1e-6)


def test_first_vs_last_both_have_a_chance(model):
    pred = PoissonGoalModel(model)
    usa = Team("United States", "D", 17)
    cape_verde = Team("Cape Verde", "H", 70)
    p_home, _, p_away = pred.predict(usa, cape_verde)
    assert p_home > 0
    assert p_away > 0
