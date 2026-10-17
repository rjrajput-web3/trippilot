#!/usr/bin/env python3
"""Render TripPilot demo video frames with PIL.

Every number/text shown is genuine output from demo/real-run-output.txt
(the verified plan_trip run, trip #6). Each frame is labeled as an
AI-narrated visualization of a real run — never presented as live recording.
"""
import os, textwrap
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "terminal-cast")
W, H = 1280, 720
BG = (18, 20, 28); CARD = (28, 32, 44); ACCENT = (86, 180, 255)
GREEN = (90, 220, 140); TEXT = (235, 238, 245); DIM = (150, 160, 180)

FS = "/usr/share/fonts/truetype/dejavu/"
def f(sz, bold=False): return ImageFont.truetype(FS + ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), sz)
def fm(sz): return ImageFont.truetype(FS + "DejaVuSansMono.ttf", sz)

LABEL = "AI-narrated visualization of a real TripPilot run"

def base(title=None):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    if title:
        d.text((60, 34), title, font=f(30, True), fill=ACCENT)
        d.line((60, 78, W-60, 78), fill=(45, 52, 70), width=2)
    d.text((60, H-40), LABEL, font=f(16), fill=(100, 108, 128))
    return img, d

def save(name, img): img.save(os.path.join(OUT, name)); print("frame:", name)

def wrap(d, text, font, maxw):
    out, line = [], ""
    for w in text.split():
        if d.textlength(line + " " + w, font=font) <= maxw:
            line = (line + " " + w).strip()
        else:
            out.append(line); line = w
    if line: out.append(line)
    return out

