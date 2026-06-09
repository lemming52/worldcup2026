from __future__ import annotations
import click
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


@click.group()
def cli() -> None:
    """World Cup 2026 Monte Carlo simulator."""


@cli.command()
@click.option("--model", default="ranking", show_default=True,
              help="Predictor to use (uniform, ranking, or any registered name).")
@click.option("--n", default=10_000, show_default=True,
              help="Number of Monte Carlo simulations.")
@click.option("--seed", default=None, type=int,
              help="Random seed for reproducibility.")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing saved results for this model.")
def simulate(model: str, n: int, seed: int | None, force: bool) -> None:
    """Run the group stage simulation and print qualification probabilities."""
    from worldcup.algorithms import REGISTRY
    from worldcup.tournament import load_teams, get_groups
    from worldcup.simulator import GroupStageSimulator

    predictor = _get_predictor(model, REGISTRY)
    teams = load_teams()
    groups = get_groups(teams)

    console.print(f"\n[bold cyan]Running {n:,} simulations with model: [yellow]{predictor.name}[/yellow][/bold cyan]")
    with console.status("Simulating..."):
        sim = GroupStageSimulator(predictor, n=n, seed=seed)
        results = sim.run(groups)

    df = results.to_dataframe()
    _print_results_table(df, predictor.name)
    _save_results(df, predictor.name, force=force)
    _save_predictions(predictor, predictor.name, force=force)


@cli.command()
@click.option("--n", default=10_000, show_default=True,
              help="Number of Monte Carlo simulations per model.")
@click.option("--seed", default=42, show_default=True,
              help="Random seed (same seed used for all models for comparability).")
@click.option("--force", is_flag=True, default=False,
              help="Overwrite existing saved results for all models.")
def compare(n: int, seed: int, force: bool) -> None:
    """Run all registered models and print a side-by-side qualification comparison."""
    from worldcup.algorithms import REGISTRY
    from worldcup.tournament import load_teams, get_groups
    from worldcup.simulator import GroupStageSimulator
    import pandas as pd

    teams = load_teams()
    groups = get_groups(teams)
    all_dfs: dict[str, "pd.DataFrame"] = {}

    for name, predictor in REGISTRY.items():
        console.print(f"[dim]Simulating with [yellow]{name}[/yellow]...[/dim]")
        sim = GroupStageSimulator(predictor, n=n, seed=seed)
        results = sim.run(groups)
        df = results.to_dataframe()
        _save_results(df, name, force=force)
        _save_predictions(predictor, name, force=force)
        all_dfs[name] = df.set_index("team")

    model_names = list(all_dfs.keys())
    teams_list = list(all_dfs[model_names[0]].index)

    table = Table(title="Qualification probability comparison", box=box.SIMPLE_HEAVY)
    table.add_column("Team", style="bold")
    for name in model_names:
        table.add_column(f"{name}\np(qualify)", justify="right")

    for team in teams_list:
        row = [team]
        for name in model_names:
            p = all_dfs[name].loc[team, "p_qualify"]
            row.append(f"{p:.1%}")
        table.add_row(*row)

    console.print(table)


@cli.command()
def accuracy() -> None:
    """Show model accuracy metrics against actual results recorded in data/results.csv."""
    from worldcup.algorithms import REGISTRY
    from worldcup.tournament import load_teams
    from worldcup.accuracy import evaluate

    teams = load_teams()
    table = Table(title="Model accuracy vs actual results", box=box.SIMPLE_HEAVY)
    table.add_column("Model")
    table.add_column("Brier score", justify="right")
    table.add_column("Log loss", justify="right")
    table.add_column("Matches", justify="right")
    table.add_column("Predictions", justify="center")

    any_results = False
    for name, predictor in REGISTRY.items():
        metrics = evaluate(predictor, teams)
        if metrics:
            any_results = True
            source = "frozen" if metrics.get("used_frozen") else "live"
            table.add_row(
                name,
                f"{metrics['brier_score']:.4f}",
                f"{metrics['log_loss']:.4f}",
                str(int(metrics["n_matches"])),
                source,
            )
        else:
            table.add_row(name, "—", "—", "0", "—")

    if not any_results:
        console.print("[yellow]No results recorded yet. Add match results to data/results.csv.[/yellow]")
    else:
        console.print(table)


