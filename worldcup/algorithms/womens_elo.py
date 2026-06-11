from __future__ import annotations
from pathlib import Path
import pandas as pd
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


class WomensEloRatingModel:
    """Team strength derived from the FIFA Women's World Ranking Elo points.

    Used as a RatingModel for PoissonGoalModel: the ratio of two teams'
    women's Elo (and its inverse) sets the home/away goal lambdas, so a
    team with double the women's Elo of its opponent gets a higher lambda
    and its opponent the correspondingly lower one.

    Qatar has no FIFA-ranked senior women's national team, so it falls back
    to a rating below the lowest-ranked team in the dataset (Mauritius,
    433.66).
    """

    name = "womens_elo"

    def __init__(self, rankings_path: Path | None = None, fallback: float = 400.0) -> None:
        self.fallback = fallback
        csv = rankings_path or (_DATA_DIR / "womens_elo.csv")
        df = pd.read_csv(csv)
        self._elo: dict[str, float] = dict(zip(df["country"], df["womens_elo"]))

    def rate(self, team: Team) -> float:
        return self._elo.get(team.name, self.fallback)
