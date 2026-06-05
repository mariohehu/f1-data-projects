import pandas as pd
import numpy as np


def _track_status_at_lap(session, lap_number: int) -> str:
    """Get the dominant TrackStatus for a given lap number."""
    laps = session.laps
    lap_rows = laps[laps["LapNumber"] == lap_number]
    if lap_rows.empty:
        return "1"
    status = lap_rows["TrackStatus"].dropna()
    if status.empty:
        return "1"
    return status.mode().iloc[0]


def _weather_at_lap(session, lap_number: int) -> dict:
    """Get weather snapshot closest to a given lap."""
    try:
        weather = session.weather_data
        if weather is None or weather.empty:
            return {"Rainfall": 0}
        laps = session.laps
        lap_rows = laps[laps["LapNumber"] == lap_number]
        if lap_rows.empty or "Time" not in lap_rows.columns:
            return {"Rainfall": 0}
        lap_time = lap_rows["Time"].dropna()
        if lap_time.empty:
            return {"Rainfall": 0}
        idx = (weather["Time"] - lap_time.iloc[0]).abs().idxmin()
        return weather.loc[idx].to_dict()
    except Exception:
        return {"Rainfall": 0}


def classify_anomaly(lap: pd.Series, session, median_time: float) -> str:
    lap_num = int(lap["LapNumber"])

    if pd.notna(lap.get("PitInTime")):
        return "Pit in lap"
    if pd.notna(lap.get("PitOutTime")):
        return "Pit out lap"

    status = _track_status_at_lap(session, lap_num)
    if status == "4":
        return "Safety Car lap"
    if status == "5":
        return "VSC lap"
    if status == "6":
        return "Red Flag lap"
    if status == "2":
        return "Yellow Flag lap"

    weather = _weather_at_lap(session, lap_num)
    if weather.get("Rainfall", 0) > 0:
        return "Rain lap"

    if lap["LapTime_sec"] > median_time * 1.15:
        return "Possible mechanical issue"

    return "Unknown anomaly"


def label_anomalies(laps: pd.DataFrame, session) -> pd.DataFrame:
    df = laps.copy()
    median_time = df["LapTime_sec"].median()

    # vectorize the common cases first
    df["anomaly_label"] = "Normal"

    anomaly_mask = df["is_anomaly"]
    if not anomaly_mask.any():
        return df

    pit_in = anomaly_mask & df["PitInTime"].notna()
    pit_out = anomaly_mask & df["PitOutTime"].notna()
    df.loc[pit_in, "anomaly_label"] = "Pit in lap"
    df.loc[pit_out, "anomaly_label"] = "Pit out lap"

    # only call classify_anomaly for remaining anomalies (non-pit)
    remaining = anomaly_mask & ~pit_in & ~pit_out
    for idx in df.index[remaining]:
        row = df.loc[idx]
        df.at[idx, "anomaly_label"] = classify_anomaly(row, session, median_time)

    # track-wide detection: if >50% of drivers have anomaly on same lap
    lap_counts = df[anomaly_mask].groupby("LapNumber")["Driver"].nunique()
    total_drivers = df["Driver"].nunique()
    shared_laps = lap_counts[lap_counts / max(total_drivers, 1) > 0.5].index
    for lap_num in shared_laps:
        mask = (df["LapNumber"] == lap_num) & df["anomaly_label"].isin(
            ["Possible mechanical issue", "Unknown anomaly"])
        df.loc[mask, "anomaly_label"] = "Track-wide incident"

    return df
