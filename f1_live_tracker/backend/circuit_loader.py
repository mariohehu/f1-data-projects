"""
Circuit outline + coordinate transform.

Design decision: the track outline AND the car positions are both derived from
OpenF1 location data, so they share one coordinate space and cars always land
on the track. (Mixing FastF1's track shape with OpenF1's car coords risks
misalignment between two telemetry sources.)

A single aspect-ratio-preserving transform maps raw telemetry x,y into the SVG
viewport [0,VIEW_W] x [0,VIEW_H], with the Y axis flipped for SVG.
"""

VIEW_W = 1000
VIEW_H = 600
PAD = 40


def _compute_transform(x_min, x_max, y_min, y_max) -> dict:
    width = max(x_max - x_min, 1e-6)
    height = max(y_max - y_min, 1e-6)
    scale = min((VIEW_W - 2 * PAD) / width, (VIEW_H - 2 * PAD) / height)
    draw_w, draw_h = width * scale, height * scale
    off_x = (VIEW_W - draw_w) / 2
    off_y = (VIEW_H - draw_h) / 2
    return {"x_min": x_min, "y_min": y_min, "scale": scale, "off_x": off_x, "off_y": off_y}


def _apply(x: float, y: float, t: dict) -> tuple[float, float]:
    sx = t["off_x"] + (x - t["x_min"]) * t["scale"]
    sy = t["off_y"] + (y - t["y_min"]) * t["scale"]
    sy = VIEW_H - sy  # flip Y for SVG
    return round(sx, 2), round(sy, 2)


def normalise_position(x: float, y: float, track: dict) -> tuple[float, float]:
    """Map a raw car x,y into SVG coordinates using the track's transform."""
    return _apply(x, y, track["transform"])


def build_track(positions: list[dict], outline_points: int = 400) -> dict:
    """
    Build a track outline + transform from a batch of OpenF1 location records.

    positions: list of {driver_number, x, y, date}
    Returns {"path": [{x,y}...], "transform": {...}, "bounds": {...}}.
    """
    pts = [p for p in positions if p.get("x") is not None and p.get("y") is not None]
    if not pts:
        # degenerate fallback — empty track
        t = _compute_transform(0, 1, 0, 1)
        return {"path": [], "transform": t, "bounds": {}}

    xs = [float(p["x"]) for p in pts]
    ys = [float(p["y"]) for p in pts]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    transform = _compute_transform(x_min, x_max, y_min, y_max)

    # outline = the trajectory of the driver with the most samples (covers a lap)
    by_driver: dict[int, list[dict]] = {}
    for p in pts:
        by_driver.setdefault(p["driver_number"], []).append(p)
    outline_src = max(by_driver.values(), key=len)
    outline_src = sorted(outline_src, key=lambda p: p["date"])

    step = max(1, len(outline_src) // outline_points)
    path = []
    for p in outline_src[::step]:
        sx, sy = _apply(float(p["x"]), float(p["y"]), transform)
        path.append({"x": sx, "y": sy})

    return {
        "path": path,
        "transform": transform,
        "bounds": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
    }
