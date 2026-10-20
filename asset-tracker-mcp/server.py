"""MCP server wrapping the Rockwell Asset Tracker REST API.

One tool per REST endpoint. Reads the API base URL from the API_BASE_URL
environment variable (default http://127.0.0.1:8000). The target API needs no
authentication, so no secrets are read here.
"""

import json
import os
import sys

import httpx
from mcp.server.mcpserver import MCPServer

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Host/port the MCP server itself listens on (streamable-http transport).
MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.environ.get("MCP_PORT", "9000"))

mcp = MCPServer("asset-tracker")

# One shared HTTP client for all tools.
_client = httpx.Client(base_url=API_BASE_URL, timeout=10.0)


def _request(method: str, path: str, **kwargs) -> str:
    """Send a request and render the result as a readable string."""
    try:
        resp = _client.request(method, path, **kwargs)
    except httpx.ConnectError:
        return (
            f"Could not connect to the API at {API_BASE_URL}. "
            "Is the asset tracker running? Start it with "
            "`uvicorn src.main:app --port 8000`."
        )
    except httpx.HTTPError as exc:
        return f"Request failed: {exc}"

    if resp.status_code == 404:
        return f"Not found (404): {resp.text}"
    if resp.status_code == 409:
        return f"Conflict (409): {resp.text}"
    if resp.status_code >= 400:
        return f"Error {resp.status_code}: {resp.text}"

    if resp.status_code == 204 or not resp.content:
        return "OK (no content)."
    try:
        return json.dumps(resp.json(), indent=2)
    except ValueError:
        return resp.text


@mcp.tool()
def check_health() -> str:
    """Check whether the asset tracker API is up. Returns {"status": "ok"}."""
    return _request("GET", "/health")


@mcp.tool()
def list_locations() -> str:
    """List all plant locations (id, name, plant_code, building)."""
    return _request("GET", "/locations")


@mcp.tool()
def list_assets(status: str | None = None, category: str | None = None) -> str:
    """List manufacturing assets, optionally filtered.

    Args:
        status: Filter by status. One of: active, maintenance, retired.
        category: Filter by category. One of: plc, sensor, drive, hmi, robot.
    """
    params = {}
    if status is not None:
        params["status"] = status
    if category is not None:
        params["category"] = category
    return _request("GET", "/assets", params=params)


@mcp.tool()
def get_asset(asset_id: int) -> str:
    """Get a single asset by its numeric id. Returns 404 if it does not exist."""
    return _request("GET", f"/assets/{asset_id}")


@mcp.tool()
def create_asset(
    name: str,
    asset_tag: str,
    category: str,
    status: str = "active",
    location_id: int | None = None,
    installed_date: str | None = None,
    notes: str | None = None,
) -> str:
    """Create a new asset.

    Args:
        name: Human-readable asset name (1-200 chars).
        asset_tag: Unique tag matching pattern XX-NNNN (2-4 uppercase letters,
            dash, 4-6 digits), e.g. PLC-1042. Duplicate tags return 409.
        category: One of: plc, sensor, drive, hmi, robot.
        status: One of: active, maintenance, retired. Defaults to active.
        location_id: Optional numeric location id (see list_locations).
        installed_date: Optional date string, e.g. 2024-01-10.
        notes: Optional free-text notes.
    """
    body = {
        "name": name,
        "asset_tag": asset_tag,
        "category": category,
        "status": status,
        "location_id": location_id,
        "installed_date": installed_date,
        "notes": notes,
    }
    return _request("POST", "/assets", json=body)


@mcp.tool()
def update_asset(
    asset_id: int,
    name: str | None = None,
    category: str | None = None,
    status: str | None = None,
    location_id: int | None = None,
    notes: str | None = None,
) -> str:
    """Update fields of an existing asset. Only provided fields change.

    Args:
        asset_id: Numeric id of the asset to update. Returns 404 if missing.
        name: New name.
        category: One of: plc, sensor, drive, hmi, robot.
        status: One of: active, maintenance, retired.
        location_id: New numeric location id.
        notes: New notes.

    Note: asset_tag and installed_date cannot be changed via this endpoint.
    """
    body = {}
    if name is not None:
        body["name"] = name
    if category is not None:
        body["category"] = category
    if status is not None:
        body["status"] = status
    if location_id is not None:
        body["location_id"] = location_id
    if notes is not None:
        body["notes"] = notes
    return _request("PUT", f"/assets/{asset_id}", json=body)


@mcp.tool()
def delete_asset(asset_id: int) -> str:
    """Delete an asset by its numeric id. Returns 404 if it does not exist."""
    return _request("DELETE", f"/assets/{asset_id}")


@mcp.tool()
def create_maintenance_event(
    asset_id: int,
    due_at: str,
    task: str,
    completed: bool = False,
) -> str:
    """Schedule a maintenance event for an asset.

    Args:
        asset_id: Numeric id of the asset. Returns 404 if the asset is missing.
        due_at: When the task is due, e.g. 2024-12-01 (non-empty string).
        task: Description of the maintenance task (1-500 chars).
        completed: Whether the task is already done. Defaults to false.
    """
    body = {"due_at": due_at, "task": task, "completed": completed}
    return _request("POST", f"/assets/{asset_id}/maintenance", json=body)


@mcp.tool()
def list_maintenance_events(asset_id: int) -> str:
    """List maintenance events for an asset, ordered by due date ascending.

    Args:
        asset_id: Numeric id of the asset. Returns 404 if the asset is missing.
    """
    return _request("GET", f"/assets/{asset_id}/maintenance")


def _selftest() -> int:
    """Sanity check without touching the stdio JSON-RPC channel.

    Prints config and the registered tools to STDERR, pings the API if it is
    reachable, then exits. Use this instead of running the bare stdio server in
    an interactive shell (typing/Enter there sends stray newlines that the
    JSON-RPC parser rejects).
    """
    print("asset-tracker-mcp self-test", file=sys.stderr)
    print(f"  API_BASE_URL = {API_BASE_URL}", file=sys.stderr)
    print(f"  API reachable: {check_health()}", file=sys.stderr)
    print("OK. Register with an MCP client to use over stdio.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    # Streamable-HTTP transport: you start this process yourself and the MCP
    # client connects over the network at http://MCP_HOST:MCP_PORT/mcp.
    print(
        f"asset-tracker-mcp listening on http://{MCP_HOST}:{MCP_PORT}/mcp "
        f"(API_BASE_URL={API_BASE_URL})",
        file=sys.stderr,
    )
    mcp.run(transport="streamable-http", host=MCP_HOST, port=MCP_PORT)
