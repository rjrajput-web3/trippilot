"""Free, keyless external data providers used by TripPilot.

- Geocoding + weather: Open-Meteo (https://open-meteo.com) — free, no API key.
- Currency conversion: Frankfurter (https://frankfurter.dev) — free ECB rates, no API key.

Zero-cost by design: no paid APIs, no secrets, no credentials anywhere.
"""

from __future__ import annotations

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FX_URL = "https://api.frankfurter.dev/v1"  # migrated from api.frankfurter.app (Oct 2026)

_TIMEOUT = 15.0

# ISO country code -> ISO 4217 currency code (common destinations; fallback USD)
COUNTRY_CURRENCY = {
    "US": "USD", "GB": "GBP", "IN": "INR", "JP": "JPY", "AU": "AUD",
    "CA": "CAD", "CH": "CHF", "CN": "CNY", "SG": "SGD", "AE": "AED",
    "TH": "THB", "MY": "MYR", "ID": "IDR", "KR": "KRW", "HK": "HKD",
    "NZ": "NZD", "ZA": "ZAR", "BR": "BRL", "MX": "MXN", "TR": "TRY",
    "SA": "SAR", "QA": "QAR", "KW": "KWD", "EG": "EGP", "IL": "ILS",
    "SE": "SEK", "NO": "NOK", "DK": "DKK", "PL": "PLN", "CZ": "CZK",
    "HU": "HUF", "RO": "RON", "GR": "EUR", "IT": "EUR", "ES": "EUR",
    "FR": "EUR", "DE": "EUR", "NL": "EUR", "PT": "EUR", "AT": "EUR",
    "BE": "EUR", "IE": "EUR", "FI": "EUR",
}

# Frankfurter only serves ~30 ECB currencies; non-ECB codes fall back to USD display.
_FX_CURRENCIES: set[str] | None = None


import os


def _sanitized_proxy_env():
    """Temporarily drop malformed no_proxy entries that crash httpx's parser.

    Runtimes sometimes ship bracketed IPv6 tokens (e.g. ``[::1]``) in
    ``no_proxy`` which httpx cannot parse, killing client construction and
    with it every proxied request. The unbracketed ``::1`` entry covers the
    same host, so removing bracketed tokens is behavior-safe. Returns a
    restore callable.
    """
    saved = {}
    for key in ("no_proxy", "NO_PROXY"):
        val = os.environ.get(key)
        if val and "[" in val:
            saved[key] = val
            cleaned = ",".join(
                tok for tok in val.split(",") if "[" not in tok
            )
            os.environ[key] = cleaned
    return saved


def _restore_proxy_env(saved: dict):
    for key, val in saved.items():
        os.environ[key] = val


def _get(url: str, params: dict | None = None, **kwargs) -> httpx.Response:
    """GET with a proxy-env-tolerant client (see _sanitized_proxy_env)."""
    saved = _sanitized_proxy_env()
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:  # trust_env=True
            return client.get(url, params=params)
    finally:
        _restore_proxy_env(saved)


def supported_fx_currencies() -> set[str]:
    """Currencies actually servable by the Frankfurter API (cached)."""
    global _FX_CURRENCIES
    if _FX_CURRENCIES is None:
        try:
            r = _get(f"{FX_URL}/currencies")
            r.raise_for_status()
            _FX_CURRENCIES = set(r.json().keys())
        except Exception:
            _FX_CURRENCIES = {"USD", "EUR", "GBP", "INR", "JPY"}
    return _FX_CURRENCIES


def geocode_place(place_name: str) -> dict:
    """Resolve a place name to coordinates, country and timezone."""
    r = _get(
        GEOCODE_URL,
        params={"name": place_name, "count": 1, "language": "en", "format": "json"},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Could not find a place named '{place_name}'.")
    top = results[0]
    # Fuzzy-match guard: Open-Meteo sometimes returns a loosely similar
    # place ("Goa" -> "Genoa"). Flag it so the caller can surface a warning.
    q = "".join(ch for ch in place_name.strip().lower() if ch.isalnum() or ch == " ")
    q = " ".join(q.split())  # collapse whitespace
    name = top.get("name", "")
    haystack = " ".join([
        name, top.get("country", ""), top.get("admin1", ""), top.get("admin2", ""),
    ]).lower()
    match_confidence = "high" if q in haystack else "low"
    result = {
        "name": name,
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "country": top.get("country", ""),
        "country_code": top.get("country_code", ""),
        "timezone": top.get("timezone", "UTC"),
        "admin1": top.get("admin1", ""),
        "match_confidence": match_confidence,
    }
    if match_confidence == "low":
        result["match_note"] = (
            f"'{place_name}' matched '{name}' loosely — "
            "confirm this is the intended destination."
        )
    return result


def get_daily_weather(latitude: float, longitude: float, start_date: str,
                      end_date: str) -> dict:
    """Daily forecast (max/min temp, weather code, precipitation) for a date range.

    Open-Meteo serves up to 16 days ahead; dates beyond that raise ValueError.
    """
    r = _get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max",
            "timezone": "auto",
        },
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    daily = r.json().get("daily", {})
    days = []
    times = daily.get("time", [])
    for i, day in enumerate(times):
        days.append({
            "date": day,
            "temp_max_c": daily["temperature_2m_max"][i],
            "temp_min_c": daily["temperature_2m_min"][i],
            "weather_code": daily["weathercode"][i],
            "precip_prob_pct": daily["precipitation_probability_max"][i],
        })
    return {"days": days, "timezone": r.json().get("timezone", "UTC")}


WEATHER_CODE_LABELS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 80: "Light showers", 81: "Showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Storm with hail", 99: "Severe storm",
}


def weather_label(code: int) -> str:
    return WEATHER_CODE_LABELS.get(code, f"Code {code}")


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount using Frankfurter ECB rates (free, no key)."""
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency == to_currency:
        return {"amount": amount, "from": from_currency, "to": to_currency,
                "converted": round(amount, 2), "rate": 1.0, "date": "same-currency"}
    r = _get(
        f"{FX_URL}/latest",
        params={"amount": amount, "from": from_currency, "to": to_currency},
        timeout=_TIMEOUT,
        follow_redirects=True,
    )
    r.raise_for_status()
    data = r.json()
    rate = data["rates"][to_currency]
    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "converted": round(rate, 2),
        "rate": round(rate / amount, 4),
        "date": data.get("date"),
    }


def currency_for_country(country_code: str) -> str:
    """Best-effort local currency for a country; USD fallback."""
    code = COUNTRY_CURRENCY.get(country_code.upper(), "USD")
    if code not in supported_fx_currencies():
        return "USD"
    return code
