"""
F1 Live Car Tracker — FastAPI backend.
Run: uvicorn main:app --reload --port 8001

Track outline and car positions are both derived from OpenF1 location data,
so they share one coordinate space (see circuit_loader.build_track).
"""
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.disable(logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import openf1_client as openf1
from circuit_loader import build_track, normalise_position
from data_processor import get_current_phase, latest_per_driver, downsample

app = FastAPI(title="F1 Live Car Tracker")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _driver_map(drivers_raw: list[dict]) -> dict:
    return {
        d["driver_number"]: {
            "acronym": d.get("name_acronym", "???"),
            "team_colour": "#" + str(d.get("team_colour")).lstrip("#") if d.get("team_colour") else "#AAAAAA",
        }
        for d in drivers_raw
    }


# ── REST endpoints ──────────────────────────────────────────────────────────

@app.get("/sessions")
async def sessions(year: int | None = None, session_name: str | None = None):
    try:
        data = await openf1.get_sessions(year=year, session_name=session_name)
        return [
            {
                "session_key": s.get("session_key"),
                "session_name": s.get("session_name", ""),
                "year": s.get("year"),
                "country_name": s.get("country_name", ""),
                "circuit_short_name": s.get("circuit_short_name", ""),
                "date_start": s.get("date_start", ""),
            }
            for s in data
            if s.get("session_key") and s.get("date_start")
        ]
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/drivers/{session_key}")
async def drivers(session_key: int):
    try:
        data = await openf1.get_drivers(session_key)
        return _driver_map(data)
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/replay/{session_key}")
async def replay_data(session_key: int, minutes: int = 8):
    """
    Bulk-load a time window of a historical session for replay.
    Returns a normalised track outline + downsampled, normalised car positions.
    """
    try:
        session = await openf1.get_session_by_key(session_key)
        if not session:
            raise HTTPException(404, "Session not found")

        start = datetime.fromisoformat(session["date_start"].replace("Z", "+00:00"))
        end = start + timedelta(minutes=minutes)

        raw = await openf1.get_positions_window(session_key, _iso(start), _iso(end))
        if not raw:
            raise HTTPException(404, "No position data for this session window")

        positions = downsample(raw, interval_ms=1000)
        track = build_track(positions)

        norm = []
        for p in positions:
            sx, sy = normalise_position(float(p["x"]), float(p["y"]), track)
            norm.append({"driver": p["driver_number"], "x": sx, "y": sy, "date": p["date"]})

        drivers_raw = await openf1.get_drivers(session_key)
        race_ctrl = await openf1.get_race_control(session_key)

        return {
            "track": track["path"],
            "positions": norm,
            "drivers": _driver_map(drivers_raw),
            "race_control": race_ctrl,
            "window_minutes": minutes,
            "point_count": len(norm),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ── WebSocket live tracking ─────────────────────────────────────────────────

@app.websocket("/ws/{session_key}")
async def live_track(websocket: WebSocket, session_key: int):
    await websocket.accept()

    # Build track from whatever data exists so far (needs ~1 lap of coverage)
    try:
        seed = await openf1.get_positions(session_key)
        if not seed:
            await websocket.send_json({"type": "error", "message": "No position data yet for this session."})
            await websocket.close()
            return
        track = build_track(downsample(seed, interval_ms=1000))
    except Exception as e:
        await websocket.send_json({"type": "error", "message": f"Track build failed: {e}"})
        await websocket.close()
        return

    try:
        drivers_raw = await openf1.get_drivers(session_key)
        driver_map = _driver_map(drivers_raw)
    except Exception:
        driver_map = {}

    await websocket.send_json({"type": "init", "track": track["path"], "drivers": driver_map})

    last_timestamp: str | None = max((p["date"] for p in seed), default=None)
    race_ctrl: list[dict] = []

    try:
        while True:
            positions = await openf1.get_positions(session_key, after=last_timestamp)

            if positions:
                last_timestamp = max(p["date"] for p in positions)
                latest = latest_per_driver(positions)

                normalised = []
                for p in latest:
                    sx, sy = normalise_position(float(p["x"]), float(p["y"]), track)
                    info = driver_map.get(p["driver_number"], {})
                    normalised.append({
                        "driver": p["driver_number"],
                        "x": sx, "y": sy,
                        "acronym": info.get("acronym", "???"),
                        "color": info.get("team_colour", "#AAAAAA"),
                        "date": p["date"],
                    })

                try:
                    race_ctrl = await openf1.get_race_control(session_key)
                except Exception:
                    pass

                await websocket.send_json({
                    "type": "positions",
                    "data": normalised,
                    "phase": get_current_phase(race_ctrl),
                    "timestamp": last_timestamp,
                })

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


@app.get("/health")
async def health():
    return {"status": "ok"}
