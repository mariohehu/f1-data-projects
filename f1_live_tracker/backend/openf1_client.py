"""OpenF1 REST API client."""
import httpx
from typing import Any

BASE = "https://api.openf1.org/v1"


async def get_sessions(year: int | None = None, session_name: str | None = None) -> list[dict]:
    params: dict[str, Any] = {}
    if year:
        params["year"] = year
    if session_name:
        params["session_name"] = session_name
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/sessions", params=params)
        r.raise_for_status()
        return r.json()


async def get_latest_session() -> dict | None:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/sessions", params={"session_key": "latest"})
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None


async def get_drivers(session_key: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/drivers", params={"session_key": session_key})
        r.raise_for_status()
        return r.json()


async def get_positions(session_key: int, after: str | None = None) -> list[dict]:
    """Fetch car position data, optionally after a timestamp."""
    params: dict[str, Any] = {"session_key": session_key}
    if after:
        params["date>"] = after
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{BASE}/location", params=params)
        r.raise_for_status()
        return r.json()


async def get_positions_window(session_key: int, start_iso: str, end_iso: str) -> list[dict]:
    """Fetch all-driver position data within a [start, end] time window."""
    params: dict[str, Any] = {
        "session_key": session_key,
        "date>": start_iso,
        "date<": end_iso,
    }
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(f"{BASE}/location", params=params)
        r.raise_for_status()
        return r.json()


async def get_session_by_key(session_key: int) -> dict | None:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/sessions", params={"session_key": session_key})
        r.raise_for_status()
        data = r.json()
        return data[0] if data else None


async def get_race_control(session_key: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/race_control", params={"session_key": session_key})
        r.raise_for_status()
        return r.json()


async def get_intervals(session_key: int) -> list[dict]:
    """Get gap-to-leader intervals (available for recent sessions)."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE}/intervals", params={"session_key": session_key})
        r.raise_for_status()
        return r.json()
