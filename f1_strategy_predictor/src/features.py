import pandas as pd
import numpy as np

COMPOUND_MAP = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}

# Circuit archetypes — pit strategy differs a lot by track character.
#   0 = street (quali-dominant, pit mostly on SC)
#   1 = power / low-downforce (undercut-heavy)
#   2 = tyre-killer / high-degradation (strategy-defined stops)
#   3 = balanced
CIRCUIT_TYPE = {
    # street
    "Monaco": 0, "Azerbaijan": 0, "Singapore": 0, "Las Vegas": 0,
    "Miami": 0, "Saudi Arabian": 0, "Australian": 0,
    # power / low-downforce
    "Italian": 1, "Belgian": 1, "Mexico City": 1, "São Paulo": 1, "Sao Paulo": 1,
    # tyre-killer / high-deg
    "Spanish": 2, "British": 2, "Hungarian": 2, "Japanese": 2,
    "Qatar": 2, "Turkish": 2, "Bahrain": 2, "Portuguese": 2,
}


def _circuit_type(race_name: str) -> int:
    for key, val in CIRCUIT_TYPE.items():
        if key in race_name:
            return val
    return 3  # balanced default


def compute_position_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Per-lap, position-sorted features:
      GapToAhead, GapToBehind, and the tyre life of the car directly behind
      (used to detect undercut threat). Computed from cumulative race time.
    """
    df = df.copy()
    df = df.sort_values(["Season", "Race", "Driver", "LapNumber"])
    df["CumTime"] = df.groupby(["Season", "Race", "Driver"])["LapTime_sec"].cumsum()

    out = []
    for _, group in df.groupby(["Season", "Race", "LapNumber"]):
        g = group.sort_values("Position").copy()
        g["GapToAhead"] = g["CumTime"].diff().fillna(0).abs()
        g["GapToBehind"] = g["CumTime"].diff(periods=-1).fillna(0).abs()
        g["TyreLifeBehind"] = g["TyreLife"].shift(-1)
        out.append(g)

    result = pd.concat(out).sort_index()
    return result


def build_features(raw_laps: pd.DataFrame) -> pd.DataFrame:
    df = raw_laps.copy().reset_index(drop=True)
    df = df[df["LapTime"].notna()].copy()

    df["LapTime_sec"] = df["LapTime"].dt.total_seconds()

    # TARGET on unfiltered data so shift(-1) references the true next lap
    df = df.sort_values(["Season", "Race", "Driver", "LapNumber"])
    df["NextLapPit"] = (
        df.groupby(["Season", "Race", "Driver"])["PitInTime"]
        .shift(-1)
        .notna()
        .astype(int)
    )

    # --- keep SC/VSC laps (flag them) — they hold ~30% of pit decisions ---
    df["IsSC"] = df["TrackStatus"].isin(["4", "5"]).astype(int)
    # still drop pit-out laps (out-lap times are garbage) and red flags (stopped)
    df = df[df["PitOutTime"].isna()].copy()
    df = df[df["TrackStatus"] != "6"].copy()

    # --- basic tyre features ---
    df["Compound_encoded"] = df["Compound"].map(COMPOUND_MAP).fillna(1)
    df["TyreLife"] = df["TyreLife"].fillna(1)
    df["Position"] = df["Position"].fillna(20)
    df["StintNumber"] = pd.to_numeric(df["Stint"], errors="coerce").fillna(1)

    # tyre degradation vs best lap on this compound this race
    best_by_compound = (
        df.groupby(["Season", "Race", "Driver", "Compound"])["LapTime_sec"]
        .transform("min")
    )
    df["TyreDegradation"] = (df["LapTime_sec"] - best_by_compound) / best_by_compound

    # --- race context ---
    df["LapsRemaining"] = df["TotalLaps"] - df["LapNumber"]
    df["RacePhasePct"] = df["LapNumber"] / df["TotalLaps"]
    df["CircuitType"] = df["Race"].apply(_circuit_type)

    # lap time vs the leader's lap on the same lap (normalised)
    leader_lap = (
        df.groupby(["Season", "Race", "LapNumber"])["LapTime_sec"].transform("min")
    )
    df["LapTimeVsLeader"] = (df["LapTime_sec"] - leader_lap) / leader_lap

    # rolling 3-lap pace per driver
    df = df.sort_values(["Season", "Race", "Driver", "LapNumber"])
    df["LapTimeRolling3"] = (
        df.groupby(["Season", "Race", "Driver"])["LapTime_sec"]
        .transform(lambda x: x.rolling(3, min_periods=1).mean())
    )

    # compounds used so far (running count of distinct compounds per driver)
    def _compounds_used(g):
        seen = set()
        counts = []
        for c in g:
            seen.add(c)
            counts.append(len(seen))
        return counts
    df["CompoundsUsedSoFar"] = (
        df.groupby(["Season", "Race", "Driver"])["Compound"]
        .transform(lambda s: _compounds_used(s.tolist()))
    )

    # --- position dynamics (gap ahead/behind + undercut threat) ---
    pos = compute_position_features(df)
    # column assignment aligns by index — safe regardless of row ordering
    df["GapToAhead"] = pos["GapToAhead"]
    df["GapToBehind"] = pos["GapToBehind"]
    df["TyreLifeBehind"] = pos["TyreLifeBehind"]

    # undercut threat: car behind is close AND on meaningfully fresher tyres
    df["UndercutThreat"] = (
        (df["GapToBehind"] < 25) & (df["TyreLifeBehind"] < df["TyreLife"] - 3)
    ).fillna(False).astype(int)

    meta_cols = ["Season", "Race", "Driver", "LapNumber", "Compound", "LapTime_sec"]
    df = df[meta_cols + FEATURE_COLS + [TARGET_COL]].dropna()
    return df


FEATURE_COLS = [
    # tyre
    "TyreLife",
    "TyreDegradation",
    "Compound_encoded",
    "StintNumber",
    "CompoundsUsedSoFar",
    # position dynamics
    "Position",
    "GapToAhead",
    "GapToBehind",
    "UndercutThreat",
    # race context
    "LapsRemaining",
    "RacePhasePct",
    "LapTimeRolling3",
    "LapTimeVsLeader",
    # track / conditions
    "CircuitType",
    "IsSC",
]
TARGET_COL = "NextLapPit"
