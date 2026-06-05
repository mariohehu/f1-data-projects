import sys
import time
import fastf1
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CACHE_DIR = Path(__file__).parent.parent / "data" / "raw"
fastf1.Cache.enable_cache(str(CACHE_DIR))

API_DELAY = 8  # seconds between uncached loads to stay under 500 calls/h


def load_season(season: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    race_names = schedule["EventName"].tolist()

    all_laps = []
    for race in race_names:
        t0 = time.time()
        try:
            session = fastf1.get_session(season, race, "R")
            session.load(telemetry=False)
            laps = session.laps.copy()
            laps["Season"] = season
            laps["Race"] = race
            laps["TotalLaps"] = session.total_laps
            all_laps.append(laps)
            print(f"  Loaded {season} {race}")
        except Exception as e:
            print(f"  Skipped {season} {race}: {e}")
        # only throttle when we actually hit the API (cached loads are ~instant)
        if time.time() - t0 > 3:
            time.sleep(API_DELAY)

    if not all_laps:
        return pd.DataFrame()
    return pd.concat(all_laps, ignore_index=True)


def load_seasons(seasons: list[int]) -> pd.DataFrame:
    all_data = []
    for season in seasons:
        print(f"Loading season {season}...")
        df = load_season(season)
        if not df.empty:
            all_data.append(df)
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def get_race_list(season: int) -> list[str]:
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    return schedule["EventName"].tolist()


def get_driver_list(season: int, race: str) -> list[str]:
    session = fastf1.get_session(season, race, "R")
    session.load(telemetry=False)
    return sorted(session.laps["Driver"].unique().tolist())
