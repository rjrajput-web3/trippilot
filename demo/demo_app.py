#!/usr/bin/env python3
"""Simulated Alexa+ experience for TripPilot (demo web app, stdlib only).

Serves demo/index.html and a /api/chat endpoint that interprets simple
natural-language commands and drives the SAME tool functions the MCP server
exposes. This is the "simulated Alexa+ experience" path the hackathon rules
explicitly allow for the Alexa+ track.

Run:
    python3 demo/demo_app.py
Open http://127.0.0.1:8080 in a browser.
Port overridable via DEMO_PORT.
"""

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))

from trippilot import tools  # noqa: E402


def fmt_money(amount: float, currency: str) -> str:
    return f"{amount:,.0f} {currency}"


def render_plan(result: dict) -> str:
    lines = [
        f"✈️ Trip #{result['trip_id']}: {result['destination']}, {result['country']}",
        f"📅 {result['dates']['start']} → {result['dates']['end']}  ({result['timezone']})",
        b = result["budget"],
        f"💰 Budget: ${b['usd']:,.0f} ≈ {b[b['currency'].lower()]:,.0f} {b['currency']}",
        "",
    ]
    for day in result["itinerary"]:
        lines.append(f"Day {day['day']} ({day['date']}) — {day['theme']}")
        lines.append(f"  🌅 {day['morning']}")
        lines.append(f"  ☀️ {day['afternoon']}")
        lines.append(f"  🌙 {day['evening']}")
        if day["weather_note"]:
            lines.append(f"  🌦 {day['weather_note']}")
    lines += ["", "🎒 Packing:"]
    lines += [f"  • {item}" for item in result["packing_checklist"]]
    return "\n".join(lines)


def render_digest(d: dict) -> str:
    lines = [
        f"🧾 Trip #{d['trip_id']}: {d['destination']}",
        f"📅 {d['dates']}",
        f"💰 {d['budget']}",
        f"🗓 {d['days_planned']} days planned · 🌧 {d['rain_adapted_days']} rain-adapted · 📝 {d['notes_count']} notes",
    ]
    if d["todays_plan"]:
        p = d["todays_plan"]
        lines += ["", f"Today ({p['date']}) — {p['theme']}:",
                  f"  🌅 {p['morning']}", f"  ☀️ {p['afternoon']}", f"  🌙 {p['evening']}"]
        if p["weather_note"]:
            lines.append(f"  🌦 {p['weather_note']}")
    if d["latest_note"]:
        lines.append(f"\nLatest note: “{d['latest_note']['text']}”")
    return "\n".join(lines)


HELP = (
    "I can help you plan trips. Try:\n"
    "• “plan a trip to Goa from 2026-11-05 to 2026-11-09, budget 800, likes beach food”\n"
    "• “weather in Tokyo from 2026-10-20 to 2026-10-23”\n"
    "• “convert 500 USD to EUR”\n"
    "• “my trips” · “trip 1” · “digest of trip 1”\n"
    "• “note on trip 1: booked flight AI202”"
)


def handle_chat(message: str) -> str:
    msg = message.strip()
    low = msg.lower()

    if re.match(r"^(hi|hello|hey)\b", low):
        return "Hello! I'm TripPilot, your travel concierge. " + HELP
    if "help" in low or "what can you" in low:
        return HELP

    m = re.match(
        r"plan (?:a )?trip to (.+?) from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})"
        r"(?:,?\s*budget\s*(\d+(?:\.\d+)?))?(?:,?\s*(?:likes?|interests?|into)\s*(.+))?$",
        low,
    )
    if m:
        dest, start, end = m.group(1).strip(), m.group(2), m.group(3)
        budget = float(m.group(4)) if m.group(4) else 1000.0
        interests = [w.strip() for w in m.group(5).split(",")] if m.group(5) else ["culture", "food"]
        try:
            return render_plan(tools.tool_plan_trip(dest, start, end, budget, interests))
        except Exception as e:  # noqa: BLE001 — surface provider errors honestly
            return f"Couldn't plan that trip: {e}"

    m = re.match(r"weather in (.+?) from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", low)
    if m:
        try:
            r = tools.tool_weather(m.group(1).strip(), m.group(2), m.group(3))
            lines = [f"🌤 {r['place']['name']}, {r['place']['country']}:"]
            for d in r["forecast"]:
                lines.append(
                    f"  {d['date']}: {d['summary']}, {d['temp_min_c']}–{d['temp_max_c']}°C"
                )
            return "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            return f"Couldn't fetch weather: {e}"

    m = re.match(r"convert (\d+(?:\.\d+)?)\s*([a-z]{3})\s*to\s*([a-z]{3})", low)
    if m:
        try:
            r = tools.tool_currency(float(m.group(1)), m.group(2), m.group(3))
            return (f"💱 {r['amount']:,.0f} {r['from']} = {r['converted']:,.2f} {r['to']} "
                    f"(rate {r['rate']}, {r['date']})")
        except Exception as e:  # noqa: BLE001
            return f"Couldn't convert: {e}"

    if re.match(r"^(my trips|list trips|show trips)$", low):
        r = tools.tool_list_trips()
        if not r["count"]:
            return "No trips saved yet — ask me to plan one!"
        return "\n".join(
            f"#{t['id']}: {t['destination']}, {t['country']} "
            f"({t['start_date']} → {t['end_date']})" for t in r["trips"]
        )

    m = re.match(r"^(?:trip|show trip|digest of trip|digest)\s+(\d+)$", low)
    if m:
        try:
            return render_digest(tools.tool_trip_digest(int(m.group(1))))
        except Exception as e:  # noqa: BLE001
            return f"Couldn't load that trip: {e}"

    m = re.match(r"note on trip (\d+):\s*(.+)$", low, re.S)
    if m:
        try:
            tools.tool_add_note(int(m.group(1)), m.group(2).strip())
            return f"📝 Note saved on trip {m.group(1)}."
        except Exception as e:  # noqa: BLE001
            return f"Couldn't save the note: {e}"

    return ("I didn't catch that. " + HELP)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            with open(os.path.join(BASE, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/chat":
            self._send(404, b"not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            payload = {}
        reply = handle_chat(str(payload.get("message", "")))
        self._send(200, json.dumps({"reply": reply}).encode(), "application/json")


if __name__ == "__main__":
    port = int(os.environ.get("DEMO_PORT", "8080"))
    print(f"TripPilot demo at http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
