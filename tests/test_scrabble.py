from pathlib import Path
import pandas as pd
import pytest
from worldcup.algorithms.scrabble import ScrabbleRatingModel, word_score, letters
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def model():
    return ScrabbleRatingModel()


@pytest.fixture
def teams():
    df = pd.read_csv(_DATA_DIR / "teams.csv")
    return [Team(row["name"], row["group"], int(row["fifa_ranking"])) for _, row in df.iterrows()]


def test_letters_strips_accents_spaces_and_punctuation():
    assert letters("Côte d'Ivoire") == list("COTEDIVOIRE")
    assert letters("Bosnia-Herzegovina") == list("BOSNIAHERZEGOVINA")


def test_word_score_known_values():
    assert word_score("Iran") == 4   # I+R+A+N = 1+1+1+1
    assert word_score("Brazil") == 17  # B+R+A+Z+I+L = 3+1+1+10+1+1


def test_rating_is_double_word_score(model):
    iran = Team("Iran", "G", 21)
    assert model.rate(iran) == pytest.approx(2 * word_score("Iran"))


def test_rating_always_positive(model, teams):
    for team in teams:
        assert model.rate(team) > 0


def test_longer_higher_value_name_scores_more(model):
    bosnia = Team("Bosnia-Herzegovina", "B", 57)
    iran = Team("Iran", "G", 21)
    assert model.rate(bosnia) > model.rate(iran)


def test_poisson_predict_sums_to_one(model):
    pred = PoissonGoalModel(model)
    bosnia = Team("Bosnia-Herzegovina", "B", 57)
    iran = Team("Iran", "G", 21)
    p = pred.predict(bosnia, iran)
    assert sum(p) == pytest.approx(1.0, abs=1e-6)


def test_first_vs_last_both_have_a_chance(model):
    pred = PoissonGoalModel(model)
    bosnia = Team("Bosnia-Herzegovina", "B", 57)
    iran = Team("Iran", "G", 21)
    p_home, _, p_away = pred.predict(bosnia, iran)
    assert p_home > 0
    assert p_away > 0
