from worldcup.algorithms.base import MatchPredictor
from worldcup.algorithms.uniform import UniformPredictor
from worldcup.algorithms.ranking import RankingPredictor

REGISTRY: dict[str, MatchPredictor] = {
    "uniform": UniformPredictor(),
    "ranking": RankingPredictor(),
}

__all__ = ["MatchPredictor", "UniformPredictor", "RankingPredictor", "REGISTRY"]
