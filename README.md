# F1 Data Projects 🏎

End-to-end Formula 1 data projects — machine learning, anomaly detection, a full web app, statistical analysis, and an AI agent — built on real F1 timing data via [FastF1](https://github.com/theOehrly/Fast-F1) and the [Jolpica API](https://github.com/jolpica/jolpica-f1).

---

## Projects

### 1. [Race Strategy Predictor](f1_strategy_predictor/) — `Python · XGBoost · Streamlit`
Predicts a driver's pit-stop window lap by lap. XGBoost classifier on 15 engineered features (tyre state, position dynamics, race context), with honest evaluation: **0.766 test AUC / 0.805 validation AUC**, clean time-series splits, and feature-importance analysis that shows *what the model actually learned*.

### 2. [Lap Time Anomaly Detection](f1_anomaly_detection/) — `Python · Isolation Forest · Streamlit`
Unsupervised detection of unusual laps (Safety Car, VSC, rain, mechanical issues) with **zero manual labelling**. Isolation Forest + Z-score agreement, then context-based auto-labelling that separates track-wide events from driver-specific ones.

### 3. [Driver Performance Dashboard](f1_driver_dashboard/) — `Next.js 14 · TypeScript · Recharts`
A web app comparing any two drivers across seasons — radar charts, bar grids, season trends. Server-side API with caching and rate limiting, direction-aware metric normalisation.

### 4. [Qualifying vs Race Pace](f1_quali_vs_race/) — `Python · seaborn · CLI`
Finds which teams "hide" pace in qualifying vs. the race via a `hidden_pace` metric. Three visualisations (scatter, team bar, season heatmap), with rain races and sprint weekends handled automatically.

### 5. [Race Analyst Agent](f1_analyst_agent/) — `Python · FastAPI · Ollama · Next.js`
A tool-calling AI agent that answers F1 questions using **real timing data** — no hallucinated numbers. Runs on a local Ollama model (free, no API key), with 5 data tools, fuzzy race/driver resolution, and a chat UI with session memory.

---

## Why these projects

Each one targets a different skill:

| Project | Demonstrates |
|---------|-------------|
| 1 | ML pipeline, time-series splitting, imbalanced classification, honest model evaluation |
| 2 | Unsupervised learning, feature design, domain-driven labelling |
| 3 | Full-stack web dev, API design, data viz, caching/rate-limiting |
| 4 | Statistical analysis, normalisation across heterogeneous conditions, CLI tooling |
| 5 | LLM agents, tool calling, RAG-style grounding, local model orchestration |

## Running them

Each project has its own README with setup instructions. Python projects need `pip install -r requirements.txt`; the dashboard needs `npm install`.

> **Note:** FastF1 caches, trained models, and `node_modules` are gitignored — they're regenerated on first run (see each project's README).

## Tech stack

`Python 3` · `XGBoost` · `scikit-learn` · `pandas` · `Streamlit` · `Plotly` · `seaborn` · `FastAPI` · `Ollama` · `Next.js 14` · `TypeScript` · `Recharts` · `FastF1` · `Jolpica API`

## Data sources

- **[FastF1](https://github.com/theOehrly/Fast-F1)** — official F1 timing, telemetry, and weather data
- **[Jolpica API](https://github.com/jolpica/jolpica-f1)** — drop-in successor to the Ergast API (which shut down in late 2024)
