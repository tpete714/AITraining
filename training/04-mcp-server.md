# Step 4: Custom MCP Server

`asset-tracker-mcp/` is a standalone MCP server that wraps the Rockwell
Asset Tracker REST API as MCP tools, so an MCP client (Claude Code) can
query and manage assets, locations, and maintenance events through
natural-language tool calls instead of curl. It talks to the API over
HTTP and does not import the app's source, so it can run and be deployed
independently of the API.

It runs over the streamable-http transport: you start it yourself as a
long-running process, and the client connects to it by URL. Nothing
spawns it for you.

## Tools it exposes

| Tool | Wraps |
|---|---|
| `check_health` | `GET /health` |
| `list_locations` | `GET /locations` |
| `list_assets` | `GET /assets?status&category` |
| `get_asset` | `GET /assets/{id}` |
| `create_asset` | `POST /assets` |
| `update_asset` | `PUT /assets/{id}` |
| `delete_asset` | `DELETE /assets/{id}` |
| `create_maintenance_event` | `POST /assets/{id}/maintenance` |
| `list_maintenance_events` | `GET /assets/{id}/maintenance` |

## Sequence to run

Two terminals. The API must be up before the MCP server is useful.

1. **Terminal 1, from the repo root: start the API**

   ```bash
   pip install -e ".[dev]"
   uvicorn src.main:app --reload --port 8000
   ```

   If port `8000` gives `[WinError 10013]` on Windows, it's reserved.
   Use another port (e.g. `--port 8080`) and set `API_BASE_URL` to match
   in step 2 below.

2. **Terminal 2, from `asset-tracker-mcp/`: install and configure**

   ```bash
   cd asset-tracker-mcp
   pip install -e .
   copy ".env copy.example" .env   REM cmd.exe
   cp ".env copy.example" .env     # git bash
   ```

   `.env` variables (all optional, defaults shown):

   | Var | Default | Purpose |
   |---|---|---|
   | `API_BASE_URL` | `http://127.0.0.1:8000` | Where the target API is running |
   | `MCP_HOST` | `127.0.0.1` | Host this MCP server binds to |
   | `MCP_PORT` | `9000` | Port this MCP server listens on |

3. **Start the MCP server** (same terminal, still in `asset-tracker-mcp/`)

   ```bash
   python server.py
   ```

   It prints its listen URL and stays running:

   ```
   asset-tracker-mcp listening on http://127.0.0.1:9000/mcp (API_BASE_URL=http://127.0.0.1:8000)
   ```

   Sanity check without starting the server (prints config, pings the API, exits):

   ```bash
   python server.py --selftest
   ```

4. **Register it with Claude Code**

   ```bash
   claude mcp add --transport http asset-tracker http://127.0.0.1:9000/mcp
   ```

5. **Restart Claude Code**, then verify:

   ```bash
   claude mcp list        # should show asset-tracker connected
   ```

   A freshly registered server's tools don't load into the session that
   registered it; the restart is required.

## Try it

With the server registered and Claude Code restarted, ask things like:

- "List all assets that are in maintenance status."
- "Show me the drives at the Milwaukee plant, then get details for asset 3."
- "Create a new PLC named CompactLogix 5480 with tag PLC-1099 at location 1."
- "Schedule a maintenance task for asset 3 due 2025-01-15: replace cooling fan."

## Out of scope for this step

HTTPS and auth (reverse proxy, bearer tokens) for exposing this server
beyond localhost. Not needed for local training; see
`asset-tracker-mcp/README.md` if you need it later.

## Next

Step 5: `05-doc-generation.md`
