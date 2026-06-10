from worldcup.algorithms.base import MatchPredictor, RatingModel
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor
from worldcup.algorithms.fifa_rating import FIFARatingModel
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.algorithms.nathan_rating import NathanRatingModel
from worldcup.algorithms.seyon import SeyonPredictor

REGISTRY: dict[str, object] = {
    "uniform":      UniformPredictor(),
    "ranking":      RankingPredictor(),
    "poisson_fifa": PoissonGoalModel(FIFARatingModel()),
    "nathan":       PoissonGoalModel(NathanRatingModel()),
    "seyon":        SeyonPredictor(),
}

__all__ = [
    "MatchPredictor", "RatingModel",
    "UniformPredictor", "RankingPredictor",
    "FIFARatingModel", "PoissonGoalModel",
    "NathanRatingModel", "SeyonPredictor",
    "REGISTRY",
]
