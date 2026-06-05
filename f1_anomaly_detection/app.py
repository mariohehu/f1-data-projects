import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import fastf1

from loader import load_session, get_laps, get_race_list, get_driver_list
from detector import detect_anomalies
from labeler import label_anomalies
from visualizer import plot_anomalies, plot_comparison

CACHE_DIR = Path(__file__).parent / "data" / "cache"
fastf1.Cache.enable_cache(str(CACHE_DIR))

st.set_page_config(page_title="F1 Anomaly Detection", layout="wide")
st.title("F1 Lap Time Anomaly Detection")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    season = st.selectbox("Season", [2021, 2022, 2023])

    with st.spinner("Loading calendar..."):
        try:
            races = get_race_list(season)
        except Exception as e:
            st.error(str(e))
            races = []

    race = st.selectbox("Race", races) if races else None

    compare_mode = st.checkbox("Compare 2 drivers")

    if race:
        with st.spinner("Loading drivers..."):
            try:
                drivers = get_driver_list(season, race)
            except Exception as e:
                st.error(str(e))
                drivers = []

        driver_a = st.selectbox("Driver", drivers) if drivers else None
        driver_b = st.selectbox("Driver B", drivers, index=min(1, len(drivers)-1)) if (compare_mode and drivers) else None
    else:
        driver_a = driver_b = None

    st.divider()
    contamination = st.slider(
        "Isolation Forest sensitivity",
        min_value=0.01, max_value=0.15, value=0.05, step=0.01,
        help="Higher = more anomalies detected"
    )
    zscore_thresh = st.slider(
        "Z-score threshold",
        min_value=1.5, max_value=4.0, value=2.5, step=0.1
    )

    run = st.button("Detect Anomalies", disabled=(driver_a is None))

# --- Main ---
if run and driver_a:
    with st.spinner(f"Loading {season} {race}... (first load may take ~30s)"):
        try:
            session = load_session(season, race)
            all_laps = get_laps(session)
        except Exception as e:
            st.error(f"Failed to load session: {e}")
            st.stop()

    # detect anomalies for ALL drivers first (needed for track-wide detection)
    all_detected = detect_anomalies(all_laps, contamination=contamination,
                                     zscore_thresh=zscore_thresh)
    all_labelled = label_anomalies(all_detected, session)

    laps_a = all_labelled[all_labelled["Driver"] == driver_a].copy()

    if compare_mode and driver_b:
        laps_b = all_labelled[all_labelled["Driver"] == driver_b].copy()
        fig = plot_comparison(laps_a, laps_b, driver_a, driver_b, race, season)
    else:
        fig = plot_anomalies(laps_a, driver_a, race, season)

    st.plotly_chart(fig, use_container_width=True)

    # --- Summary stats ---
    anomaly_df = laps_a[laps_a["anomaly_label"] != "Normal"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Laps", len(laps_a))
    col2.metric("Anomalies Detected", len(anomaly_df))
    col3.metric("Anomaly Rate", f"{len(anomaly_df)/max(len(laps_a),1):.1%}")

    if not anomaly_df.empty:
        st.subheader("Anomaly Breakdown")
        breakdown = (
            anomaly_df.groupby("anomaly_label")
            .agg(count=("LapNumber", "count"), laps=("LapNumber", list))
            .reset_index()
        )
        breakdown["laps"] = breakdown["laps"].apply(lambda x: ", ".join(map(str, sorted(x))))
        st.dataframe(breakdown.rename(columns={
            "anomaly_label": "Type", "count": "Count", "laps": "Lap Numbers"
        }), use_container_width=True)

    with st.expander("Full lap data"):
        show_cols = ["LapNumber", "LapTime_sec", "Compound", "TyreLife",
                     "Position", "z_score", "anomaly_score", "anomaly_label"]
        st.dataframe(laps_a[[c for c in show_cols if c in laps_a.columns]],
                     use_container_width=True)

else:
    st.info("Select a season, race, and driver then click **Detect Anomalies**.")
    st.markdown("""
    ### What it detects
    - **Safety Car / VSC laps** — detected via TrackStatus
    - **Rain laps** — via weather data
    - **Pit in/out laps** — filtered separately
    - **Mechanical issues** — unexplained slow laps (Isolation Forest + Z-score)
    - **Track-wide incidents** — when >50% of drivers show anomaly on same lap

    ### Methods
    - **Isolation Forest** (primary) — multivariate, considers tyre age
    - **Z-score** (secondary confirmation) — lap time outliers per driver
    """)
