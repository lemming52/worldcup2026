from __future__ import annotations
from pathlib import Path
import pandas as pd
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# FIFA team names that differ from the canonical names used in rankings.csv
_TEAM_TO_CANONICAL: dict[str, str] = {
    "United States": "United States",  # teams.csv uses "United States", rankings.csv too
}


class NathanRatingModel:
    """Combines FIFA ranking strength with an inverted LGBT equality index.

    The equality index (Equaldex, 0–100) is deliberately inverted: a score of 0
    (least equal) contributes the maximum equality component to the rating.
    The hypothesis being tested is whether lower LGBT equality correlates with
    stronger international football performance.

    rating = w_fifa * (1 / rank^fifa_power) + w_equality * ((100 - equality) / 100)

    Parameters
    ----------
    fifa_power:
        Power transform on the FIFA rank (same as FIFARatingModel). Default 0.5.
    w_fifa:
        Weight on the FIFA component. Default 0.5.
    w_equality:
        Weight on the inverted equality component. Default 0.5.
    equality_fallback:
        Score to use when a team has no equality index entry. Default 50 (neutral).
    """

    name = "nathan"

    def __init__(
        self,
        fifa_power: float = 0.5,
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
        self._rankings: dict[str, tuple[int, float]] = {
            str(row["country"]): (
                int(row["fifa_ranking"]),
                float(row["equality_index"]) if pd.notna(row["equality_index"]) else equality_fallback,
            )
            for _, row in df.iterrows()
        }

    def _lookup(self, team_name: str) -> tuple[int, float]:
        canonical = _TEAM_TO_CANONICAL.get(team_name, team_name)
        if canonical in self._rankings:
            return self._rankings[canonical]
        raise KeyError(
            f"NathanRatingModel: no entry for '{team_name}' in rankings.csv. "
            "Run scripts/build_rankings.py to rebuild the dataset."
        )

    def rate(self, team: Team) -> float:
        fifa_rank, equality_index = self._lookup(team.name)

        # FIFA component: lower rank = higher score
        fifa_score = 1.0 / (fifa_rank ** self.fifa_power)

        # Equality component: INVERTED — score 0 → 1.0, score 100 → 0.0
        eq_score = (100.0 - equality_index) / 100.0

        return self.w_fifa * fifa_score + self.w_equality * eq_score