# --- 1. title ---
img, d = base()
d.text((W//2, 260), "TripPilot", font=f(92, True), fill=ACCENT, anchor="mm")
d.text((W//2, 360), "your AI travel concierge", font=f(40), fill=TEXT, anchor="mm")
d.text((W//2, 440), "An Alexa+ Agent Skill  \u00b7  Amazon Developer Hackathon", font=f(24), fill=DIM, anchor="mm")
save("01_title.png", img)

# --- 2. the ask ---
img, d = base("The ask")
d.rounded_rectangle((60, 140, W-60, 300), 18, fill=CARD)
ask = 'plan me a 4-day food trip to Tokyo under $1,500'
for i, ln in enumerate(wrap(d, '\u201c' + ask + '\u201d', f(34), W-240)):
    d.text((110, 180+i*50), ln, font=f(34), fill=TEXT)
d.text((110, 240), 'one sentence \u2014 that is all it needs', font=f(22), fill=DIM)
save("02_ask.png", img)

# --- 3-5. terminal: agent steps (genuine run output) ---
STEPS = [
    "$ plan_trip('Tokyo', '2026-10-18', '2026-10-21', budget_usd=1500, interests=['food', 'culture'])",
    "- Located Tokyo, Japan (Asia/Tokyo).",
    "- Pulled 4-day forecast for your dates.",
    "- Converted budget: $1,500 \u2248 237,030 JPY.",
    "- Generated 4-day itinerary across 2 themes.",
    "- Saved as trip #6 \u2014 ask me for it anytime.",
]
for k in (1, 3, 6):
    img, d = base("Real run output: agent steps")
    d.rounded_rectangle((60, 120, W-60, H-80), 16, fill=(12, 14, 20))
    y = 150
    for j, ln in enumerate(STEPS[:k]):
        col = GREEN if j == 0 else TEXT
        ln = ln if j == 0 else "  " + ln
        for sub in wrap(d, ln, fm(24), W-200):
            d.text((100, y), sub, font=fm(24), fill=col); y += 40
        y += 8
    save(f"03_terminal{k}.png", img)

# --- 6-7. itinerary cards (genuine itinerary text) ---
DAYS = [
    ("Day 1 \u00b7 2026-10-18 \u00b7 Food & drink", "12.1\u201322.2\u00b0C",
     ["Breakfast at a local market; taste the regional specialty",
      "Food-tour style lunch crawl through the old quarter",
      "Dinner at a well-reviewed local restaurant"]),
    ("Day 2 \u00b7 2026-10-19 \u00b7 Culture & history", "14.4\u201325.6\u00b0C",
     ["Visit the top museum / heritage site right at opening time",
      "Guided walking tour of the historic district",
      "Evening cultural show or performance"]),
    ("Day 3 \u00b7 2026-10-20 \u00b7 Food & drink", "20.9\u201329.3\u00b0C",
     ["Breakfast at a local market; taste the regional specialty",
      "Food-tour style lunch crawl through the old quarter",
      "Dinner at a well-reviewed local restaurant"]),
    ("Day 4 \u00b7 2026-10-21 \u00b7 Culture & history", "21.4\u201329.3\u00b0C",
     ["Visit the top museum / heritage site right at opening time",
      "Guided walking tour of the historic district",
      "Evening cultural show or performance"]),
]
for k, idxs in (("a", (0, 1)), ("b", (2, 3))):
    img, d = base("Real run output: 4-day itinerary (Tokyo)")
    for i, di in enumerate(idxs):
        title, wx, slots = DAYS[di]
        y0 = 120 + i * 250
        d.rounded_rectangle((60, y0, W-60, y0+228), 16, fill=CARD)
        d.text((90, y0+14), title, font=f(24, True), fill=ACCENT)
        d.text((90, y0+50), "Forecast: " + wx, font=f(19), fill=DIM)
        y = y0 + 86
        for lab, s in zip(("Morning", "Afternoon", "Evening"), slots):
            for sub in wrap(d, lab + ": " + s, f(20), W-260):
                d.text((90, y), sub, font=f(20), fill=TEXT); y += 30
            y += 8
    save(f"04_itinerary{k}.png", img)

# --- 8. packing ---
img, d = base("Real run output: packing checklist (forecast-tailored)")
ITEMS = [
    "Passport / ID + printed hotel & transport bookings",
    "Phone charger, power bank, universal travel adapter",
    "Basic medicines + any prescriptions",
    "Sunscreen and sunglasses",
    "Modest clothing for temples / religious sites",
    "Local currency or card that works in Tokyo",
]
y = 140
for it in ITEMS:
    d.rounded_rectangle((90, y, W-90, y+58), 12, fill=CARD)
    d.text((120, y+15), "\u2713  " + it, font=f(22), fill=TEXT); y += 76
save("05_packing.png", img)

# --- 9. budget ---
img, d = base("Real run output: budget conversion (live ECB rates)")
d.rounded_rectangle((60, 150, W-60, 420), 20, fill=CARD)
d.text((W//2, 220), "$1,500 USD", font=f(56, True), fill=TEXT, anchor="mm")
d.text((W//2, 300), "\u2248  237,030 JPY", font=f(56, True), fill=GREEN, anchor="mm")
d.text((W//2, 370), "FX date 2026-10-16 \u00b7 Frankfurter / ECB", font=f(22), fill=DIM, anchor="mm")
save("06_budget.png", img)

# --- 10. digest ---
img, d = base("Follow-up: \u201chow is my Tokyo trip looking?\u201d")
ROWS = [("Destination", "Tokyo"), ("Dates", "2026-10-18 \u2192 2026-10-21"),
        ("Budget", "$1,500 USD \u2248 237,030 JPY"), ("Days planned", "4"),
        ("Rain-adapted days", "0"), ("Latest note", "Flight AI-302 booked, aisle seat")]
y = 130
for k2, v in ROWS:
    d.rounded_rectangle((90, y, W-90, y+56), 12, fill=CARD)
    d.text((120, y+15), k2, font=f(21, True), fill=ACCENT)
    d.text((430, y+15), v, font=f(21), fill=TEXT); y += 72
save("07_digest.png", img)

# --- 11. MCP tools ---
img, d = base("Architecture: MCP tools (spec 2025-11-25+, Streamable HTTP)")
TOOLS = ["plan_trip  \u2014  agentic orchestration with visible agent_steps",
         "get_weather  \u2014  daily forecast (Open-Meteo, free, no key)",
         "convert_currency  \u2014  ECB rates (Frankfurter, free, no key)",
         "geocode_place  \u2014  coordinates + timezone, fuzzy-match guard",
         "get_trip / list_trips / add_trip_note / trip_digest",
         "trips://list  \u2014  read-only MCP resource"]
y = 130
for t in TOOLS:
    d.text((100, y), "\u2022  " + t, font=f(23), fill=TEXT); y += 62
save("08_mcp.png", img)

# --- 12. outro ---
img, d = base()
d.text((W//2, 250), "Free, keyless data \u00b7 zero cost to run", font=f(38, True), fill=TEXT, anchor="mm")
d.text((W//2, 320), "Open source under MIT", font=f(32), fill=DIM, anchor="mm")
d.text((W//2, 430), "TripPilot \u2014 one sentence in, a whole trip out", font=f(36, True), fill=ACCENT, anchor="mm")
d.text((W//2, 500), "built by Rohit Rajput", font=f(24), fill=DIM, anchor="mm")
save("09_outro.png", img)
print("ALL FRAMES DONE")
