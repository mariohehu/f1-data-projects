# F1 Live Car Tracker

Real-time visualisation of F1 car positions on a circuit map — coloured dots with team colours and driver acronyms moving around the track. Supports **replay** of historical races and **live** tracking during a race weekend.

![Python](https://img.shields.io/badge/python-3.14-blue) ![FastAPI](https://img.shields.io/badge/backend-FastAPI%20%2B%20WebSocket-009688) ![Next.js](https://img.shields.io/badge/frontend-Next.js%2014-black) ![OpenF1](https://img.shields.io/badge/data-OpenF1-orange)

---

## What it does

Renders 20 cars as dots on an SVG circuit map, animated from real F1 position telemetry. A timing tower lists the running order; race-phase overlays show Safety Car / VSC / Red Flag periods. Replay mode lets you scrub through a historical race with play/pause and speed controls.

## Quickstart

**Backend** (port 8001):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8001
```

**Frontend** (port 3002):
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3002**, pick a season + race in **Replay** mode, and hit **Load race**.

No API key needed — [OpenF1](https://openf1.org) is free and unauthenticated.

## Architecture

```
backend/
├── main.py            # FastAPI: /sessions, /replay, /ws (WebSocket), /health
├── openf1_client.py   # OpenF1 REST client (sessions, drivers, location, race control)
├── circuit_loader.py  # build_track() + coordinate transform (OpenF1-derived)
└── data_processor.py  # downsampling, race-phase detection, latest-per-driver
frontend/
├── app/page.tsx       # tracker page: mode toggle, replay controls
├── components/        # TrackSVG, CarDot, TimingTower
└── hooks/             # useWebSocket (live), useReplay (historical)
```

## Key design decision: one coordinate source

The original idea was to draw the track from FastF1 telemetry and overlay car
positions from OpenF1 — but those are **two different telemetry sources** that
don't share a coordinate origin/scale, so cars can drift off the track.

Instead, **both the track outline and the car positions are derived from OpenF1
location data**, through a single aspect-ratio-preserving transform
(`circuit_loader.build_track`). The track outline is the trajectory of the
most-sampled driver in the window; the same transform maps every car. Result:
**100% of car positions land within the track viewport** (verified on 2023 Monza:
8,420 positions, all in-bounds).

## How replay works

1. Look up the session's start time from OpenF1
2. Fetch all-driver `location` data for an 8-minute window
3. **Downsample** ~4 Hz → ~1 Hz (cuts payload ~4×, still smooth)
4. Build the track + transform from those points
5. Normalise every position into SVG space and return track + positions together
6. Frontend animates with play/pause, 1×–10× speed, and a scrubber

## Race phase detection

Parses OpenF1 `race_control` messages (walking backwards to the latest active
state) to classify each moment as `normal` / `safety_car` / `vsc` / `red_flag`,
then tints the map accordingly.

## Known limitations (honest)

- **OpenF1 data starts in 2023.** Earlier seasons aren't available, so replay is limited to 2023+.
- **Replay loads an 8-minute window, not the full race.** A full race is millions of location points; an 8-minute window keeps the payload (~8k points) responsive. Adjustable via `?minutes=` on `/replay`.
- **Track outline can show pit-lane excursions.** Since the outline is one driver's real trajectory, if that driver pitted in the window the outline includes the pit lane. Cosmetic only — cars still render correctly.
- **Live mode only works during a race weekend** (OpenF1 streams live data only then). Replay is the always-available path and the one to demo.

## Data source

[OpenF1](https://openf1.org) — free, unauthenticated F1 timing API: car locations (~4 Hz), drivers, sessions, and race control messages.
