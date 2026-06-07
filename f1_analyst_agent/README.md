# F1 Race Analyst Agent

A conversational AI agent that answers questions about F1 races using **real timing data**. Ask *"Why did Verstappen win at Monza?"* and it pulls actual race data through tools, then explains the result with specific lap numbers, gaps, and strategy decisions — no hallucinated numbers.

![Python](https://img.shields.io/badge/python-3.14-blue) ![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688) ![Ollama](https://img.shields.io/badge/LLM-Ollama%20(local)-black) ![Next.js](https://img.shields.io/badge/frontend-Next.js%2014-black)

---

## What it does

A **tool-calling agent**: the LLM has no race data baked in — it decides which tools to call, the tools fetch structured data from FastF1, and the LLM synthesises an answer grounded in that data. Runs on a **local Ollama model**, so it's free and needs no API key.

```
User question → LLM picks tools → FastF1 returns JSON → LLM synthesises answer
```

## Quickstart

**Prerequisites:** [Ollama](https://ollama.com) installed with a tool-capable model:
```bash
ollama pull gemma3        # or llama3.1, any tool-calling model
```

**Backend** (port 8000):
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

**Frontend** (port 3001):
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3001**.

> No API key required — everything runs locally. Optionally override the model in `backend/.env` (see `.env.example`).

## The 5 tools

| Tool | Returns |
|------|---------|
| `get_race_summary` | Podium, fastest lap, safety cars, DNFs, weather |
| `get_driver_race_data` | Lap times, pit stops, compounds, positions gained |
| `get_strategy_comparison` | Pit strategies & stints for the top 10 |
| `get_qualifying_context` | Grid positions, gaps to pole |
| `get_championship_context` | Standings before the race (via Jolpica API) |

## Architecture

```
backend/
├── main.py              # FastAPI + agentic loop (OpenAI-compatible Ollama client)
├── f1_data/loader.py    # FastF1 wrapper, session cache, fuzzy race-name resolution
└── tools/
    ├── race_tools.py     # get_race_summary, get_qualifying_context
    ├── driver_tools.py   # get_driver_race_data
    └── strategy_tools.py # get_strategy_comparison, get_championship_context
frontend/
├── app/page.tsx         # chat UI + sidebar
├── components/          # ChatMessage, RaceSelector
└── lib/api.ts           # backend client
```

## Design decisions

- **Grounded, not generative.** The system prompt forbids fabricating numbers; every claim must come from a tool result. Tool failures are surfaced honestly rather than papered over.
- **Fuzzy race resolution.** Accepts official names ("Italian Grand Prix"), keywords ("Italian"), and circuit nicknames ("Monza", "Silverstone", "Spa") — with whole-word matching so "Spa" resolves to Belgian, not Spanish.
- **Driver name resolution.** "Verstappen" → "VER" via the session results, so users don't need to know 3-letter codes.
- **Synthesis fallback.** Local models sometimes return empty content after tool rounds; the loop detects this and forces a final synthesis pass, so you never get a blank answer.
- **Lean context.** Tool outputs are capped (top-10 strategies, truncated lap lists) to keep the local model fast across multiple rounds.
- **Session memory.** Follow-up questions ("And Hamilton?") work without repeating the race.

## Known limitations (honest)

- **Latency.** On a local CPU model, answers take **~30s for simple questions, up to 2-4 minutes** for multi-tool questions ("why did X win" calls 1-3 tools). A hosted model (Claude/GPT) would respond in seconds — the code is OpenAI-compatible, so swapping is a two-line change.
- **Local model polish.** Smaller models occasionally produce minor text artifacts (e.g. a misspelled driver code) — the underlying *data* is always correct, only the prose is rougher than a frontier model.
- **First load is slow.** The first FastF1 fetch per race builds the cache (10-30s); subsequent calls are instant.

## Swapping to a hosted model

The backend uses the OpenAI-compatible client, so pointing it at Claude or GPT is trivial — change `base_url`/`api_key` in `main.py` and set `MODEL`. Hosted models are faster and produce cleaner prose, at a small per-call cost.

## Data sources

- **[FastF1](https://github.com/theOehrly/Fast-F1)** — race results, lap times, pit data, weather
- **[Jolpica API](https://github.com/jolpica/jolpica-f1)** — championship standings
- **[Ollama](https://ollama.com)** — local LLM runtime
