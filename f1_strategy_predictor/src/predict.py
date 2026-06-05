import joblib
import fastf1
import pandas as pd
import numpy as np
from pathlib import Path

from features import build_features, FEATURE_COLS

MODELS_DIR = Path(__file__).parent.parent / "models"
CACHE_DIR = Path(__file__).parent.parent / "data" / "raw"
fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_model():
    path = MODELS_DIR / "strategy_model.pkl"
    if not path.exists():
        raise FileNotFoundError("Model not found. Run train.py first.")
    return joblib.load(path)


def predict_pit_window(season: int, race: str, driver: str) -> pd.DataFrame:
    model = load_model()

    r_session = fastf1.get_session(season, race, "R")
    r_session.load(telemetry=False)

    # build features for ALL drivers — identical pipeline to training, so the
    # cross-driver features (gap behind, undercut threat, vs-leader) are consistent
    laps = r_session.laps.copy()
    laps["Season"] = season
    laps["Race"] = race
    laps["TotalLaps"] = r_session.total_laps

    feat = build_features(laps)
    driver_feat = feat[feat["Driver"] == driver].copy().sort_values("LapNumber")

    if driver_feat.empty:
        return pd.DataFrame()

    X = driver_feat[FEATURE_COLS].fillna(0)
    probs = model.predict_proba(X)[:, 1]
    driver_feat["PitProbability"] = probs

    # adaptive threshold: surface roughly the expected number of stops for the race
    n_expected = max(2, int(len(driver_feat) / 25))
    top = pd.Series(probs).nlargest(n_expected * 3)
    threshold = max(top.iloc[-1] if not top.empty else 0.3, 0.15)
    driver_feat["PredictedPit"] = (driver_feat["PitProbability"] >= threshold).astype(int)

    # NextLapPit is the ground-truth target (did they actually pit next lap)
    driver_feat["ActualNextPit"] = driver_feat["NextLapPit"]

    return driver_feat[[
        "LapNumber", "LapTime_sec", "Compound", "TyreLife", "Position",
        "StintNumber", "PitProbability", "PredictedPit", "ActualNextPit",
    ]].reset_index(drop=True)
