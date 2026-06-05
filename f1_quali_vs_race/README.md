# F1 Qualifying vs Race Pace

Discovers which teams **"hide" pace in qualifying** and reveal it in the race — or the opposite. Computes a per-driver, per-race `hidden_pace` metric across a full season and visualises it three ways.

![Python](https://img.shields.io/badge/python-3.14-blue) ![seaborn](https://img.shields.io/badge/viz-seaborn-teal) ![CLI](https://img.shields.io/badge/interface-CLI-lightgrey)

---

## The idea

```
quali_gap_pct = (driver_quali - fastest_quali) / fastest_quali × 100
race_gap_pct  = (driver_race_pace - fastest_race) / fastest_race × 100

hidden_pace = quali_gap_pct − race_gap_pct
```

- **Positive hidden_pace** → the car is *better in the race* than qualifying suggests (hidden race pace)
- **Negative** → better in qualifying than in the race (e.g. tyre-management weakness)

Gaps are expressed as **% of the fastest time**, so circuits with different lap lengths (Monza ~1:20 vs. Monaco ~1:10) are directly comparable.

## Quickstart

```bash
pip install -r requirements.txt

python main.py --season 2023                 # full season
python main.py --season 2022 2023            # multiple seasons
python main.py --season 2023 --race Monaco   # single race
```

Outputs land in `output/charts/` (PNGs) and `output/hidden_pace_<season>.csv`.

## What it produces

1. **Scatter** (per race) — qualifying gap vs. race gap, with a diagonal "no hiding" baseline. Points below the line = hidden race pace.
2. **Bar chart** (per season) — average hidden pace by team.
3. **Heatmap** (per season) — hidden pace by team × race, diverging colour scale.

## Methodology

- **Race pace = median** of clean laps 5-15 (more robust than the minimum)
- **Clean laps only** — excludes SC/VSC/red-flag laps and pit in/out laps
- **Rain races skipped** automatically (pace incomparable in mixed conditions)
- **Qualifying = best lap** per driver from `pick_quicklaps()`

## Architecture

```
src/
├── loader.py          # FastF1 session loading, clean-lap filtering
├── pace_analysis.py   # hidden_pace calc + team aggregation
├── team_mapping.py    # driver→team per season (2022-2024)
└── visualizer.py      # seaborn scatter / bar / heatmap (dark theme)
main.py                # CLI entry point
```

## Known limitations

- **Fuel-load effect** isn't corrected — early-race pace carries more fuel weight, which the median over laps 5-15 only partially smooths.
- **Driver→team mapping is hard-coded** per season (2022-2024). New seasons need a new entry in `team_mapping.py`.
- **Lap window 5-15** assumes a representative clean stint exists; some street circuits with early Safety Cars may yield few clean laps.

## Data source

[FastF1](https://github.com/theOehrly/Fast-F1) — qualifying and race lap times, track status, weather.
