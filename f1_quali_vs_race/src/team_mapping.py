TEAM_MAPPING: dict[int, dict[str, str]] = {
    2022: {
        "VER": "Red Bull", "PER": "Red Bull",
        "HAM": "Mercedes", "RUS": "Mercedes",
        "LEC": "Ferrari", "SAI": "Ferrari",
        "NOR": "McLaren", "RIC": "McLaren",
        "ALO": "Alpine", "OCO": "Alpine",
        "BOT": "Alfa Romeo", "ZHO": "Alfa Romeo",
        "VET": "Aston Martin", "STR": "Aston Martin",
        "GAS": "AlphaTauri", "TSU": "AlphaTauri",
        "MAG": "Haas", "MSC": "Haas",
        "LAT": "Williams", "ALB": "Williams",
    },
    2023: {
        "VER": "Red Bull", "PER": "Red Bull",
        "HAM": "Mercedes", "RUS": "Mercedes",
        "LEC": "Ferrari", "SAI": "Ferrari",
        "NOR": "McLaren", "PIA": "McLaren",
        "ALO": "Aston Martin", "STR": "Aston Martin",
        "OCO": "Alpine", "GAS": "Alpine",
        "BOT": "Alfa Romeo", "ZHO": "Alfa Romeo",
        "DEV": "AlphaTauri", "TSU": "AlphaTauri", "LAW": "AlphaTauri",
        "MAG": "Haas", "HUL": "Haas",
        "ALB": "Williams", "SAR": "Williams",
    },
    2024: {
        "VER": "Red Bull", "PER": "Red Bull",
        "HAM": "Mercedes", "RUS": "Mercedes",
        "LEC": "Ferrari", "SAI": "Ferrari",
        "NOR": "McLaren", "PIA": "McLaren",
        "ALO": "Aston Martin", "STR": "Aston Martin",
        "OCO": "Alpine", "GAS": "Alpine",
        "BOT": "Sauber", "ZHO": "Sauber",
        "RIC": "RB", "TSU": "RB",
        "MAG": "Haas", "HUL": "Haas",
        "ALB": "Williams", "SAR": "Williams",
    },
}

TEAM_COLORS = {
    "Red Bull": "#3671C6",
    "Mercedes": "#27F4D2",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "AlphaTauri": "#5E8FAA",
    "RB": "#5E8FAA",
    "Alfa Romeo": "#C92D4B",
    "Sauber": "#C92D4B",
    "Haas": "#B6BABD",
}


def get_team(driver: str, season: int) -> str:
    return TEAM_MAPPING.get(season, {}).get(driver, "Unknown")


def get_team_color(team: str) -> str:
    return TEAM_COLORS.get(team, "#888888")