@cli.command()
def models() -> None:
    """List available prediction models."""
    from worldcup.algorithms import REGISTRY

    table = Table(title="Registered models", box=box.SIMPLE_HEAVY)
    table.add_column("Name")
    table.add_column("Class")
    for name, predictor in REGISTRY.items():
        table.add_row(name, type(predictor).__name__)
    console.print(table)


def _get_predictor(name: str, registry: dict) -> object:
    if name not in registry:
        console.print(f"[red]Unknown model '{name}'. Available: {', '.join(registry)}[/red]")
        raise SystemExit(1)
    return registry[name]


def _print_results_table(df: "import pandas; pandas.DataFrame", model_name: str) -> None:
    import pandas as pd
    table = Table(
        title=f"Group stage qualification probabilities — [yellow]{model_name}[/yellow]",
        box=box.SIMPLE_HEAVY,
    )
    table.add_column("Team", style="bold")
    table.add_column("Group", justify="center")
    table.add_column("p(qualify)", justify="right")
    table.add_column("p(1st)", justify="right")
    table.add_column("p(2nd)", justify="right")
    table.add_column("p(best 3rd)", justify="right")
    table.add_column("p(eliminated)", justify="right")

    from worldcup.tournament import load_teams
    teams = load_teams()
    team_map = {t.name: t for t in teams}

    for _, row in df.iterrows():
        name = str(row["team"])
        team = team_map.get(name)
        flag = team.flag if team else ""
        group = team.group if team else "?"
        display = f"{flag} {name}" if flag else name
        table.add_row(
            display,
            group,
            f"{row['p_qualify']:.1%}",
            f"{row['p_group_winner']:.1%}",
            f"{row['p_runner_up']:.1%}",
            f"{row['p_best_third']:.1%}",
            f"{row['p_eliminated']:.1%}",
        )
    console.print(table)


def _save_results(df: "import pandas; pandas.DataFrame", model_name: str, force: bool = False) -> None:
    from pathlib import Path
    out_dir = Path(__file__).parent.parent / "data" / "sim_results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{model_name}.csv"
    if out_path.exists() and not force:
        console.print(f"[yellow]Skipped saving — {out_path.name} already exists. Use --force to overwrite.[/yellow]")
        return
    df.to_csv(out_path, index=False)
    console.print(f"[dim]Results saved to {out_path}[/dim]")


def _save_predictions(predictor: object, model_name: str, force: bool = False) -> None:
    """Freeze per-match probabilities at run time so accuracy can be scored later."""
    from pathlib import Path
    import pandas as pd
    from worldcup.tournament import load_teams, get_groups, get_group_matches

    out_dir = Path(__file__).parent.parent / "data" / "sim_results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{model_name}_predictions.csv"

    if out_path.exists() and not force:
        console.print(f"[yellow]Skipped predictions — {out_path.name} already exists. Use --force to overwrite.[/yellow]")
        return

    teams = load_teams()
    groups = get_groups(teams)
    rows = []
    for group_name, group_teams in groups.items():
        for home, away in get_group_matches(group_teams):
            p_home, p_draw, p_away = predictor.predict(home, away)
            rows.append({
                "group": group_name,
                "home": home.name,
                "away": away.name,
                "p_home_win": round(p_home, 6),
                "p_draw": round(p_draw, 6),
                "p_away_win": round(p_away, 6),
            })

    pd.DataFrame(rows).to_csv(out_path, index=False)
    console.print(f"[dim]Predictions saved to {out_path}[/dim]")


if __name__ == "__main__":
    cli()
