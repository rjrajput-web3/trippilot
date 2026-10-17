"""Tool implementations shared by the MCP server and the web demo.

Each function is a pure-ish operation: raise ValueError on bad input,
return JSON-serialisable dicts otherwise. The MCP layer (server.py) and the
demo chat (demo/demo_app.py) are thin wrappers over these.
"""

from __future__ import annotations

from datetime import date, datetime

from . import db, itinerary, providers


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Date '{value}' must be YYYY-MM-DD.")


def tool_geocode(place_name: str) -> dict:
    return providers.geocode_place(place_name)


def tool_weather(place_name: str, start_date: str, end_date: str) -> dict:
    geo = providers.geocode_place(place_name)
    start, end = _parse_date(start_date), _parse_date(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date.")
    if (end - start).days > 16:
        raise ValueError("Forecast range is limited to 16 days.")
    wx = providers.get_daily_weather(geo["latitude"], geo["longitude"], iso(start), iso(end))
    for d in wx["days"]:
        d["summary"] = providers.weather_label(d["weather_code"])
    return {"place": geo, "forecast": wx["days"]}


def tool_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    if amount <= 0:
        raise ValueError("amount must be positive.")
    return providers.convert_currency(amount, from_currency, to_currency)


def tool_plan_trip(destination: str, start_date: str, end_date: str,
                   budget_usd: float = 1000.0,
                   interests: list[str] | None = None) -> dict:
    """Agentic orchestrator: geocode -> weather -> currency -> itinerary -> save."""
    interests = interests or ["culture", "food"]
    start, end = _parse_date(start_date), _parse_date(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date.")
    if (end - start).days > 30:
        raise ValueError("Trips longer than 30 days are not supported in v1.")
    if budget_usd <= 0:
        raise ValueError("budget_usd must be positive.")

    steps = []
    geo = providers.geocode_place(destination)
    steps.append(f"Located {geo['name']}, {geo['country']} ({geo['timezone']}).")

    # Weather only if any of the trip falls inside the 16-day forecast window.
    today = date.today()
    wx_days: list[dict] = []
    if start <= today + __import__("datetime").timedelta(days=16):
        wx_start = max(start, today).isoformat()
        wx_end = min(end, today + __import__("datetime").timedelta(days=16)).isoformat()
        wx = providers.get_daily_weather(geo["latitude"], geo["longitude"], wx_start, wx_end)
        wx_days = wx["days"]
        steps.append(f"Pulled {len(wx_days)}-day forecast for your dates.")
    else:
        steps.append("Trip is beyond the 16-day forecast window; plan is weather-neutral.")

    currency = providers.currency_for_country(geo["country_code"])
    fx = providers.convert_currency(budget_usd, "USD", currency)
    steps.append(f"Converted budget: ${budget_usd:,.0f} ≈ {fx['converted']:,.0f} {currency}.")

    plan = itinerary.generate_itinerary(geo["name"], start, end, interests, wx_days)
    steps.append(f"Generated {len(plan)}-day itinerary across {len(set(p['theme'] for p in plan))} themes.")
    packing = itinerary.packing_checklist(geo["name"], interests, wx_days)

    trip_id = db.save_trip({
        "destination": geo["name"],
        "country": geo["country"],
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "budget_usd": budget_usd,
        "budget_local": fx["converted"],
        "currency": currency,
        "interests": interests,
        "itinerary": plan,
        "weather": {"days": wx_days},
    })
    steps.append(f"Saved as trip #{trip_id} — ask me for it anytime.")

    return {
        "trip_id": trip_id,
        "destination": geo["name"],
        "country": geo["country"],
        "timezone": geo["timezone"],
        "dates": {"start": start.isoformat(), "end": end.isoformat()},
        "budget": {"usd": budget_usd, currency.lower(): fx["converted"], "currency": currency,
                   "fx_date": fx["date"]},
        "itinerary": plan,
        "packing_checklist": packing,
        "agent_steps": steps,
    }


def tool_get_trip(trip_id: int) -> dict:
    trip = db.get_trip(trip_id)
    if not trip:
        raise ValueError(f"No trip found with id {trip_id}.")
    return trip


def tool_list_trips(limit: int = 10) -> dict:
    trips = db.list_trips(limit)
    return {"count": len(trips), "trips": [
        {k: t[k] for k in ("id", "destination", "country", "start_date",
                           "end_date", "budget_usd", "currency", "created_at")}
        for t in trips
    ]}


def tool_add_note(trip_id: int, note: str) -> dict:
    if not note.strip():
        raise ValueError("note must not be empty.")
    if not db.add_note(trip_id, note.strip()):
        raise ValueError(f"No trip found with id {trip_id}.")
    return {"trip_id": trip_id, "note_added": note.strip()}


def tool_trip_digest(trip_id: int) -> dict:
    """One-screen brief: dates, budget, weather outlook, today's plan."""
    trip = tool_get_trip(trip_id)
    today = date.today().isoformat()
    todays_plan = next((d for d in trip["itinerary"] if d["date"] == today), None)
    rainy_days = sum(1 for d in trip["itinerary"] if d.get("rain_adapted"))
    return {
        "trip_id": trip_id,
        "destination": trip["destination"],
        "dates": f"{trip['start_date']} → {trip['end_date']}",
        "budget": f"${trip['budget_usd']:,.0f} USD ≈ {trip['budget_local']:,.0f} {trip['currency']}",
        "days_planned": len(trip["itinerary"]),
        "rain_adapted_days": rainy_days,
        "notes_count": len(trip["notes"]),
        "todays_plan": todays_plan,
        "latest_note": trip["notes"][-1] if trip["notes"] else None,
    }


def iso(d: date) -> str:
    return d.isoformat()
