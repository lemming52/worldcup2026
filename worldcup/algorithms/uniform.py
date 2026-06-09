from worldcup.models import Team


class UniformPredictor:
    """Baseline: equal probability for every outcome."""

    name = "uniform"

    def predict(self, home: Team, away: Team) -> tuple[float, float, float]:
        return (1 / 3, 1 / 3, 1 / 3)
