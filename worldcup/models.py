from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Outcome = Literal["home", "draw", "away"]


@dataclass(frozen=True)
class Team:
    name: str
    group: str
    fifa_ranking: int
    flag: str = ""

    def __str__(self) -> str:
        return f"{self.flag} {self.name}" if self.flag else self.name


@dataclass
class MatchOutcome:
    home_goals: int
    away_goals: int

    @property
    def result(self) -> Outcome:
        if self.home_goals > self.away_goals:
            return "home"
        elif self.home_goals == self.away_goals:
            return "draw"
        return "away"


@dataclass
class TeamRecord:
    team: Team
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def update(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.wins += 1
        elif goals_for == goals_against:
            self.draws += 1
        else:
            self.losses += 1
