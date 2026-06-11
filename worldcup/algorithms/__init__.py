from worldcup.algorithms.base import MatchPredictor, RatingModel
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor
from worldcup.algorithms.fifa_rating import FIFARatingModel
from worldcup.algorithms.poisson import PoissonGoalModel
from worldcup.algorithms.nathan_rating import NathanRatingModel
from worldcup.algorithms.seyon import SeyonPredictor
from worldcup.algorithms.animaniacs import AnimaniacsRatingModel
from worldcup.algorithms.womens_elo import WomensEloRatingModel
from worldcup.algorithms.scrabble import ScrabbleRatingModel

REGISTRY: dict[str, object] = {
    "uniform":      UniformPredictor(),
    "ranking":      RankingPredictor(),
    "poisson_fifa": PoissonGoalModel(FIFARatingModel()),
    "nathan":       PoissonGoalModel(NathanRatingModel()),
    "seyon":        SeyonPredictor(),
    "animaniacs":   PoissonGoalModel(AnimaniacsRatingModel()),
    "womens_elo":   PoissonGoalModel(WomensEloRatingModel()),
    "scrabble":     PoissonGoalModel(ScrabbleRatingModel()),
}

__all__ = [
    "MatchPredictor", "RatingModel",
    "UniformPredictor", "RankingPredictor",
    "FIFARatingModel", "PoissonGoalModel",
    "NathanRatingModel", "SeyonPredictor",
    "AnimaniacsRatingModel", "WomensEloRatingModel",
    "ScrabbleRatingModel",
    "REGISTRY",
]
