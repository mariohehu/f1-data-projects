"""Coordinate normalisation and race phase detection."""


def normalize_positions(positions: list[dict], track: dict) -> list[dict]:
    from circuit_loader import normalise_position
    out = []
    for pos in positions:
        x, y = normalise_position(float(pos.get("x", 0)), float(pos.get("y", 0)), track)
        out.append({
            "driver": pos["driver_number"],
            "x": x,
            "y": y,
            "date": pos.get("date", ""),
        })
    return out


def get_current_phase(race_control_messages: list[dict], current_lap: int | None = None) -> str:
    """
    Determine current race phase from race control messages.
    Returns: 'normal' | 'safety_car' | 'vsc' | 'red_flag'
    """
    if not race_control_messages:
        return "normal"

    # use lap filter only when lap is known
    if current_lap is not None:
        relevant = [m for m in race_control_messages if (m.get("lap_number") or 0) <= current_lap]
    else:
        relevant = race_control_messages

    if not relevant:
        return "normal"

    # walk backwards to find latest active state
    for msg in reversed(relevant):
        text = (msg.get("message") or "").upper()
        if "SAFETY CAR IN THIS LAP" in text or "TRACK CLEAR" in text:
            return "normal"
        if "SAFETY CAR DEPLOYED" in text:
            return "safety_car"
        if "VIRTUAL SAFETY CAR DEPLOYED" in text:
            return "vsc"
        if "RED FLAG" in text:
            return "red_flag"

    return "normal"


def latest_per_driver(positions: list[dict]) -> list[dict]:
    """Given a list of position records, keep only the most recent per driver."""
    seen: dict[int, dict] = {}
    for pos in positions:
        driver = pos["driver_number"]
        existing = seen.get(driver)
        if existing is None or pos["date"] > existing["date"]:
            seen[driver] = pos
    return list(seen.values())


def downsample(positions: list[dict], interval_ms: int = 1000) -> list[dict]:
    """Keep ~one position per driver per interval_ms, to shrink replay payloads.

    Raw OpenF1 location data is ~4Hz; 1Hz is plenty for smooth dot animation
    and cuts the payload ~4x."""
    from datetime import datetime

    def parse(d: str) -> float:
        try:
            return datetime.fromisoformat(d.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    by_driver: dict[int, list[dict]] = {}
    for p in positions:
        by_driver.setdefault(p["driver_number"], []).append(p)

    out: list[dict] = []
    for driver, recs in by_driver.items():
        recs.sort(key=lambda r: r["date"])
        last_t = None
        for r in recs:
            t = parse(r["date"])
            if last_t is None or (t - last_t) * 1000 >= interval_ms:
                out.append(r)
                last_t = t
    out.sort(key=lambda r: r["date"])
    return out
