"""
F1 Race Analyst Agent — FastAPI backend (Ollama / OpenAI-compatible).
Run: uvicorn main:app --reload --port 8000
"""
import sys
import json
import os
import logging
from pathlib import Path

logging.disable(logging.WARNING)
sys.path.insert(0, str(Path(__file__).parent))

# optional .env (manual parse — robust against non-ASCII Windows paths)
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if "=" in _line and not _line.startswith("#"):
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools import (
    get_race_summary, get_qualifying_context,
    get_driver_race_data,
    get_strategy_comparison, get_championship_context,
)
from f1_data.loader import get_race_list

# ── Ollama client (OpenAI-compatible, local, free) ─────────────────────────
# Configurable via env: OLLAMA_BASE_URL, OLLAMA_MODEL
client = OpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
    api_key="ollama",   # required by the library, ignored by Ollama
)
MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")

app = FastAPI(title="F1 Race Analyst Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session memory ─────────────────────────────────────────────────────────
sessions: dict[str, list] = {}

# ── Tool definitions (OpenAI format) ──────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_race_summary",
            "description": "Get a high-level summary of a race: podium, fastest lap, safety cars, DNFs, weather.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "integer", "description": "Championship year e.g. 2023"},
                    "race": {"type": "string", "description": "Race name e.g. 'Monza', 'Italian', 'Silverstone'"},
                },
                "required": ["season", "race"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_driver_race_data",
            "description": "Get detailed data for one driver: lap times, pit stops, compounds, positions gained.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "integer"},
                    "race": {"type": "string"},
                    "driver": {"type": "string", "description": "3-letter driver code e.g. 'VER', 'HAM'"},
                },
                "required": ["season", "race", "driver"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_strategy_comparison",
            "description": "Get pit stop strategies for ALL drivers in a race: stints, compounds, number of stops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "integer"},
                    "race": {"type": "string"},
                },
                "required": ["season", "race"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_qualifying_context",
            "description": "Get qualifying results: grid positions, lap times, gaps to pole.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "integer"},
                    "race": {"type": "string"},
                },
                "required": ["season", "race"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_championship_context",
            "description": "Get driver championship standings before this race.",
            "parameters": {
                "type": "object",
                "properties": {
                    "season": {"type": "integer"},
                    "race": {"type": "string"},
                },
                "required": ["season", "race"],
            },
        },
    },
]

TOOL_MAP = {
    "get_race_summary": get_race_summary,
    "get_driver_race_data": get_driver_race_data,
    "get_strategy_comparison": get_strategy_comparison,
    "get_qualifying_context": get_qualifying_context,
    "get_championship_context": get_championship_context,
}

SYSTEM_PROMPT = """You are an expert F1 race analyst with access to real timing data.

Rules:
1. ALWAYS call the appropriate tools before answering — never fabricate lap times, gaps, or positions.
2. Base every claim on the data returned by tools. If a tool returns an error, say so honestly.
3. Cite specific evidence: lap numbers, time gaps, tyre compounds, position changes.
4. Explain the "why" behind events (e.g. "the undercut worked because the gap was only 2.3s").
5. Keep answers structured: start with a one-sentence summary, then detailed analysis."""


def execute_tool(name: str, arguments: str) -> str:
    fn = TOOL_MAP.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        inputs = json.loads(arguments)
        result = fn(**inputs)
        raw = json.dumps(result)
        # cap output to avoid context bloat
        if len(raw) > 6000 and isinstance(result, dict) and "lap_time_evolution" in result:
            result["lap_time_evolution"] = result["lap_time_evolution"][:15]
            result["_truncated"] = True
            raw = json.dumps(result)
        return raw
    except Exception as e:
        return json.dumps({"error": str(e)})


MAX_ROUNDS = 4  # local models are slow; cap tool rounds to keep latency sane


def _force_synthesis(msgs: list) -> str:
    """Final fallback: ask the model to answer using gathered data, no more tools.
    Local models sometimes return empty content after tool rounds; this recovers it."""
    synth = client.chat.completions.create(
        model=MODEL,
        messages=(
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + msgs
            + [{"role": "user", "content": "Now answer my original question using the data you gathered above. Be specific and cite the numbers."}]
        ),
        tool_choice="none",
    )
    return (synth.choices[0].message.content or "").strip()


async def run_agent(messages: list) -> tuple[str, list, int]:
    """Run the agentic loop. Returns (final_text, updated_messages, tool_call_count)."""
    msgs = list(messages)
    tool_calls_total = 0

    for round_idx in range(MAX_ROUNDS):
        last_round = round_idx == MAX_ROUNDS - 1
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + msgs,
            tools=TOOLS,
            tool_choice="none" if last_round else "auto",  # force text on last round
        )

        choice = response.choices[0]
        msg = choice.message

        if msg.tool_calls and not last_round:
            tool_calls_total += len(msg.tool_calls)

            msgs.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            for tc in msg.tool_calls:
                result = execute_tool(tc.function.name, tc.function.arguments)
                msgs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
            continue

        # no tool calls → final answer
        text = (msg.content or "").strip()
        if not text:
            # local model returned empty after tool rounds — force a synthesis pass
            text = _force_synthesis(msgs)
        if not text:
            text = "I gathered the race data but couldn't compose a reply. Try rephrasing the question."
        msgs.append({"role": "assistant", "content": text})
        return text, msgs, tool_calls_total

    # exhausted rounds without a clean stop — synthesise from what we have
    text = _force_synthesis(msgs) or "I gathered data across several steps but couldn't finalise an answer. Try a more specific question."
    msgs.append({"role": "assistant", "content": text})
    return text, msgs, tool_calls_total


# ── API models ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls_made: int


# ── Endpoints ───────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    history = sessions.get(req.session_id, [])
    history.append({"role": "user", "content": req.message})

    response_text, updated, tool_calls = await run_agent(history)
    sessions[req.session_id] = updated

    return ChatResponse(
        response=response_text,
        session_id=req.session_id,
        tool_calls_made=tool_calls,
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


@app.get("/races/{season}")
async def races(season: int):
    try:
        return {"season": season, "races": get_race_list(season)}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/health")
async def health():
    try:
        models = client.models.list()
        model_names = [m.id for m in models.data]
        ollama_ok = MODEL in model_names
    except Exception:
        ollama_ok = False
    return {"status": "ok", "ollama": ollama_ok, "model": MODEL}
