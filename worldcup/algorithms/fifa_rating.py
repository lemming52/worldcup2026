from worldcup.models import Team


class FIFARatingModel:
    """Team strength derived from FIFA ranking via a power transform.

    rating = 1 / ranking ** power

    power=1.0 makes rank 2 half as strong as rank 1 (too aggressive at the top).
    power=0.5 (default) uses the square root, so rank 1 vs rank 2 is a 1.41× ratio
    rather than 2×, while still giving meaningful separation across the full range.
    The absolute scale is irrelevant — only the ratio between two teams is used.
    """

    name = "fifa"

    def __init__(self, power: float = 0.5) -> None:
        self.power = power

    def rate(self, team: Team) -> float:
        return 1.0 / (team.fifa_ranking ** self.power)
