import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
import plotly.graph_objects as go
import fastf1

from data_loader import get_race_list, get_driver_list
from predict import predict_pit_window

CACHE_DIR = Path(__file__).parent / "data" / "raw"
fastf1.Cache.enable_cache(str(CACHE_DIR))

st.set_page_config(page_title="F1 Race Strategy Predictor", layout="wide")
st.title("F1 Race Strategy Predictor")

# --- Sidebar controls ---
with st.sidebar:
    st.header("Select Race")
    season = st.selectbox("Season", [2021, 2022, 2023])

    with st.spinner("Loading race calendar..."):
        try:
            races = get_race_list(season)
        except Exception as e:
            st.error(f"Could not load calendar: {e}")
            races = []

    race = st.selectbox("Race", races) if races else None

    if race:
        with st.spinner("Loading drivers..."):
            try:
                drivers = get_driver_list(season, race)
            except Exception as e:
                st.error(f"Could not load drivers: {e}")
                drivers = []
        driver = st.selectbox("Driver", drivers) if drivers else None
    else:
        driver = None

    run = st.button("Predict Strategy", disabled=(driver is None))

# --- Main area ---
if run and driver:
    with st.spinner(f"Loading {season} {race} — {driver}... (first load may take ~30s)"):
        try:
            result = predict_pit_window(season, race, driver)
        except FileNotFoundError:
            st.error("Model not found. Run `python src/train.py` first to train the model.")
            st.stop()
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    # --- Chart ---
    fig = go.Figure()

    # Lap times as scatter
    fig.add_trace(go.Scatter(
        x=result["LapNumber"],
        y=result["LapTime_sec"],
        mode="markers+lines",
        name="Lap Time",
        marker=dict(
            color=result["PitProbability"],
            colorscale="RdYlGn_r",
            size=10,
            colorbar=dict(title="Pit Probability"),
            showscale=True,
        ),
        hovertemplate=(
            "Lap %{x}<br>"
            "Time: %{y:.3f}s<br>"
            "Compound: %{customdata[0]}<br>"
            "Tyre Life: %{customdata[1]} laps<br>"
            "Pit Prob: %{customdata[2]:.1%}"
        ),
        customdata=result[["Compound", "TyreLife", "PitProbability"]].values,
    ))

    # Highlight predicted pit laps
    pit_laps = result[result["PredictedPit"] == 1]
    if not pit_laps.empty:
        fig.add_trace(go.Scatter(
            x=pit_laps["LapNumber"],
            y=pit_laps["LapTime_sec"],
            mode="markers",
            name="Predicted Pit Window",
            marker=dict(color="red", size=16, symbol="triangle-down"),
        ))

    # Mark where the driver ACTUALLY pitted (ground truth) for comparison
    actual_laps = result[result["ActualNextPit"] == 1]
    if not actual_laps.empty:
        fig.add_trace(go.Scatter(
            x=actual_laps["LapNumber"],
            y=actual_laps["LapTime_sec"],
            mode="markers",
            name="Actual Pit (next lap)",
            marker=dict(color="cyan", size=14, symbol="circle-open",
                        line=dict(width=3)),
        ))

    fig.update_layout(
        title=f"{driver} — {season} {race} Strategy Prediction",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (s)",
        height=500,
        template="plotly_dark",
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Stats table ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Laps Analyzed", len(result))
    col2.metric("Predicted Pit Laps", int(result["PredictedPit"].sum()))
    col3.metric("Actual Pit Laps", int(result["ActualNextPit"].sum()))
    # how many predicted pits matched an actual pit (within ±1 lap tolerance)
    actual_set = set(result.loc[result["ActualNextPit"] == 1, "LapNumber"])
    pred_set = set(result.loc[result["PredictedPit"] == 1, "LapNumber"])
    hits = sum(any(abs(p - a) <= 1 for a in actual_set) for p in pred_set)
    col4.metric("Pred within ±1 lap", f"{hits}/{len(pred_set) or 0}")

    with st.expander("Raw prediction data"):
        st.dataframe(result, use_container_width=True)

else:
    st.info("Select a season, race, and driver from the sidebar, then click **Predict Strategy**.")
    st.markdown("""
    ### How it works
    1. **FastF1** loads lap data (lap times, tyre compounds, positions)
    2. **Feature engineering** computes tyre degradation, gap to car ahead, laps remaining
    3. **XGBoost classifier** predicts pit probability for each lap
    4. Laps above 40% probability are marked as predicted pit window

    > **Note:** Train the model first with `python src/train.py`
    """)
