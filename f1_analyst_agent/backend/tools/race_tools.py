"""Tools 1 & 4: get_race_summary, get_qualifying_context"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from f1_data.loader import get_session, fuzzy_race_name


def get_race_summary(season: int, race: str) -> dict:
    resolved = fuzzy_race_name(season, race)
    if not resolved:
        return {"error": f"Race '{race}' not found in {season} calendar."}
    try:
        session = get_session(season, resolved)
        laps = session.laps

        results = session.results
        podium = []
        if results is not None and not results.empty:
            top3 = results.sort_values("Position").head(3)
            for _, r in top3.iterrows():
                pos = int(r["Position"])
                t = r.get("Time")
                if pos == 1:
                    time_str = "winner"
                elif pd.notna(t):
                    secs = t.total_seconds() if hasattr(t, "total_seconds") else None
                    time_str = f"+{secs:.3f}s" if secs is not None else "—"
                else:
                    time_str = "—"
                podium.append({
                    "position": pos,
                    "driver": r["Abbreviation"],
                    "team": r["TeamName"],
                    "gap": time_str,
                })

        # count safety cars from track status
        sc_laps = laps[laps["TrackStatus"] == "4"]["LapNumber"].unique().tolist()
        vsc_laps = laps[laps["TrackStatus"] == "5"]["LapNumber"].unique().tolist()

        # DNFs
        dnf_drivers = []
        if results is not None and not results.empty:
            dnf_rows = results[~results["Status"].str.startswith("+") &
                               (results["Status"] != "Finished")]
            dnf_drivers = dnf_rows["Abbreviation"].tolist()

        # fastest lap
        fastest = laps.pick_fastest()
        fastest_info = {
            "driver": fastest["Driver"],
            "lap": int(fastest["LapNumber"]),
            "time": str(fastest["LapTime"]),
        } if fastest is not None and not fastest.empty else None

        # weather summary
        weather = {}
        try:
            w = session.weather_data
            if w is not None and not w.empty:
                weather = {
                    "air_temp_avg": round(float(w["AirTemp"].mean()), 1),
                    "track_temp_avg": round(float(w["TrackTemp"].mean()), 1),
                    "rainfall": bool(w["Rainfall"].max() > 0),
                }
        except Exception:
            pass

        return {
            "race": resolved,
            "season": season,
            "total_laps": int(session.total_laps),
            "podium": podium,
            "safety_car_laps": sc_laps[:5],
            "vsc_laps": vsc_laps[:5],
            "safety_car_count": len(sc_laps),
            "dnf_drivers": dnf_drivers,
            "fastest_lap": fastest_info,
            "weather": weather,
        }
    except Exception as e:
        return {"error": str(e)}


def get_qualifying_context(season: int, race: str) -> dict:
    resolved = fuzzy_race_name(season, race)
    if not resolved:
        return {"error": f"Race '{race}' not found in {season} calendar."}
    try:
        session = get_session(season, resolved, "Q")
        laps = session.laps.pick_quicklaps()

        best = laps.groupby("Driver")["LapTime"].min().reset_index()
        best["LapTime_sec"] = best["LapTime"].dt.total_seconds()
        best = best.sort_values("LapTime_sec").reset_index(drop=True)

        pole_time = best["LapTime_sec"].iloc[0]
        grid = []
        for i, row in best.iterrows():
            gap = row["LapTime_sec"] - pole_time
            grid.append({
                "position": i + 1,
                "driver": row["Driver"],
                "lap_time": str(row["LapTime"]),
                "gap_to_pole": f"+{gap:.3f}s" if gap > 0 else "pole",
            })

        return {
            "race": resolved,
            "season": season,
            "pole_driver": grid[0]["driver"] if grid else None,
            "pole_time": grid[0]["lap_time"] if grid else None,
            "grid": grid[:20],
        }
    except Exception as e:
        return {"error": str(e)}
