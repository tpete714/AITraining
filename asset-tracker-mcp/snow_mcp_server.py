"""Custom MCP Server: ServiceNow Incidents (example for real enterprise use).

Shows the pattern for connecting to a real enterprise API.
Uses mock data for the demo, but the structure matches SNOW REST API.

Replace SNOW_INSTANCE and add real auth for production use.
"""
import json
import os
from mcp.server.mcpserver import MCPServer

# In production, these come from env vars
SNOW_INSTANCE = os.environ.get("SNOW_INSTANCE", "https://rockwell-demo.service-now.com")
SNOW_USER = os.environ.get("SNOW_USER", "")
SNOW_PASS = os.environ.get("SNOW_PASS", "")

mcp = MCPServer(
    "ServiceNow",
    description="Query ServiceNow incidents, changes, and service requests",
)

# Mock data for demo (replace with real API calls in production)
MOCK_INCIDENTS = [
    {"number": "INC0012345", "short_description": "FactoryTalk Optix crashes on dashboard load",
     "priority": "1 - Critical", "state": "In Progress", "assigned_to": "Alex Kim",
     "category": "Application", "sys_created_on": "2026-06-28 14:32:00"},
    {"number": "INC0012346", "short_description": "VPN disconnects every 30 minutes",
     "priority": "2 - High", "state": "New", "assigned_to": "Casey Martinez",
     "category": "Network", "sys_created_on": "2026-06-29 09:15:00"},
    {"number": "INC0012347", "short_description": "ERP transaction taking 30+ seconds",
     "priority": "2 - High", "state": "In Progress", "assigned_to": "Sam Patel",
     "category": "Application", "sys_created_on": "2026-06-29 11:00:00"},
    {"number": "INC0012348", "short_description": "TLS cert expired on api.rockwell.internal",
     "priority": "1 - Critical", "state": "Resolved", "assigned_to": "Taylor Brown",
     "category": "Infrastructure", "sys_created_on": "2026-06-27 08:45:00"},
    {"number": "INC0012349", "short_description": "Monthly close report query timeout",
     "priority": "3 - Medium", "state": "New", "assigned_to": "Quinn Wilson",
     "category": "Database", "sys_created_on": "2026-06-30 07:30:00"},
]


@mcp.tool()
async def get_incidents(priority: str = "", state: str = "", limit: int = 10) -> str:
    """Get ServiceNow incidents. Filter by priority (1-4) or state (New/In Progress/Resolved/Closed)."""
    results = MOCK_INCIDENTS
    if priority:
        results = [i for i in results if priority in i["priority"]]
    if state:
        results = [i for i in results if i["state"].lower() == state.lower()]
    return json.dumps(results[:limit], indent=2)


@mcp.tool()
async def get_incident(number: str) -> str:
    """Get a single incident by number (e.g. INC0012345)."""
    for inc in MOCK_INCIDENTS:
        if inc["number"] == number:
            return json.dumps(inc, indent=2)
    return f"Incident {number} not found."


@mcp.tool()
async def incident_summary() -> str:
    """Get a summary of open incidents by priority and state."""
    summary = {"total": len(MOCK_INCIDENTS), "by_priority": {}, "by_state": {}}
    for inc in MOCK_INCIDENTS:
        p = inc["priority"].split(" - ")[1]
        summary["by_priority"][p] = summary["by_priority"].get(p, 0) + 1
        s = inc["state"]
        summary["by_state"][s] = summary["by_state"].get(s, 0) + 1
    return json.dumps(summary, indent=2)


if __name__ == "__main__":
    mcp.run()
