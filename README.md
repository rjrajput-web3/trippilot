# ✈️ TripPilot — Travel-Concierge Agent Skill

TripPilot is an **AI agent skill** (Alexa+ track) that plans complete trips
autonomously. Ask in plain English — *"plan me a 4-day food trip to Tokyo in
December under $1,500"* — and it geocodes the destination, pulls the real
forecast for your exact dates, converts your budget to local currency at live
ECB rates, generates a weather-adaptive day-by-day itinerary with a packing
list, and **remembers the trip** so follow-ups like *"how's my Tokyo trip
looking?"* work without repeating yourself.

## ⚡ 30-second quickstart

```bash
# Python 3.12+
pip install -r requirements.txt
python3 server.py
```

Then connect any MCP client to `http://127.0.0.1:8000/mcp` — e.g. MCP
Inspector: `npx @modelcontextprotocol/inspector`.

Try the full orchestration in one call:

```python
from trippilot import tools
trip = tools.tool_plan_trip(
    "Tokyo", "2026-12-01", "2026-12-04",
    budget_usd=1500, interests=["food", "culture"])
print(trip["agent_steps"])   # watch the agent work, step by step
print(trip["budget"])        # $1,500 converted to JPY at live rates
```

## 🧠 Architecture

TripPilot is a **Model Context Protocol (MCP) server** (spec 2025-11-25+,
Streamable HTTP) built on the MCP Python SDK 2.x. All logic lives in
`trippilot/`; `server.py` is a thin MCP wrapper, so the same tools also run
from plain Python.

| MCP tool | What it does |
|---|---|
| `plan_trip` | **Agentic orchestrator:** geocode → forecast → FX → itinerary → save, with a visible `agent_steps` trace |
| `get_weather` | Daily forecast (temp, weather code, rain probability) for a place + dates |
| `convert_currency` | Live ECB-rate conversion between ISO currencies |
| `geocode_place` | Place → coordinates, country, timezone (with fuzzy-match guard) |
| `get_trip` / `list_trips` | Read persistent trip memory (SQLite) |
| `add_trip_note` | Attach booking refs / reminders to a trip |
| `trip_digest` | One-screen trip brief: dates, budget, rain-adapted days, today's plan |

Also exposed: `trips://list` read-only MCP resource.

**Why it's agentic, not a thin wrapper:**
- One request fans out across geocoding, weather, currency and planning in a
  dependency-ordered pipeline.
- **Weather actually changes the plan:** rain probability ≥ 60% swaps outdoor
  activities for indoor alternatives.
- **State across sessions:** trips persist in SQLite; `trip_digest` replays
  dates, budget, rainy days, today's plan and latest note.

**Zero-cost design:** data providers are Open-Meteo (geocoding + forecast) and
Frankfurter (ECB FX rates) — both free, no API keys, no credentials anywhere
in the codebase. The v1 itinerary planner is deterministic and rule-based
(documented honestly; an LLM-backed planner is on the roadmap).

## 🎬 Demo

See `demo/DEMO_SCRIPT.md` for the shot-by-shot script and full narration.
The demo video is an AI-narrated visualization of a **real `plan_trip` run**
(genuine program output — never a fake screen recording).

## 🗂️ Project layout

```
server.py          # MCP server (Streamable HTTP)
trippilot/         # tools, providers, itinerary, SQLite db
demo/              # demo app + script + narration assets
FRICTION_LOG.md    # real frictions hit and solved (build bonus material)
LICENSE            # MIT
```

## 📜 License

MIT — see `LICENSE`. Copyright (c) 2026 Rohit Rajput.
