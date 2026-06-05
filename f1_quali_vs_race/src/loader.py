import fastf1
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_session(season: int, race: str, session_type: str):
    session = fastf1.get_session(season, race, session_type)
    session.load(telemetry=False)
    return session


def get_best_quali_times(session) -> pd.DataFrame:
    """Return best qualifying lap per driver."""
    laps = session.laps.pick_quicklaps()
    laps["LapTime_sec"] = laps["LapTime"].dt.total_seconds()
    best = laps.groupby("Driver")["LapTime_sec"].min().reset_index()
    best.columns = ["Driver", "QualiTime_sec"]
    return best


def get_clean_race_pace(session, lap_start: int = 5, lap_end: int = 15) -> pd.DataFrame:
    """Return median race pace per driver from clean laps (no SC/VSC/pit)."""
    laps = session.laps.copy()
    laps["LapTime_sec"] = laps["LapTime"].dt.total_seconds()

    clean = laps[
        (laps["LapNumber"] >= lap_start) &
        (laps["LapNumber"] <= lap_end) &
        laps["PitInTime"].isna() &
        laps["PitOutTime"].isna() &
        (~laps["TrackStatus"].isin(["4", "5", "6"])) &
        laps["LapTime"].notna()
    ]

    pace = clean.groupby("Driver")["LapTime_sec"].median().reset_index()
    pace.columns = ["Driver", "RacePace_sec"]
    return pace


def has_rain(session) -> bool:
    try:
        weather = session.weather_data
        if weather is None or weather.empty:
            return False
        return weather["Rainfall"].max() > 0
    except Exception:
        return False


def get_race_list(season: int) -> list[str]:
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    return schedule["EventName"].tolist()
