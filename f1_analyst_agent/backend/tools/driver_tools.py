"""Tool 2: get_driver_race_data"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from f1_data.loader import get_session, fuzzy_race_name


def _resolve_driver(session, driver: str) -> str:
    """Map a name or surname to a 3-letter code (e.g. 'Verstappen' → 'VER')."""
    driver = driver.strip()
    if len(driver) == 3 and driver.isalpha():
        return driver.upper()
    results = session.results
    if results is not None and not results.empty:
        dl = driver.lower()
        for _, row in results.iterrows():
            full = str(row.get("FullName", "")).lower()
            last = str(row.get("LastName", "")).lower()
            if dl in full or dl in last or full.endswith(dl):
                return row["Abbreviation"]
    return driver.upper()


def get_driver_race_data(season: int, race: str, driver: str) -> dict:
    resolved = fuzzy_race_name(season, race)
    if not resolved:
        return {"error": f"Race '{race}' not found in {season} calendar."}
    try:
        session = get_session(season, resolved)
        driver_upper = _resolve_driver(session, driver)
        driver_laps = session.laps.pick_driver(driver_upper)

        if driver_laps.empty:
            return {"error": f"Driver '{driver}' not found in {resolved} {season}."}

        # pit stops
        pit_laps = driver_laps[driver_laps["PitInTime"].notna()]
        pit_stops = []
        for _, row in pit_laps.iterrows():
            pit_stops.append({
                "lap": int(row["LapNumber"]),
                "compound_in": row["Compound"],
            })

        # compounds used in order
        compounds = driver_laps.dropna(subset=["Compound"])["Compound"].unique().tolist()

        # lap time evolution (clean laps only, seconds)
        clean = driver_laps[
            driver_laps["PitInTime"].isna() &
            driver_laps["PitOutTime"].isna() &
            driver_laps["LapTime"].notna() &
            ~driver_laps["TrackStatus"].isin(["4", "5", "6"])
        ]
        lap_times = [
            {"lap": int(r["LapNumber"]), "time_sec": round(r["LapTime"].total_seconds(), 3)}
            for _, r in clean.iterrows()
        ]

        # positions
        results = session.results
        start_pos = finish_pos = None
        if results is not None and not results.empty:
            driver_result = results[results["Abbreviation"] == driver_upper]
            if not driver_result.empty:
                start_pos = int(driver_result["GridPosition"].iloc[0])
                finish_pos = int(driver_result["Position"].iloc[0]) if pd.notna(driver_result["Position"].iloc[0]) else None

        avg_clean = clean["LapTime"].dt.total_seconds().mean() if not clean.empty else None

        return {
            "driver": driver_upper,
            "race": resolved,
            "season": season,
            "start_position": start_pos,
            "finish_position": finish_pos,
            "positions_gained": (start_pos - finish_pos) if (start_pos and finish_pos) else None,
            "pit_stops": pit_stops,
            "compounds_used": compounds,
            "avg_clean_lap_sec": round(avg_clean, 3) if avg_clean else None,
            "lap_time_evolution": lap_times[:60],  # cap at 60 laps
            "total_clean_laps": len(clean),
        }
    except Exception as e:
        return {"error": str(e)}
