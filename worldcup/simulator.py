from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from worldcup.models import Team, TeamRecord, MatchOutcome, Outcome
from worldcup.algorithms.base import MatchPredictor
from worldcup.tournament import get_group_matches, compute_standings


@dataclass
class SimulationResults:
    predictor_name: str
    n_simulations: int
    # Per-team counts across all simulations
    _group_wins: dict[str, int] = field(default_factory=dict)
    _runner_ups: dict[str, int] = field(default_factory=dict)
    _best_thirds: dict[str, int] = field(default_factory=dict)
    _eliminated: dict[str, int] = field(default_factory=dict)

    def _init_team(self, name: str) -> None:
        for d in (self._group_wins, self._runner_ups, self._best_thirds, self._eliminated):
            d.setdefault(name, 0)

    def record(
        self,
        group_winners: list[str],
        runner_ups: list[str],
        best_thirds: list[str],
        eliminated: list[str],
    ) -> None:
        for name in group_winners:
            self._init_team(name)
            self._group_wins[name] += 1
        for name in runner_ups:
            self._init_team(name)
            self._runner_ups[name] += 1
        for name in best_thirds:
            self._init_team(name)
            self._best_thirds[name] += 1
        for name in eliminated:
            self._init_team(name)
            self._eliminated[name] += 1

    def to_dataframe(self) -> pd.DataFrame:
        n = self.n_simulations
        teams = sorted(self._group_wins.keys())
        rows = []
        for name in teams:
            gw = self._group_wins.get(name, 0)
            ru = self._runner_ups.get(name, 0)
            bt = self._best_thirds.get(name, 0)
            el = self._eliminated.get(name, 0)
            rows.append(
                {
                    "team": name,
                    "p_group_winner": gw / n,
                    "p_runner_up": ru / n,
                    "p_best_third": bt / n,
                    "p_qualify": (gw + ru + bt) / n,
                    "p_eliminated": el / n,
                }
            )
        df = pd.DataFrame(rows)
        return df.sort_values("p_qualify", ascending=False).reset_index(drop=True)


class GroupStageSimulator:
    def __init__(self, predictor: MatchPredictor, n: int = 10_000, seed: int | None = None):
        self.predictor = predictor
        self.n = n
        self.rng = np.random.default_rng(seed)

    def run(self, groups: dict[str, list[Team]]) -> SimulationResults:
        results = SimulationResults(
            predictor_name=self.predictor.name,
            n_simulations=self.n,
        )

        for _ in range(self.n):
            group_winners: list[str] = []
            runner_ups: list[str] = []
            third_place_records: list[TeamRecord] = []
            fourth_place: list[str] = []

            for group_teams in groups.values():
                standings = self._simulate_group(group_teams)
                group_winners.append(standings[0].team.name)
                runner_ups.append(standings[1].team.name)
                third_place_records.append(standings[2])
                fourth_place.append(standings[3].team.name)

            best_thirds, rest_thirds = _pick_best_thirds(third_place_records, n=8)

            results.record(
                group_winners=group_winners,
                runner_ups=runner_ups,
                best_thirds=[r.team.name for r in best_thirds],
                eliminated=[r.team.name for r in rest_thirds] + fourth_place,
            )

        return results

    def _simulate_group(self, teams: list[Team]) -> list[TeamRecord]:
        match_pairs = get_group_matches(teams)
        match_results: list[tuple[Team, Team, MatchOutcome]] = []

        for home, away in match_pairs:
            probs = self.predictor.predict(home, away)
            outcome_str: Outcome = self.rng.choice(
                ["home", "draw", "away"], p=list(probs)  # type: ignore[arg-type]
            )
            home_goals, away_goals = _simulate_goals(outcome_str, self.rng)
            match_results.append((home, away, MatchOutcome(home_goals, away_goals)))

        return compute_standings(teams, match_results)


def _simulate_goals(outcome: Outcome, rng: np.random.Generator) -> tuple[int, int]:
    if outcome == "draw":
        goals = int(rng.poisson(0.9))
        return goals, goals

    base = int(rng.poisson(0.9))      # loser's goals (0 or more)
    margin = int(rng.poisson(0.8)) + 1  # winner always wins by at least 1
    winner = base + margin

    if outcome == "home":
        return winner, base
    return base, winner


def _pick_best_thirds(
    records: list[TeamRecord], n: int = 8
) -> tuple[list[TeamRecord], list[TeamRecord]]:
    """Sort all third-place finishers and return (top n, rest)."""
    sorted_thirds = sorted(
        records,
        key=lambda r: (-r.points, -r.goal_difference, -r.goals_for),
    )
    return sorted_thirds[:n], sorted_thirds[n:]
