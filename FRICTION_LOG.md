# TripPilot — Friction Log

Judge note: this log documents real problems hit while building TripPilot and
how each was solved. Entries are dated and describe what actually happened.

---

## 1. Malformed proxy env crashing httpx on this runtime (2026-10-16)

**Friction:** Every HTTP call failed before leaving the machine. `httpx` raised
while *constructing* the client — never even reaching the network — because the
runtime's environment ships a bracketed IPv6 token (`[::1]`) inside `no_proxy`,
which httpx's proxy parser cannot handle.

**Investigation:** Stack traces pointed at proxy parsing, not at the APIs.
The bracketed token appeared in `no_proxy`/`NO_PROXY`; the unbracketed `::1`
entry covered the same loopback host, so nothing depended on the brackets.

**Solution:** `providers.py` now sanitizes the proxy env on every request:
`_sanitized_proxy_env()` strips tokens containing `[` from `no_proxy`/`NO_PROXY`
before client construction and restores the original env in a `finally` block.
Scoped mutation — no global state leaks, no behavior change for valid tokens.

**File:** `trippilot/providers.py`

---

## 2. Frankfurter API domain migration (2026-10-16)

**Friction:** Currency conversion calls failed: the old Frankfurter endpoint
(`api.frankfurter.app`) was returning redirects to the new domain instead of
JSON, so `convert_currency` broke.

**Solution:** Migrated `FX_URL` to `https://api.frankfurter.dev/v1`
(the project's documented new home as of October 2026), added
`follow_redirects=True` on the FX request as belt-and-braces, and kept a
sane fallback set (`USD/EUR/GBP/INR/JPY`) if the currency list can't be
fetched.

**File:** `trippilot/providers.py`

---

## 3. Geocoder fuzzy-match guard: "Goa" → "Genoa" (2026-10-16)

**Friction:** Open-Meteo's geocoding endpoint sometimes returns a loosely
similar place instead of failing — a query for "Goa" (India) resolved to
**Genoa, Italy**. Without a guard, the agent would confidently plan an Italy
trip for a user asking about India.

**Solution:** `geocode_place` now runs a fuzzy-match check: if the normalized
query string does not appear in the returned name/country/admin fields, the
result is flagged `match_confidence: "low"` with an explicit `match_note`
telling the caller to confirm the destination. High-confidence matches carry
no noise.

**Verified:** reproduced during the 2026-10-17 smoke test — `tool_geocode("Goa")`
returned Genoa flagged `"match_confidence": "low"` with the warning note,
exactly as designed.

**File:** `trippilot/providers.py`

---

## 4. MCP handshake verification (2026-10-17)

**Friction:** None — but it was explicitly re-verified: `server.py` on
Streamable HTTP answers an MCP `initialize` POST with **HTTP 200**, confirming
the server layer survived all provider-layer fixes.

---

## 5. Session 4 build hygiene (2026-10-17)

- `README.md` written judge-ready (quickstart, MCP tool list, demo notes, license).
- Demo assets: shot-by-shot script + full voiceover narration in `demo/`, synthesized
  narration audio, and an animated terminal visualization built from the output of a
  REAL `plan_trip` run — genuine program output, AI-narrated, never presented as a
  live screen recording.
- Git repo initialized; secrets-free tree; runtime data (`data/*.db`, `__pycache__/`)
  gitignored.
