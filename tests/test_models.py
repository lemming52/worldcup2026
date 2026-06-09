import pytest
from worldcup.models import Team, MatchOutcome, TeamRecord


@pytest.fixture
def two_teams():
    return (
        Team("TeamA", "A", 10),
        Team("TeamB", "A", 20),
    )


def test_match_outcome_home_win():
    o = MatchOutcome(2, 1)
    assert o.result == "home"


def test_match_outcome_draw():
    o = MatchOutcome(1, 1)
    assert o.result == "draw"


def test_match_outcome_away_win():
    o = MatchOutcome(0, 1)
    assert o.result == "away"


def test_team_record_points():
    t = Team("X", "A", 1)
    r = TeamRecord(team=t)
    r.update(2, 0)  # win
    r.update(1, 1)  # draw
    r.update(0, 1)  # loss
    assert r.points == 4
    assert r.wins == 1
    assert r.draws == 1
    assert r.losses == 1
    assert r.goals_for == 3
    assert r.goals_against == 2
    assert r.goal_difference == 1


def test_team_record_goal_difference():
    t = Team("X", "A", 1)
    r = TeamRecord(team=t)
    r.update(3, 1)
    assert r.goal_difference == 2
