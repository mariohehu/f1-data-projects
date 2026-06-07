"""Tools 3 & 5: get_strategy_comparison, get_championship_context"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import pandas as pd
from f1_data.loader import get_session, fuzzy_race_name


def get_strategy_comparison(season: int, race: str) -> dict:
    resolved = fuzzy_race_name(season, race)
    if not resolved:
        return {"error": f"Race '{race}' not found in {season} calendar."}
    try:
        session = get_session(season, resolved)
        laps = session.laps

        strategies = []
        for driver in laps["Driver"].unique():
            dlaps = laps.pick_driver(driver)

            # build stint list
            stints = []
            current_compound = None
            stint_start = None
            for _, row in dlaps.sort_values("LapNumber").iterrows():
                if row["Compound"] != current_compound:
                    if current_compound is not None:
                        stints.append({
                            "compound": current_compound,
                            "start_lap": int(stint_start),
                            "end_lap": int(row["LapNumber"]) - 1,
                            "length": int(row["LapNumber"]) - int(stint_start),
                        })
                    current_compound = row["Compound"]
                    stint_start = row["LapNumber"]
            if current_compound and stint_start:
                stints.append({
                    "compound": current_compound,
                    "start_lap": int(stint_start),
                    "end_lap": int(dlaps["LapNumber"].max()),
                    "length": int(dlaps["LapNumber"].max()) - int(stint_start) + 1,
                })

            # pit laps
            pit_laps = dlaps[dlaps["PitInTime"].notna()]["LapNumber"].tolist()

            # finish position
            results = session.results
            finish_pos = None
            if results is not None and not results.empty:
                dr = results[results["Abbreviation"] == driver]
                if not dr.empty:
                    finish_pos = int(dr["Position"].iloc[0]) if pd.notna(dr["Position"].iloc[0]) else None

            strategies.append({
                "driver": driver,
                "finish_position": finish_pos,
                "pit_laps": [int(l) for l in pit_laps],
                "stops": len(pit_laps),
                "stints": stints,
            })

        # sort by finish position; cap to top 10 to keep LLM context lean
        strategies.sort(key=lambda x: x["finish_position"] or 99)

        return {
            "race": resolved,
            "season": season,
            "strategies": strategies[:10],
        }
    except Exception as e:
        return {"error": str(e)}


def get_championship_context(season: int, race: str) -> dict:
    """Fetch driver standings BEFORE this race via Jolpica API."""
    resolved = fuzzy_race_name(season, race)
    if not resolved:
        return {"error": f"Race '{race}' not found in {season} calendar."}

    import fastf1
    try:
        schedule = fastf1.get_event_schedule(season, include_testing=False)
        race_rounds = {row["EventName"]: int(row["RoundNumber"]) for _, row in schedule.iterrows()}
        this_round = race_rounds.get(resolved)
        if not this_round:
            return {"error": "Could not determine round number."}

        # standings after previous round
        prev_round = this_round - 1
        if prev_round < 1:
            return {"race": resolved, "season": season, "round": this_round,
                    "note": "First race of the season — no prior standings.", "standings": []}

        url = f"https://api.jolpi.ca/ergast/f1/{season}/{prev_round}/driverStandings.json"
        response = httpx.get(url, timeout=10)
        data = response.json()
        lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not lists:
            return {"error": "No standings data returned."}

        raw = lists[0].get("DriverStandings", [])
        standings = [
            {
                "position": int(s["position"]),
                "driver": f"{s['Driver']['givenName']} {s['Driver']['familyName']}",
                "code": s["Driver"].get("code", ""),
                "points": float(s["points"]),
                "wins": int(s["wins"]),
                "team": s["Constructors"][0]["name"] if s.get("Constructors") else "",
            }
            for s in raw[:10]
        ]

        leader_pts = standings[0]["points"] if standings else 0
        for s in standings:
            s["gap_to_leader"] = round(leader_pts - s["points"], 1)

        return {
            "race": resolved,
            "season": season,
            "round": this_round,
            "standings_after_round": prev_round,
            "standings": standings,
        }
    except Exception as e:
        return {"error": str(e)}
