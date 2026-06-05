import fastf1
import pandas as pd
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))

COMPOUND_MAP = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4}


def load_session(season: int, race: str):
    session = fastf1.get_session(season, race, "R")
    session.load()
    return session


def get_laps(session) -> pd.DataFrame:
    laps = session.laps.copy()
    laps["LapTime_sec"] = laps["LapTime"].dt.total_seconds()
    laps["Compound_encoded"] = laps["Compound"].map(COMPOUND_MAP).fillna(1)
    laps["TyreLife"] = laps["TyreLife"].fillna(1)
    return laps


def get_race_list(season: int) -> list[str]:
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    return schedule["EventName"].tolist()


def get_driver_list(season: int, race: str) -> list[str]:
    session = fastf1.get_session(season, race, "R")
    session.load(telemetry=False)
    return sorted(session.laps["Driver"].unique().tolist())
