# F1 Race Strategy Predictor

Predicts the **pit-stop window** for a driver during a race, lap by lap, using an XGBoost classifier trained on historical FastF1 data. Ships with a Streamlit app that overlays predicted vs. actual pit laps.

![Python](https://img.shields.io/badge/python-3.14-blue) ![XGBoost](https://img.shields.io/badge/model-XGBoost-green) ![Streamlit](https://img.shields.io/badge/ui-Streamlit-red)

---

## What it does

For each racing lap, the model outputs a **pit probability** — how likely the driver is to pit on the *next* lap — based on tyre state, race context, and position dynamics. The Streamlit UI lets you pick a season/race/driver and shows the predicted pit window against where the driver actually pitted.

## Quickstart

```bash
pip install -r requirements.txt

# 1. Train the model (downloads 2021-2023 via FastF1, ~10-15 min first run; cached after)
python src/train.py

# 2. Launch the app
streamlit run app.py
```

> First FastF1 load per race is slow (API + cache build). Subsequent loads are instant.

## Architecture

```
src/
├── data_loader.py    # FastF1 session loading (rate-limited to respect API)
├── features.py       # 15-feature engineering + target
├── train.py          # XGBoost train w/ early stopping + clean splits
└── predict.py        # inference — reuses build_features for train/predict parity
app.py                # Streamlit UI w/ Plotly chart
models/strategy_model.pkl
```

## Features (15)

| Group | Features |
|-------|----------|
| **Tyre** | TyreLife, TyreDegradation, Compound, StintNumber, CompoundsUsedSoFar |
| **Position** | Position, GapToAhead, GapToBehind, UndercutThreat |
| **Race context** | LapsRemaining, RacePhasePct, LapTimeRolling3, LapTimeVsLeader |
| **Track/conditions** | CircuitType (street/power/tyre-killer/balanced), IsSC |

## Results

Trained on 2021-2022, validated on a held-out 20% of races, tested on **all of 2023**.

| Metric | Value |
|--------|-------|
| **Test ROC-AUC (2023)** | **0.766** |
| **Validation ROC-AUC** (in-distribution) | **0.805** |
| Pit recall | 53% |
| Pit precision | 11% |

### What the model actually learned

Feature importance was revealing:

```
CompoundsUsedSoFar   0.33   ← dominant
TyreLife             0.10
StintNumber          0.07
LapsRemaining        0.06
...
UndercutThreat       0.016  ← negligible
IsSC                 0.016  ← negligible
```

The strongest signal is **structural**: F1's mandatory two-compound rule means a driver who has used only one compound *must* pit eventually. Tyre age and stint number do the rest. The "racing intelligence" features (undercut threat, gap-to-behind) contributed little — see limitations.

## Known limitations (honest)

- **Crude gap estimate.** Gaps are derived from cumulative race time, not true track position. This is why the undercut/gap features underperform — real undercut dynamics need telemetry-based positional gaps that FastF1 doesn't expose cheaply.
- **Distribution shift.** Validation AUC (0.805) > test AUC (0.766) because 2023 (Red Bull domination) had different strategy patterns than 2021-22. Realistic ceiling for this approach: ~0.80-0.82 test.
- **Low precision is inherent.** With ~3.4% positive rate, even a good model floods false positives. The app uses an adaptive threshold to surface the most-likely pit laps rather than a fixed cutoff.
- **Reactive stops aren't predictable.** Many pits *react* to Safety Cars or rivals — a 0-second prediction window that no pre-lap model can capture.

## Possible improvements

- Reframe as **"laps until next pit"** regression (more useful, more honest output)
- Telemetry-based **true track-position gaps** (would make undercut features work)
- **Per-track models** for circuits with distinct strategy archetypes

## Data source

[FastF1](https://github.com/theOehrly/Fast-F1) — official F1 timing data via the Ergast/F1 live timing API.
