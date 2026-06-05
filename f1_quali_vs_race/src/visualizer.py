import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from team_mapping import get_team_color

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="darkgrid", context="notebook")
plt.rcParams.update({
    "figure.facecolor": "#111111",
    "axes.facecolor": "#1a1a1a",
    "axes.edgecolor": "#444444",
    "text.color": "white",
    "axes.labelcolor": "white",
    "xtick.color": "white",
    "ytick.color": "white",
    "grid.color": "#333333",
    "legend.facecolor": "#1a1a1a",
    "legend.edgecolor": "#444444",
})


def _team_palette(teams: list[str]) -> dict:
    return {t: get_team_color(t) for t in teams}


def plot_scatter(df: pd.DataFrame, race: str, season: int, save: bool = True) -> plt.Figure:
    """Scatter: qualifying gap vs race pace gap per driver, with diagonal baseline."""
    fig, ax = plt.subplots(figsize=(10, 8))

    teams = df["Team"].unique()
    palette = _team_palette(list(teams))

    sns.scatterplot(
        data=df, x="QualiGap_pct", y="RaceGap_pct",
        hue="Team", palette=palette, s=120, ax=ax, zorder=3,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["Driver"],
            (row["QualiGap_pct"], row["RaceGap_pct"]),
            textcoords="offset points", xytext=(6, 4),
            fontsize=8, color="white", alpha=0.9,
        )

    max_val = max(df[["QualiGap_pct", "RaceGap_pct"]].max()) * 1.1
    ax.plot([0, max_val], [0, max_val], "w--", alpha=0.4, linewidth=1, label="No hiding baseline")

    # below diagonal = better in race (hidden pace), above = better in quali
    ax.fill_between([0, max_val], [0, max_val], 0, alpha=0.05, color="green", label="Better in race")
    ax.fill_between([0, max_val], [0, max_val], max_val, alpha=0.05, color="red", label="Better in quali")

    ax.set_title(f"Quali vs Race Pace — {season} {race}", fontsize=14, pad=12)
    ax.set_xlabel("Qualifying Gap to Fastest (%)")
    ax.set_ylabel("Race Pace Gap to Fastest (%)")
    ax.legend(loc="upper left", fontsize=8)

    plt.tight_layout()
    if save:
        fig.savefig(OUTPUT_DIR / f"scatter_{season}_{race.replace(' ', '_')}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_team_bar(team_summary: pd.DataFrame, season: int, save: bool = True) -> plt.Figure:
    """Bar chart: avg hidden pace per team for a season."""
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = [get_team_color(t) for t in team_summary["Team"]]

    bars = ax.bar(team_summary["Team"], team_summary["AvgHiddenPace"], color=colors, zorder=3)
    ax.axhline(0, color="white", linewidth=0.8, linestyle="--", alpha=0.5)

    for bar, val in zip(bars, team_summary["AvgHiddenPace"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + (0.02 if val >= 0 else -0.06),
            f"{val:.2f}%", ha="center", va="bottom", fontsize=9, color="white",
        )

    ax.set_title(f"Average Hidden Race Pace by Team — {season}", fontsize=14, pad=12)
    ax.set_xlabel("Team")
    ax.set_ylabel("Avg Hidden Pace (%)\n(+positive = better in race)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / f"team_bar_{season}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig


def plot_heatmap(df: pd.DataFrame, season: int, save: bool = True) -> plt.Figure:
    """Heatmap: hidden pace per team per race."""
    pivot = df.pivot_table(index="Team", columns="Race", values="HiddenPace")

    # shorten race names for readability
    pivot.columns = [c.replace(" Grand Prix", "").replace("Grand Prix", "")[:12] for c in pivot.columns]

    fig, ax = plt.subplots(figsize=(max(14, len(pivot.columns) * 0.8), max(6, len(pivot.index) * 0.6)))
    sns.heatmap(
        pivot, cmap="RdYlGn", center=0, annot=True, fmt=".1f",
        linewidths=0.5, linecolor="#333333",
        cbar_kws={"label": "Hidden Pace (%)"},
        ax=ax,
    )
    ax.set_title(f"Hidden Race Pace by Team & Race — {season}", fontsize=14, pad=12)
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()

    if save:
        fig.savefig(OUTPUT_DIR / f"heatmap_{season}.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig
