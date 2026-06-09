from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from worldcup.models import Team
from worldcup.algorithms.base import MatchPredictor

_DATA_DIR = Path(__file__).parent.parent / "data"
_SIM_DIR = _DATA_DIR / "sim_results"


def load_results(path: Path | None = None) -> pd.DataFrame:
    csv = path or (_DATA_DIR / "results.csv")
    df = pd.read_csv(csv)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df


def load_predictions(model_name: str, path: Path | None = None) -> pd.DataFrame | None:
    """Load frozen per-match predictions saved at simulation time, if they exist."""
    csv = path or (_SIM_DIR / f"{model_name}_predictions.csv")
    if not csv.exists():
        return None
    return pd.read_csv(csv)


def evaluate(
    predictor: MatchPredictor,
    teams: list[Team],
    results_path: Path | None = None,
    predictions_path: Path | None = None,
) -> dict[str, float]:
    """Compute Brier score and log loss against actual results.

    Uses frozen per-match predictions saved at simulation time when available.
    Falls back to a live call to predictor.predict() if no predictions file exists.

    Returns a dict with keys 'brier_score', 'log_loss', 'n_matches', 'used_frozen'.
    Returns empty dict if no actual results are recorded yet.
    """
    results_df = load_results(results_path)
    if results_df.empty:
        return {}

    frozen = load_predictions(predictor.name, predictions_path)
    used_frozen = frozen is not None

    if used_frozen:
        # Build a lookup keyed by (home, away)
        pred_map: dict[tuple[str, str], tuple[float, float, float]] = {
            (str(row["home"]), str(row["away"])): (
                float(row["p_home_win"]),
                float(row["p_draw"]),
                float(row["p_away_win"]),
            )
            for _, row in frozen.iterrows()
        }
    else:
        team_map = {t.name: t for t in teams}

    brier_terms: list[float] = []
    log_loss_terms: list[float] = []

    for _, row in results_df.iterrows():
        home_name, away_name = str(row["home"]), str(row["away"])

        if used_frozen:
            entry = pred_map.get((home_name, away_name))
            if entry is None:
                continue
            p_home, p_draw, p_away = entry
        else:
            if home_name not in team_map or away_name not in team_map:
                continue
            p_home, p_draw, p_away = predictor.predict(
                team_map[home_name], team_map[away_name]
            )

        probs = np.array([p_home, p_draw, p_away], dtype=float)

        hg, ag = int(row["home_goals"]), int(row["away_goals"])
        if hg > ag:
            actual = np.array([1.0, 0.0, 0.0])
        elif hg == ag:
            actual = np.array([0.0, 1.0, 0.0])
        else:
            actual = np.array([0.0, 0.0, 1.0])

        brier_terms.append(float(np.sum((probs - actual) ** 2)))
        p_actual = float(probs @ actual)
        log_loss_terms.append(-np.log(max(p_actual, 1e-15)))

    if not brier_terms:
        return {}

    return {
        "brier_score": float(np.mean(brier_terms)),
        "log_loss": float(np.mean(log_loss_terms)),
        "n_matches": len(brier_terms),
        "used_frozen": used_frozen,
    }
