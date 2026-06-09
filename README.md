# World Cup 2026 Simulator

Monte Carlo simulation of the FIFA World Cup 2026 group stage. Pluggable prediction algorithms let you swap models and compare their outputs.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv venv
uv sync --extra dev
source .venv/bin/activate
```

## CLI

All commands are run as `python -m worldcup <command>`.

### Simulate

Run a Monte Carlo group stage simulation and print qualification probabilities.

```bash
python -m worldcup simulate
python -m worldcup simulate --model ranking
python -m worldcup simulate --model poisson_fifa
python -m worldcup simulate --model uniform --n 50000 --seed 42
```

Results are saved to `data/sim_results/<model>.csv`. Re-runs are blocked unless you pass `--force`:

```bash
python -m worldcup simulate --model ranking --force
```

### Compare

Run all registered models and print a side-by-side qualification table.

```bash
python -m worldcup compare
python -m worldcup compare --n 20000 --seed 42
python -m worldcup compare --force   # overwrite saved results
```

### Accuracy

Score each model against actual match results recorded in `data/results.csv`.

```bash
python -m worldcup accuracy
```

### List models

```bash
python -m worldcup models
```

## Recording results

As matches are played, add rows to `data/results.csv`:

```
date,group,home,away,home_goals,away_goals
2026-06-11,A,Mexico,South Africa,2,1
```

Once results exist, `python -m worldcup accuracy` will show Brier score and log loss per model.

## Notebooks

Open JupyterLab from the project root:

```bash
jupyter lab
```

| Notebook | Purpose |
|---|---|
| `notebooks/group_stage.ipynb` | Group stage simulation charts and heatmaps |
| `notebooks/model_comparison.ipynb` | Side-by-side model comparison + accuracy over time |
| `predictions/uniform.ipynb` | Uniform baseline — algorithm explanation + predictions |
| `predictions/poisson_fifa.ipynb` | Poisson FIFA rating model — goal distributions + predictions |

## Models

| Name | Type | Description |
|---|---|---|
| `uniform` | `MatchPredictor` | Equal probability (1/3 each). Baseline. |
| `ranking` | `MatchPredictor` | Logistic function on FIFA ranking difference. |
| `poisson_fifa` | `PoissonGoalModel` | Independent Poisson goal distributions driven by FIFA rating ratio. |

## Adding a new model

**Option A — outcome probabilities** (`MatchPredictor`): implement `name: str` and `predict(home, away) -> (p_win, p_draw, p_loss)`, then register in `worldcup/algorithms/__init__.py`.

**Option B — Poisson rating** (`RatingModel`): implement `name: str` and `rate(team) -> float`, wrap with `PoissonGoalModel`, then register. Tunable parameters: `base_lambda`, `alpha`, `max_ratio`.

```python
# worldcup/algorithms/my_model.py
class MyRatingModel:
    name = "my_model"
    def rate(self, team: Team) -> float:
        return ...   # higher = stronger

# worldcup/algorithms/__init__.py
from worldcup.algorithms.my_model import MyRatingModel
REGISTRY["my_model"] = PoissonGoalModel(MyRatingModel())
```

## Tests

```bash
pytest tests/ -v
```
