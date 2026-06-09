from __future__ import annotations
from pathlib import Path
import pandas as pd
from worldcup.models import Team, TeamRecord, MatchOutcome

_DATA_DIR = Path(__file__).parent.parent / "data"


def load_teams(path: Path | None = None) -> list[Team]:
    csv = path or (_DATA_DIR / "teams.csv")
    df = pd.read_csv(csv)
    return [
        Team(name=row["name"], group=row["group"], fifa_ranking=int(row["fifa_ranking"]), flag=str(row.get("flag", "")))
        for _, row in df.iterrows()
    ]


def get_groups(teams: list[Team]) -> dict[str, list[Team]]:
    groups: dict[str, list[Team]] = {}
    for team in teams:
        groups.setdefault(team.group, []).append(team)
    return dict(sorted(groups.items()))


def get_group_matches(teams: list[Team]) -> list[tuple[Team, Team]]:
    """All round-robin pairs within the group (home, away)."""
    matches = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            matches.append((teams[i], teams[j]))
    return matches


def compute_standings(
    teams: list[Team],
    results: list[tuple[Team, Team, MatchOutcome]],
) -> list[TeamRecord]:
    records: dict[str, TeamRecord] = {t.name: TeamRecord(team=t) for t in teams}

    for home, away, outcome in results:
        records[home.name].update(outcome.home_goals, outcome.away_goals)
        records[away.name].update(outcome.away_goals, outcome.home_goals)

    sorted_records = _sort_standings(list(records.values()), results)
    return sorted_records


def _sort_standings(
    records: list[TeamRecord],
    results: list[tuple[Team, Team, MatchOutcome]],
) -> list[TeamRecord]:
    # Primary sort: points, GD, GF
    def sort_key(r: TeamRecord) -> tuple:
        return (-r.points, -r.goal_difference, -r.goals_for)

    records.sort(key=sort_key)

    # Break remaining ties by head-to-head among tied groups
    records = _resolve_head_to_head(records, results)
    return records


def _resolve_head_to_head(
    records: list[TeamRecord],
    results: list[tuple[Team, Team, MatchOutcome]],
) -> list[TeamRecord]:
    """Resolve ties by head-to-head points then GD among tied teams."""
    n = len(records)
    i = 0
    while i < n:
        j = i + 1
        while j < n and _tied_on_primary(records[i], records[j]):
            j += 1
        if j - i > 1:
            tied = records[i:j]
            tied_names = {r.team.name for r in tied}
            h2h_results = [
                (h, a, o)
                for h, a, o in results
                if h.name in tied_names and a.name in tied_names
            ]
            tied.sort(key=lambda r: _h2h_sort_key(r, h2h_results))
            records[i:j] = tied
        i = j
    return records


def _tied_on_primary(a: TeamRecord, b: TeamRecord) -> bool:
    return (a.points, a.goal_difference, a.goals_for) == (
        b.points,
        b.goal_difference,
        b.goals_for,
    )


def _h2h_sort_key(
    record: TeamRecord,
    h2h_results: list[tuple[Team, Team, MatchOutcome]],
) -> tuple:
    pts = 0
    gd = 0
    for home, away, outcome in h2h_results:
        if home.name == record.team.name:
            if outcome.result == "home":
                pts += 3
            elif outcome.result == "draw":
                pts += 1
            gd += outcome.home_goals - outcome.away_goals
        elif away.name == record.team.name:
            if outcome.result == "away":
                pts += 3
            elif outcome.result == "draw":
                pts += 1
            gd += outcome.away_goals - outcome.home_goals
    return (-pts, -gd)
