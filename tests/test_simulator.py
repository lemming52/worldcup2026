import pytest
from worldcup.models import Team
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor
from worldcup.simulator import GroupStageSimulator, _simulate_goals
from worldcup.tournament import load_teams, get_groups


@pytest.fixture
def group_a():
    return [
        Team("TeamA", "A", 10),
        Team("TeamB", "A", 20),
        Team("TeamC", "A", 30),
        Team("TeamD", "A", 40),
    ]


def test_simulate_group_returns_four(group_a):
    sim = GroupStageSimulator(UniformPredictor(), n=1, seed=0)
    standings = sim._simulate_group(group_a)
    assert len(standings) == 4


def test_simulate_group_all_played_three(group_a):
    sim = GroupStageSimulator(UniformPredictor(), n=1, seed=0)
    standings = sim._simulate_group(group_a)
    for record in standings:
        assert record.played == 3


def test_simulate_goals_home_win():
    import numpy as np
    rng = np.random.default_rng(0)
    for _ in range(100):
        h, a = _simulate_goals("home", rng)
        assert h > a, f"Expected home win but got {h}-{a}"


def test_simulate_goals_draw():
    import numpy as np
    rng = np.random.default_rng(0)
    for _ in range(100):
        h, a = _simulate_goals("draw", rng)
        assert h == a, f"Expected draw but got {h}-{a}"


def test_simulate_goals_away_win():
    import numpy as np
    rng = np.random.default_rng(0)
    for _ in range(100):
        h, a = _simulate_goals("away", rng)
        assert a > h, f"Expected away win but got {h}-{a}"


def test_full_simulation_counts(group_a):
    n = 500
    sim = GroupStageSimulator(UniformPredictor(), n=n, seed=42)
    groups = {"A": group_a}
    results = sim.run(groups)
    df = results.to_dataframe()

    # With uniform predictor and 1 group of 4, only top 2 qualify (no best-3rd logic applies)
    for _, row in df.iterrows():
        assert 0.0 <= row["p_qualify"] <= 1.0
        assert abs(row["p_group_winner"] + row["p_runner_up"] + row["p_best_third"] + row["p_eliminated"] - 1.0) < 1e-6


def test_full_simulation_real_data():
    """Smoke test: run a simulation against the actual WC 2026 data."""
    teams = load_teams()
    groups = get_groups(teams)
    sim = GroupStageSimulator(RankingPredictor(), n=200, seed=0)
    results = sim.run(groups)
    df = results.to_dataframe()

    assert len(df) == 48
    # Total qualification probability must equal 32 teams qualifying
    total_qualifying = df["p_qualify"].sum() * 200
    # 32 teams qualify per simulation across 48 teams
    assert abs(df["p_qualify"].sum() - 32 / 48 * 48) < 1.0  # rough check


def test_uniform_qualifier_roughly_50_percent():
    """With uniform predictor, each team should have ~50% qualification chance (2/4 per group)."""
    teams = [
        Team(f"T{i}", "X", i)
        for i in range(1, 5)
    ]
    n = 2000
    sim = GroupStageSimulator(UniformPredictor(), n=n, seed=1)
    groups = {"X": teams}
    results = sim.run(groups)
    df = results.to_dataframe()

    for _, row in df.iterrows():
        # 2 out of 4 qualify automatically; best-3rd adds a fractional chance
        # In a single group, 0 best-3rd qualify (need multiple groups)
        p_qualify = row["p_runner_up"] + row["p_group_winner"]
        assert 0.35 < p_qualify < 0.65, f"{row['team']}: p_qualify={p_qualify:.2f}"
