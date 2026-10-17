#!/usr/bin/env python3
"""TripPilot MCP server — Alexa+ track entry.

Exposes the travel-concierge tools over MCP (spec 2025-11-25+, Streamable HTTP).
Implements the MCP Python SDK 2.x API (MCPServer).

Run:
    PYTHONPATH=./vendor python3 server.py
Then connect any MCP client to http://127.0.0.1:8000/mcp
(e.g. MCP Inspector: npx @modelcontextprotocol/inspector).

Port/host overridable via TRIPPILOT_HOST / TRIPPILOT_PORT.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from trippilot import tools  # noqa: E402

mcp = MCPServer("trippilot")


@mcp.tool()
def geocode_place(place_name: str) -> dict:
    """Resolve a place name to coordinates, country and timezone."""
    return tools.tool_geocode(place_name)


@mcp.tool()
def get_weather(place_name: str, start_date: str, end_date: str) -> dict:
    """Daily weather forecast for a place over YYYY-MM-DD dates (max 16-day range)."""
    return tools.tool_weather(place_name, start_date, end_date)


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert money between currencies (ISO codes) at current ECB rates."""
    return tools.tool_currency(amount, from_currency, to_currency)


@mcp.tool()
def plan_trip(destination: str, start_date: str, end_date: str,
              budget_usd: float = 1000.0,
              interests: list[str] | None = None) -> dict:
    """Plan a full trip: geocodes the destination, pulls the forecast, converts
    the budget to local currency, generates a day-by-day itinerary and packing
    list, and saves everything as a persistent trip. interests e.g.
    ["beach", "food", "culture", "nature", "adventure", "shopping", "nightlife", "relax"]."""
    return tools.tool_plan_trip(destination, start_date, end_date, budget_usd, interests)


@mcp.tool()
def get_trip(trip_id: int) -> dict:
    """Fetch a saved trip with its full itinerary, weather and notes."""
    return tools.tool_get_trip(trip_id)


@mcp.tool()
def list_trips(limit: int = 10) -> dict:
    """List saved trips (most recent first)."""
    return tools.tool_list_trips(limit)


@mcp.tool()
def add_trip_note(trip_id: int, note: str) -> dict:
    """Attach a note (booking ref, idea, reminder) to a saved trip."""
    return tools.tool_add_note(trip_id, note)


@mcp.tool()
def trip_digest(trip_id: int) -> dict:
    """One-screen brief for a trip: dates, budget, rain-adapted days, today's plan."""
    return tools.tool_trip_digest(trip_id)


@mcp.resource("trips://list")
def trips_list_resource() -> str:
    """Current saved trips as JSON (read-only view of skill memory)."""
    import json
    return json.dumps(tools.tool_list_trips(20), indent=2)


if __name__ == "__main__":
    host = os.environ.get("TRIPPILOT_HOST", "127.0.0.1")
    port = int(os.environ.get("TRIPPILOT_PORT", "8000"))
    mcp.run(transport="streamable-http", host=host, port=port)
