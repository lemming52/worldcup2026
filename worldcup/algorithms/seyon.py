from __future__ import annotations
from math import exp
from pathlib import Path
import pandas as pd
from worldcup.models import Team

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


class SeyonPredictor:
    """Match predictor based on historical humidity at each team's capital city.

    For a given match on date D, the model looks up the relative humidity at
    each team's capital on the same calendar date in the prior year (2025).
    The team from the more humid capital is predicted to win more often.

    Humidity source: Open-Meteo daily mean relative humidity at 2m (Jun 11–27 2025).
    """

    name = "seyon"

    def __init__(
        self,
        k: float = 0.03,
        draw_rate: float = 0.25,
        schedule_path: Path | None = None,
        humidity_path: Path | None = None,
        capitals_path: Path | None = None,
    ) -> None:
        self.k = k
        self.draw_rate = draw_rate

        schedule_csv  = schedule_path  or (_DATA_DIR / "schedule.csv")
        humidity_csv  = humidity_path  or (_DATA_DIR / "humidity_2025.csv")
        capitals_csv  = capitals_path  or (_DATA_DIR / "capitals.csv")

        # team_name → capital_name
        caps_df = pd.read_csv(capitals_csv)
        self._capitals: dict[str, str] = dict(zip(caps_df["team"], caps_df["capital"]))

        # frozenset({home, away}) → "YYYY-MM-DD" (mapped to prior year)
        sched_df = pd.read_csv(schedule_csv)
        self._schedule: dict[frozenset, str] = {}
        for _, row in sched_df.iterrows():
            key = frozenset({str(row["home"]), str(row["away"])})
            # Convert 2026 date to 2025 for humidity lookup
            date_2025 = str(row["date"]).replace("2026", "2025")
            self._schedule[key] = date_2025

        # (capital, "YYYY-MM-DD") → humidity float
        hum_df = pd.read_csv(humidity_csv)
        self._humidity: dict[tuple[str, str], float] = {}
        self._capital_means: dict[str, float] = {}
        for capital, grp in hum_df.groupby("capital"):
            mean = float(grp["humidity"].mean())
            self._capital_means[str(capital)] = mean
            for _, row in grp.iterrows():
                self._humidity[(str(capital), str(row["date"]))] = float(row["humidity"])

    def _get_humidity(self, team_name: str, date: str) -> float:
        capital = self._capitals[team_name]
        key = (capital, date)
        if key in self._humidity:
            return self._humidity[key]
        # Fallback: mean humidity for that capital across the tournament window
        return self._capital_means.get(capital, 50.0)

    def predict(self, home: Team, away: Team) -> tuple[float, float, float]:
        key = frozenset({home.name, away.name})
        if key not in self._schedule:
            raise KeyError(
                f"SeyonPredictor: no schedule entry for {home.name} vs {away.name}. "
                "Check data/schedule.csv."
            )
        date = self._schedule[key]

        h_hum = self._get_humidity(home.name, date)
        a_hum = self._get_humidity(away.name, date)

        delta = h_hum - a_hum
        p_home_raw = _sigmoid(self.k * delta)

        p_home_win = p_home_raw * (1.0 - self.draw_rate)
        p_away_win = (1.0 - p_home_raw) * (1.0 - self.draw_rate)

        return p_home_win, self.draw_rate, p_away_win
