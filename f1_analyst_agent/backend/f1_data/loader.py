"""
FastF1 wrapper — shared cache across all tools.
All functions return plain dicts (JSON-serialisable).
"""
import sys
import logging
import time
from pathlib import Path

logging.disable(logging.WARNING)

import fastf1
import pandas as pd

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "f1_strategy_predictor" / "data" / "raw"
fastf1.Cache.enable_cache(str(CACHE_DIR))

_session_cache: dict = {}


def get_session(season: int, race: str, session_type: str = "R"):
    key = (season, race, session_type)
    if key not in _session_cache:
        s = fastf1.get_session(season, race, session_type)
        s.load(telemetry=False)
        _session_cache[key] = s
    return _session_cache[key]


def get_race_list(season: int) -> list[str]:
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    return schedule["EventName"].tolist()


# circuit nickname / venue → keyword that appears in the official EventName
CIRCUIT_NICKNAMES = {
    "monza": "Italian",
    "silverstone": "British",
    "spa": "Belgian",
    "francorchamps": "Belgian",
    "interlagos": "São Paulo",
    "sao paulo": "São Paulo",
    "suzuka": "Japanese",
    "zandvoort": "Dutch",
    "baku": "Azerbaijan",
    "jeddah": "Saudi",
    "yas marina": "Abu Dhabi",
    "cota": "United States",
    "austin": "United States",
    "imola": "Emilia",
    "catalunya": "Spanish",
    "barcelona": "Spanish",
    "hungaroring": "Hungarian",
    "red bull ring": "Austrian",
    "spielberg": "Austrian",
    "marina bay": "Singapore",
    "albert park": "Australian",
    "melbourne": "Australian",
    "montreal": "Canadian",
    "mexico city": "Mexico",
    "vegas": "Las Vegas",
    "losail": "Qatar",
    "lusail": "Qatar",
    "paul ricard": "French",
    "istanbul": "Turkish",
    "portimao": "Portuguese",
    "sakhir": "Bahrain",
}


def fuzzy_race_name(season: int, query: str) -> str | None:
    """Return the best matching EventName for a fuzzy query.

    Handles official names ('Italian Grand Prix'), keywords ('Italian'),
    and circuit nicknames ('Monza' → 'Italian Grand Prix').
    """
    races = get_race_list(season)
    q = query.lower().strip()
    padded = f" {q} "  # for whole-word checks

    # 1. nickname match as a whole word FIRST
    #    (so 'Spa' → Belgian, not 'Spanish' via loose substring)
    for nick, keyword in CIRCUIT_NICKNAMES.items():
        if q == nick or f" {nick} " in padded:
            for r in races:
                if keyword.lower() in r.lower():
                    return r

    # 2. direct substring match (handles 'Italian', 'Monaco', full names)
    for r in races:
        if q in r.lower():
            return r

    # 3. nickname as a loose substring (catches 'at monza' style phrasing)
    for nick, keyword in CIRCUIT_NICKNAMES.items():
        if nick in q:
            for r in races:
                if keyword.lower() in r.lower():
                    return r

    # 4. word-level fallback
    for word in q.split():
        if len(word) >= 4:
            for r in races:
                if word in r.lower():
                    return r
    return None
