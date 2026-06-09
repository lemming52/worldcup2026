import numpy as np
from worldcup.models import Team


class RankingPredictor:
    """Win probability derived from FIFA ranking difference via logistic function.

    A lower FIFA ranking number means a better team. The ranking gap between
    two teams is fed into a sigmoid to produce a raw win probability, then a
    fixed draw_rate is carved out proportionally from both sides.
    """

    name = "ranking"

    def __init__(self, k: float = 0.015, draw_rate: float = 0.25):
        self.k = k
        self.draw_rate = draw_rate

    def predict(self, home: Team, away: Team) -> tuple[float, float, float]:
        # Positive delta means away is ranked higher (weaker), home is favoured.
        delta = away.fifa_ranking - home.fifa_ranking
        p_home_raw = float(1 / (1 + np.exp(-self.k * delta)))
        p_away_raw = 1.0 - p_home_raw

        p_home_win = p_home_raw * (1.0 - self.draw_rate)
        p_away_win = p_away_raw * (1.0 - self.draw_rate)
        p_draw = self.draw_rate

        return (p_home_win, p_draw, p_away_win)
