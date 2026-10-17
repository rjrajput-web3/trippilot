"""Deterministic itinerary + packing-list generation for TripPilot.

This is a rule-based planner (documented honestly in the README — it does
not call an LLM). It rotates interest themes across morning/afternoon/evening
slots and adapts to the weather snapshot (rain days push indoor activities).
"""

from __future__ import annotations

from datetime import date, timedelta

# interest keyword -> (theme label, [morning, afternoon, evening] activity ideas)
THEMES: dict[str, tuple[str, list[str]]] = {
    "beach": ("Beach & coast", [
        "Sunrise walk along the main beach before the crowds arrive",
        "Swim + relax at a quieter cove; try a local beach shack for lunch",
        "Sunset viewpoint, then dinner at a seafront restaurant",
    ]),
    "food": ("Food & drink", [
        "Breakfast at a local market; taste the regional specialty",
        "Food-tour style lunch crawl through the old quarter",
        "Dinner at a well-reviewed local restaurant; try the chef's tasting menu",
    ]),
    "culture": ("Culture & history", [
        "Visit the top museum / heritage site right at opening time",
        "Guided walking tour of the historic district",
        "Evening cultural show or performance, if available",
    ]),
    "nature": ("Nature & outdoors", [
        "Early hike or nature trail while it is cool",
        "Visit the main park, garden or viewpoint; picnic lunch",
        "Golden-hour photography at the best scenic spot",
    ]),
    "shopping": ("Shopping", [
        "Browse the local artisan market for souvenirs",
        "Explore the main shopping street / mall in the afternoon",
        "Night market visit for street food and crafts",
    ]),
    "adventure": ("Adventure", [
        "Book a morning adventure activity (kayak, snorkel, trek)",
        "Continue the adventure block or rent cycles to explore",
        "Relaxed evening: massage / spa to recover",
    ]),
    "nightlife": ("Nightlife", [
        "Slow morning; brunch at a trendy cafe",
        "Rooftop bar for sunset drinks",
        "Explore the nightlife district; check local gig listings",
    ]),
    "relax": ("Slow travel", [
        "Leisurely breakfast; no alarm today",
        "Cafe-hopping and people-watching in a nice neighbourhood",
        "Sunset spot, then an early night",
    ]),
}

INDOOR_SWAPS = {
    "beach": "Swap the beach for a spa/massage + indoor pool session",
    "nature": "Swap the hike for a museum or gallery visit",
    "adventure": "Swap the outdoor activity for a cooking class",
}


def _match_theme(interest: str) -> str:
    interest = interest.lower().strip()
    for key in THEMES:
        if key in interest or interest in key:
            return key
    return "culture"


def generate_itinerary(destination: str, start: date, end: date,
                       interests: list[str], weather_days: list[dict]) -> list[dict]:
    """Build a day-by-day plan. weather_days may be empty (dates out of range)."""
    themes = [_match_theme(i) for i in (interests or ["culture", "food"])]
    # Deduplicate while keeping order
    seen, ordered = set(), []
    for t in themes:
        if t not in seen:
            seen.add(t)
            ordered.append(t)

    weather_by_date = {w["date"]: w for w in weather_days}
    plan = []
    day_count = (end - start).days + 1
    for n in range(day_count):
        day = start + timedelta(days=n)
        iso = day.isoformat()
        theme_key = ordered[n % len(ordered)]
        label, slots = THEMES[theme_key]
        w = weather_by_date.get(iso)
        rainy = bool(w and (w.get("precip_prob_pct") or 0) >= 60)
        morning, afternoon, evening = slots
        weather_note = ""
        if w:
            weather_note = (
                f"Forecast: {w['temp_min_c']}–{w['temp_max_c']}°C. "
            )
            if rainy:
                swap = INDOOR_SWAPS.get(theme_key)
                weather_note += "High rain chance — " + (
                    swap + "." if swap else "keep an indoor backup plan."
                )
        plan.append({
            "day": n + 1,
            "date": iso,
            "theme": label,
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "weather_note": weather_note,
            "rain_adapted": rainy,
        })
    return plan


def packing_checklist(destination: str, interests: list[str],
                      weather_days: list[dict]) -> list[str]:
    """Essentials + weather/activity-aware additions."""
    items = [
        "Passport / ID + printed hotel & transport bookings",
        "Phone charger, power bank, universal travel adapter",
        "Basic medicines + any prescriptions",
        "Sunscreen and sunglasses",
    ]
    temps = [w["temp_max_c"] for w in weather_days if w.get("temp_max_c") is not None]
    if temps and min(temps) < 15:
        items.append("Warm layer / light jacket (cool days expected)")
    if temps and max(temps) > 30:
        items.append("Light breathable clothing + extra water bottle (hot days expected)")
    if any((w.get("precip_prob_pct") or 0) >= 60 for w in weather_days):
        items.append("Compact umbrella or rain jacket (rain likely on some days)")
    lowered = " ".join(interests).lower()
    if "beach" in lowered or "swim" in lowered:
        items.append("Swimwear + quick-dry towel")
    if "hike" in lowered or "nature" in lowered or "adventure" in lowered:
        items.append("Comfortable walking shoes + small daypack")
    if "culture" in lowered:
        items.append("Modest clothing for temples / religious sites")
    items.append(f"Local currency or card that works in {destination}")
    return items
