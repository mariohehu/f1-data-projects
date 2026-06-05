# F1 Lap Time Anomaly Detection

Automatically detects and explains "unusual" laps in a race — Safety Cars, VSC, rain, pit laps, and possible mechanical issues — with **no manual labelling**. Interactive Plotly visualisation colour-codes each lap by anomaly type.

![Python](https://img.shields.io/badge/python-3.14-blue) ![sklearn](https://img.shields.io/badge/model-IsolationForest-orange) ![Streamlit](https://img.shields.io/badge/ui-Streamlit-red)

---

## What it does

Runs unsupervised anomaly detection on a driver's lap times, then **auto-labels** each anomaly by cross-referencing track status, weather, and pit data. Distinguishes track-wide events (Safety Car affecting everyone) from driver-specific ones (a mechanical issue).

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

No training step — detection is unsupervised and runs on demand.

## How it works

**Detection (two methods, must agree):**
- **Isolation Forest** (primary) — multivariate, considers `[LapTime, TyreLife, Compound]` so it doesn't flag normal tyre degradation as anomalous
- **Z-score** (secondary) — lap-time outliers per driver
- High-confidence anomaly = *both* methods agree (logical AND)

**Auto-labelling** (priority order):
1. Pit in / pit out lap (from pit timestamps)
2. Safety Car / VSC / Red Flag / Yellow (from `TrackStatus`)
3. Rain lap (from weather data)
4. Possible mechanical issue (unexplained slow lap)
5. **Track-wide incident** — if >50% of drivers show an anomaly on the same lap, it's reclassified from "mechanical" to track-wide

## Architecture

```
src/
├── loader.py       # FastF1 session loading + preprocessing
├── detector.py     # Isolation Forest + Z-score (pit laps excluded from fit)
├── labeler.py      # context-based auto-labelling
└── visualizer.py   # Plotly scatter (single + 2-driver comparison)
app.py              # Streamlit UI w/ sensitivity sliders
```

## Key design decisions

- **Pit laps are excluded from the model fit**, then labelled separately — otherwise their extreme times dominate the Isolation Forest and mask real anomalies.
- **Detection runs across all drivers at once** so the track-wide >50% check actually works (it can't on a single driver).
- Two sliders expose **Isolation Forest contamination** and **Z-score threshold** for live sensitivity tuning.

## Features

- Single-driver anomaly scatter, colour-coded by type
- 2-driver side-by-side comparison (spot track-wide vs. individual events)
- Anomaly breakdown table (type → count → lap numbers)
- Adjustable detection sensitivity

## Data source

[FastF1](https://github.com/theOehrly/Fast-F1) — lap times, track status, and weather data.
