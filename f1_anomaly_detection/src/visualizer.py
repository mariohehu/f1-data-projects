import pandas as pd
import plotly.graph_objects as go

COLOR_MAP = {
    "Normal": "#378ADD",
    "Safety Car lap": "#FF6B35",
    "VSC lap": "#F7C59F",
    "Yellow Flag lap": "#FFD700",
    "Red Flag lap": "#CC0000",
    "Rain lap": "#6B9AC4",
    "Pit in lap": "#AAAAAA",
    "Pit out lap": "#CCCCCC",
    "Possible mechanical issue": "#E63946",
    "Track-wide incident": "#FF8C00",
    "Unknown anomaly": "#FFBE0B",
}

SIZE_MAP = {
    "Normal": 7,
    "Pit in lap": 6,
    "Pit out lap": 6,
}


def plot_anomalies(laps: pd.DataFrame, driver: str, race: str, season: int) -> go.Figure:
    fig = go.Figure()

    for label, group in laps.groupby("anomaly_label"):
        color = COLOR_MAP.get(label, "#888888")
        size = SIZE_MAP.get(label, 12)
        symbol = "circle" if label == "Normal" else "diamond"

        fig.add_trace(go.Scatter(
            x=group["LapNumber"],
            y=group["LapTime_sec"],
            mode="markers",
            name=label,
            marker=dict(color=color, size=size, symbol=symbol,
                        line=dict(width=1, color="white") if label != "Normal" else dict(width=0)),
            hovertemplate=(
                f"<b>{label}</b><br>"
                "Lap %{x}<br>"
                "Time: %{y:.3f}s<br>"
                "Tyre: %{customdata[0]}<br>"
                "Life: %{customdata[1]} laps<br>"
                "Z-score: %{customdata[2]:.2f}<extra></extra>"
            ),
            customdata=group[["Compound", "TyreLife", "z_score"]].fillna("?").values,
        ))

    fig.update_layout(
        title=f"Lap Time Anomalies — {driver} | {season} {race}",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (s)",
        legend_title="Event Type",
        height=520,
        template="plotly_dark",
        hovermode="closest",
    )
    return fig


def plot_comparison(laps_a: pd.DataFrame, laps_b: pd.DataFrame,
                    driver_a: str, driver_b: str,
                    race: str, season: int) -> go.Figure:
    fig = go.Figure()

    for laps, driver, base_color in [
        (laps_a, driver_a, "#378ADD"),
        (laps_b, driver_b, "#FF6B35"),
    ]:
        normal = laps[laps["anomaly_label"] == "Normal"]
        anomalous = laps[laps["anomaly_label"] != "Normal"]

        fig.add_trace(go.Scatter(
            x=normal["LapNumber"], y=normal["LapTime_sec"],
            mode="markers", name=f"{driver} — Normal",
            marker=dict(color=base_color, size=7, opacity=0.7),
        ))
        if not anomalous.empty:
            fig.add_trace(go.Scatter(
                x=anomalous["LapNumber"], y=anomalous["LapTime_sec"],
                mode="markers", name=f"{driver} — Anomaly",
                marker=dict(color=base_color, size=13, symbol="diamond",
                            line=dict(width=2, color="white")),
                hovertemplate="<b>%{customdata}</b><br>Lap %{x}<br>Time: %{y:.3f}s<extra></extra>",
                customdata=anomalous["anomaly_label"].values,
            ))

    fig.update_layout(
        title=f"Driver Comparison — {driver_a} vs {driver_b} | {season} {race}",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (s)",
        height=520,
        template="plotly_dark",
    )
    return fig
