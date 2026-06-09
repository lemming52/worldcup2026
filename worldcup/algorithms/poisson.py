from __future__ import annotations
from math import exp, factorial
from worldcup.models import Team
from worldcup.algorithms.base import RatingModel

_MAX_GOALS = 10  # upper bound for analytical probability summation


class PoissonGoalModel:
    """Wraps a RatingModel and drives simulation via independent Poisson goal distributions.

    For a match, the rating ratio determines two lambda values:
        λ_home = base_lambda * ratio ** alpha
        λ_away = base_lambda / ratio ** alpha

    so λ_home × λ_away = base_lambda² always (product is constant).

    Parameters
    ----------
    rating_model:
        Any RatingModel; supplies a positive strength value per team.
    base_lambda:
        Average goals per team per game (≈1.3 for international football).
    alpha:
        Damping exponent applied to the rating ratio. Lower values compress
        the effect of mismatches. At alpha=0.15 a 92:1 ratio gives a ~1.9×
        multiplier (~2.5 vs ~0.68 goals), which is realistic for football.
    max_ratio:
        Hard cap on the rating ratio before the power law is applied.
        Prevents extreme Poisson lambdas for very large mismatches.
    """

    def __init__(
        self,
        rating_model: RatingModel,
        base_lambda: float = 1.3,
        alpha: float = 0.3,
        max_ratio: float = 10.0,
    ) -> None:
        self.rating_model = rating_model
        self.base_lambda = base_lambda
        self.alpha = alpha
        self.max_ratio = max_ratio
        self.name = f"poisson_{rating_model.name}"

    def lambdas(self, home: Team, away: Team) -> tuple[float, float]:
        r_home = self.rating_model.rate(home)
        r_away = self.rating_model.rate(away)
        ratio = min(self.max_ratio, r_home / r_away)
        # Also apply the floor so away can't be capped more than home is capped
        ratio = max(1.0 / self.max_ratio, ratio)
        multiplier = ratio ** self.alpha
        return self.base_lambda * multiplier, self.base_lambda / multiplier

    def predict(self, home: Team, away: Team) -> tuple[float, float, float]:
        """Analytically derive outcome probabilities from the Poisson joint distribution."""
        λ_h, λ_a = self.lambdas(home, away)
        return _poisson_outcome_probs(λ_h, λ_a)


def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0.0:
        return 1.0 if k == 0 else 0.0
    return exp(-lam) * (lam ** k) / factorial(k)


def _poisson_outcome_probs(
    lam_home: float, lam_away: float, max_goals: int = _MAX_GOALS
) -> tuple[float, float, float]:
    p_home = p_draw = p_away = 0.0
    for h in range(max_goals + 1):
        ph = _poisson_pmf(h, lam_home)
        for a in range(max_goals + 1):
            p = ph * _poisson_pmf(a, lam_away)
            if h > a:
                p_home += p
            elif h == a:
                p_draw += p
            else:
                p_away += p
    total = p_home + p_draw + p_away
    return p_home / total, p_draw / total, p_away / total
