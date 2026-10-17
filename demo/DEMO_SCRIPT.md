# TripPilot — Demo Video Script (under 3 minutes)

Format: AI-narrated animated visualization of a REAL `plan_trip` program run.
All terminal/program output shown is genuine output captured from the working
code — never fabricated, and never presented as a live screen recording.

## Shot list

| # | Time | Visual | Voiceover |
|---|------|--------|-----------|
| 1 | 0:00–0:12 | Title card: "TripPilot ✈️ — your AI travel concierge. An Alexa+ Agent Skill." | See VO narration para 1. |
| 2 | 0:12–0:30 | Chat-style prompt appears, typed letter by letter: *"plan me a 4-day food trip to Tokyo next month under $1,500"* | Para 2. |
| 3 | 0:30–1:00 | Animated terminal: `agent_steps` lines appear one by one — "Located Tokyo, Japan", "Pulled 4-day forecast", "Converted budget: $1,500 ≈ 237,030 JPY", "Generated 4-day itinerary", "Saved as trip #4" | Para 3. |
| 4 | 1:00–1:50 | Itinerary cards animate in: Day 1–4 with morning/afternoon/evening themes; rain-adapted badge where applicable; packing checklist slides in; budget panel shows JPY conversion | Para 4. |
| 5 | 1:50–2:20 | Follow-up prompt: *"how's my Tokyo trip looking?"* → digest panel animates in (dates, budget, rain days, today's plan, latest note) | Para 5. |
| 6 | 2:20–2:50 | Architecture panel: MCP tools list; "Free data: Open-Meteo + Frankfurter. No keys. No cost." → MIT license card. Closing card: "TripPilot — built by Rohit Rajput" | Para 6. |

## Voiceover narration (simple, clear English — full text)

1. "Meet TripPilot: an AI travel concierge built as an agent skill. You talk to
it in plain English, and it plans your entire trip — flights of steps, all on
its own."

2. "Here's the ask: plan me a four-day food trip to Tokyo next month, under
one thousand five hundred dollars. One sentence. That's all it needs."

3. "Watch the agent work. It finds Tokyo's coordinates and timezone. It pulls
the real weather forecast for your exact travel dates. It converts your budget
to Japanese yen at live bank rates — one thousand five hundred dollars becomes
about two hundred thirty-seven thousand yen. Then it writes a full day-by-day
itinerary — and saves the trip, so it remembers."

4. "The itinerary rotates themes across morning, afternoon, and evening: food
markets, cultural landmarks, local restaurants. If a day looks rainy, it
automatically swaps outdoor plans for indoor ones. You also get a packing
checklist tailored to the forecast."

5. "Because TripPilot remembers, a follow-up works without repeating yourself.
Ask: how's my Tokyo trip looking? And you instantly get the dates, the budget,
the rain-adapted days, and today's plan."

6. "Everything runs on free, keyless data — Open-Meteo for weather, Frankfurter
for exchange rates. Zero cost to operate, open source under MIT. TripPilot:
one sentence in, a whole trip out."

---

## Assets

- `voiceover.mp3` — synthesized narration of the text above (English, single voice).
- `terminal-cast/` — frames for the animated terminal sequence, rendered from
  real captured output (`real-run-output.txt`).
- `real-run-output.txt` — the actual stdout of the verified `plan_trip` run
  shown in shots 3–4. Do not edit: it is the source of truth for the video.
