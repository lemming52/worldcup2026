from worldcup.algorithms.base import MatchPredictor, RatingModel
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor
from worldcup.algorithms.fifa_rating import FIFARatingModel
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.algorithms.nathan_rating import NathanRatingModel

REGISTRY: dict[str, object] = {
    "uniform":      UniformPredictor(),
    "ranking":      RankingPredictor(),
    "poisson_fifa": PoissonGoalModel(FIFARatingModel()),
    "nathan":       PoissonGoalModel(NathanRatingModel()),
}

__all__ = [
    "MatchPredictor", "RatingModel",
    "UniformPredictor", "RankingPredictor",
    "FIFARatingModel", "PoissonGoalModel",
    "NathanRatingModel",
    "REGISTRY",
]
