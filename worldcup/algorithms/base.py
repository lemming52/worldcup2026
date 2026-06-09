from typing import Protocol, runtime_checkable
from worldcup.models import Team


@runtime_checkable
class MatchPredictor(Protocol):
    name: str

    def predict(self, home: Team, away: Team) -> tuple[float, float, float]:
        """Return (p_home_win, p_draw, p_away_win). Values must sum to 1."""
        ...


@runtime_checkable
class RatingModel(Protocol):
    name: str

    def rate(self, team: Team) -> float:
        """Return a positive strength rating. Higher = stronger team."""
        ...
