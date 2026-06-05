import sys
import logging
import joblib
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# suppress fastf1 INFO/WARNING noise — only show our own print() progress
logging.disable(logging.WARNING)

from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score

from data_loader import load_seasons
from features import build_features, FEATURE_COLS, TARGET_COL

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

TRAIN_SEASONS = [2021, 2022]
TEST_SEASONS = [2023]


def train():
    print("Loading training data...")
    train_raw = load_seasons(TRAIN_SEASONS)
    print("Loading test data...")
    test_raw = load_seasons(TEST_SEASONS)

    print("Building features...")
    train_df = build_features(train_raw)
    test_df = build_features(test_raw)

    # split training data into train/val by RACE (no leakage within a race)
    # use last ~20% of races as validation set for early stopping
    all_races = train_df[["Season", "Race"]].drop_duplicates().reset_index(drop=True)
    n_val = max(1, int(len(all_races) * 0.20))
    val_races = all_races.tail(n_val)
    val_race_keys = set(zip(val_races["Season"], val_races["Race"]))

    train_keys = list(zip(train_df["Season"], train_df["Race"]))
    is_val = pd.Series([k in val_race_keys for k in train_keys], index=train_df.index)

    X_tr = train_df.loc[~is_val, FEATURE_COLS]
    y_tr = train_df.loc[~is_val, TARGET_COL]
    X_val = train_df.loc[is_val, FEATURE_COLS]
    y_val = train_df.loc[is_val, TARGET_COL]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df[TARGET_COL]

    print(f"Train size: {len(X_tr)}, pit laps: {y_tr.sum()} ({y_tr.mean():.2%})")
    print(f"Val size:   {len(X_val)}, pit laps: {y_val.sum()} ({y_val.mean():.2%})")
    print(f"Test size:  {len(X_test)},  pit laps: {y_test.sum()} ({y_test.mean():.2%})")

    neg_pos_ratio = int((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))

    model = XGBClassifier(
        n_estimators=600,
        max_depth=6,
        learning_rate=0.03,
        scale_pos_weight=neg_pos_ratio,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.5,
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30,
    )

    model.fit(
        X_tr, y_tr,
        eval_set=[(X_val, y_val)],
        verbose=25,
    )

    print(f"\nBest iteration: {model.best_iteration} (val AUC: {model.best_score:.4f})")

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n--- Test Set Results (held out — 2023) ---")
    print(classification_report(y_test, y_pred, target_names=["No Pit", "Pit"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

    # feature importance — which signals actually drive pit predictions
    importances = sorted(
        zip(FEATURE_COLS, model.feature_importances_),
        key=lambda x: x[1], reverse=True,
    )
    print("\n--- Feature Importance ---")
    for name, imp in importances:
        print(f"  {name:20s} {imp:.4f}")

    model_path = MODELS_DIR / "strategy_model.pkl"
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")


if __name__ == "__main__":
    train()
