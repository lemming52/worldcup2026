from __future__ import annotations
from pathlib import Path
import pandas as pd
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


class NathanRatingModel:
    """Combines FIFA Elo points with an inverted LGBT equality index.

    The equality index (Equaldex, 0–100) is deliberately inverted: a score of 0
    (least equal) contributes the maximum equality component to the rating.

    FIFA points are normalised to [0, 1] relative to the highest-ranked team in
    the dataset (higher points = higher score), replacing the previous rank-based
    approach which over-penalised small gaps at the top (rank 1 vs rank 2).

    rating = w_fifa * (points / max_points)^fifa_power
           + w_equality * ((100 - equality) / 100)
    """

    name = "nathan"

    def __init__(
        self,
        fifa_power: float = 1.0,
        w_fifa: float = 0.5,
        w_equality: float = 0.5,
        equality_fallback: float = 50.0,
        rankings_path: Path | None = None,
    ) -> None:
        self.fifa_power = fifa_power
        self.w_fifa = w_fifa
        self.w_equality = w_equality
        self.equality_fallback = equality_fallback

        csv = rankings_path or (_DATA_DIR / "rankings.csv")
        df = pd.read_csv(csv)
        self._rankings: dict[str, tuple[int, float, float]] = {
            str(row["country"]): (
                int(row["fifa_ranking"]),
                float(row["fifa_points"]),
                float(row["equality_index"]) if pd.notna(row["equality_index"]) else equality_fallback,
            )
            for _, row in df.iterrows()
        }
        self._max_points = max(pts for _, pts, _ in self._rankings.values())

    def _lookup(self, team_name: str) -> tuple[int, float, float]:
        if team_name in self._rankings:
            return self._rankings[team_name]
        raise KeyError(
            f"NathanRatingModel: no entry for '{team_name}' in rankings.csv. "
            "Run scripts/build_rankings.py to rebuild the dataset."
        )

    def rate(self, team: Team) -> float:
        _, points, equality_index = self._lookup(team.name)

        # FIFA component: higher points = higher score, normalised to [0, 1]
        fifa_score = (points / self._max_points) ** self.fifa_power

        # Equality component: INVERTED — score 0 → 1.0, score 100 → 0.0
        eq_score = (100.0 - equality_index) / 100.0

        return self.w_fifa * fifa_score + self.w_equality * eq_score
