import pandas as pd
import numpy as np


def gap_pct(driver_time: float, fastest_time: float) -> float:
    """Gap as % of fastest time."""
    return (driver_time - fastest_time) / fastest_time * 100


def calculate_hidden_pace(quali_df: pd.DataFrame, race_df: pd.DataFrame,
                           race: str, season: int) -> pd.DataFrame:
    """
    Merge qualifying and race pace DataFrames and compute hidden_pace per driver.

    hidden_pace > 0 → driver is BETTER in race than qualifying suggests
    hidden_pace < 0 → driver is BETTER in qualifying than in race
    """
    merged = pd.merge(quali_df, race_df, on="Driver", how="inner")
    if merged.empty:
        return pd.DataFrame()

    fastest_quali = merged["QualiTime_sec"].min()
    fastest_race = merged["RacePace_sec"].min()

    merged["QualiGap_pct"] = merged["QualiTime_sec"].apply(
        lambda t: gap_pct(t, fastest_quali)
    )
    merged["RaceGap_pct"] = merged["RacePace_sec"].apply(
        lambda t: gap_pct(t, fastest_race)
    )
    merged["HiddenPace"] = merged["QualiGap_pct"] - merged["RaceGap_pct"]
    merged["Race"] = race
    merged["Season"] = season

    return merged[["Driver", "Season", "Race", "QualiGap_pct", "RaceGap_pct", "HiddenPace"]]


def aggregate_by_team(df: pd.DataFrame) -> pd.DataFrame:
    """Group hidden pace stats by team."""
    return (
        df.groupby("Team")
        .agg(
            AvgHiddenPace=("HiddenPace", "mean"),
            StdHiddenPace=("HiddenPace", "std"),
            RacesAnalyzed=("Race", "count"),
        )
        .sort_values("AvgHiddenPace", ascending=False)
        .reset_index()
    )


def compute_correlation(df: pd.DataFrame, position_col: str = "RaceGap_pct") -> tuple[float, float]:
    """Pearson correlation between hidden pace and race gap (proxy for final position)."""
    from scipy.stats import pearsonr
    cols = ["HiddenPace", position_col]
    clean = df[cols].dropna()
    if len(clean) < 3:
        return float("nan"), float("nan")
    return pearsonr(clean["HiddenPace"], clean[position_col])
