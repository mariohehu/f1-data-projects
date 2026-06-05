import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest


def detect_anomalies(laps: pd.DataFrame, contamination: float = 0.05,
                     zscore_thresh: float = 2.5) -> pd.DataFrame:
    """
    Run Isolation Forest (primary) + Z-score (secondary) on cleaned laps.
    Pit in/out laps are excluded from the model fit to avoid contamination,
    then labelled separately. High confidence = both methods agree.
    """
    df = laps.copy()

    required = ["LapTime_sec", "TyreLife", "Compound_encoded"]
    df = df.dropna(subset=required)

    if df.empty:
        df["is_anomaly"] = False
        df["anomaly_score"] = 0.0
        df["z_score"] = 0.0
        return df

    is_pit = df["PitInTime"].notna() | df["PitOutTime"].notna()
    clean = df[~is_pit]
    pit_rows = df[is_pit].copy()

    if clean.empty:
        df["is_anomaly"] = is_pit
        df["anomaly_score"] = 0.0
        df["z_score"] = 0.0
        return df

    X_clean = clean[required].values

    iso = IsolationForest(contamination=contamination, random_state=42)
    clean = clean.copy()
    clean["iso_pred"] = iso.fit_predict(X_clean)
    clean["anomaly_score"] = -iso.score_samples(X_clean)

    z = stats.zscore(clean["LapTime_sec"])
    clean["z_score"] = z

    clean["is_anomaly"] = (clean["iso_pred"] == -1) & (np.abs(z) > zscore_thresh)

    pit_rows["iso_pred"] = 0
    pit_rows["anomaly_score"] = 0.0
    pit_rows["z_score"] = 0.0
    pit_rows["is_anomaly"] = True

    result = pd.concat([clean, pit_rows]).sort_index()
    return result
