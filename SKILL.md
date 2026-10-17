# TripPilot — Alexa+ Agent Skill

**Skill name:** trippilot-travel-concierge
**Version:** 0.1.0 · **Author:** Rohit Rajput

## What this skill does

TripPilot is a travel-concierge Agent Skill for Alexa+. A user says (or types)
something like *"plan me a 5-day beach trip to Goa next month under $800"* and
the skill autonomously orchestrates a multi-step workflow:

1. **Geocode** the destination (coordinates, country, timezone).
2. **Fetch the forecast** for the exact trip dates (Open-Meteo, free, no key).
3. **Convert the budget** to the destination's local currency (Frankfurter ECB rates).
4. **Generate a day-by-day itinerary** — rotating interest themes across
   morning/afternoon/evening slots, with rain days automatically adapted to
   indoor alternatives.
5. **Build a packing checklist** tailored to the forecast and activities.
6. **Persist the trip** in local skill memory (SQLite) so follow-ups work:
   *"how's my Goa trip looking?"*, *"add a note: flight AI202 booked"*,
   *"give me today's plan"*.

## Why it's agentic, not a thin wrapper

- **Multi-tool orchestration:** one request fans out to geocoding, weather,
  currency and planning in a dependency-ordered pipeline, with a visible
  `agent_steps` trace.
- **State across sessions:** trips persist; `trip_digest` replays dates, budget,
  rain-adapted days, today's plan and latest note without re-asking.
- **Context-aware adaptation:** weather actually changes the plan (rain ≥60%
  probability swaps outdoor activities for indoor ones).

## Tools (MCP)

| Tool | Purpose |
|---|---|
| `plan_trip` | Full orchestration: geocode → weather → FX → itinerary → save |
| `get_weather` | Daily forecast for a place + date range |
| `convert_currency` | ECB-rate conversion between ISO currencies |
| `geocode_place` | Place → coordinates / country / timezone |
| `get_trip` / `list_trips` | Read skill memory |
| `add_trip_note` | Attach notes/reminders to a trip |
| `trip_digest` | One-screen trip brief incl. today's plan |

Also exposed: `trips://list` MCP resource (read-only view of saved trips).

## Invocation examples

- "Alexa, ask TripPilot to plan a 4-day food trip to Tokyo in December under $1500."
- "Alexa, ask TripPilot how my Goa trip is looking."
- "Alexa, tell TripPilot to note on trip 2: hotel booked near the beach."

## Technical notes

- MCP spec 2025-11-25+, Streamable HTTP (`server.py`, SDK 2.x `MCPServer`).
- Zero external credentials: Open-Meteo + Frankfurter are keyless and free.
- The itinerary generator is rule-based (see README) — honest scope for v1;
  an LLM-backed planner is a listed roadmap item.
