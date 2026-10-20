# asset-tracker-mcp

An MCP server that wraps the **Rockwell Asset Tracker** REST API (FastAPI +
SQLite). It exposes one MCP tool per REST endpoint so an MCP client (e.g. Claude
Code) can query and manage manufacturing assets, locations, and maintenance
events. It is standalone and deployable on its own — it talks to the API over
HTTP and does not import the app's source.

It runs over the **streamable-http** transport: you start the server yourself as
a long-running process, and the MCP client connects to it by URL. Nothing
spawns it for you.

## TL;DR — run both

Two terminals. The API must be up before the MCP server is useful.

```bash
# Terminal 1 - from the repo ROOT: start the API
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# Terminal 2 - from asset-tracker-mcp/: start the MCP server
pip install -e .
python server.py            # listens on http://127.0.0.1:9000/mcp
```

If port `8000` gives `[WinError 10013]` on Windows, it is reserved — use another
port (e.g. `--port 8080`) and set `API_BASE_URL` to match. The detailed steps
follow.

## Tools

| Tool | Wraps |
|------|-------|
| `check_health` | `GET /health` |
| `list_locations` | `GET /locations` |
| `list_assets` | `GET /assets?status&category` |
| `get_asset` | `GET /assets/{id}` |
| `create_asset` | `POST /assets` |
| `update_asset` | `PUT /assets/{id}` |
| `delete_asset` | `DELETE /assets/{id}` |
| `create_maintenance_event` | `POST /assets/{id}/maintenance` |
| `list_maintenance_events` | `GET /assets/{id}/maintenance` |

## Prereqs

- Python 3.11+
- `pip install mcp httpx python-dotenv` (installed automatically by the install
  step below)

## 1. Install

```bash
cd asset-tracker-mcp && pip install -e .
```

## 2. Configure

```bash
copy ".env copy.example" .env   REM cmd.exe
cp ".env copy.example" .env     # git bash
```

Environment variables (all optional, defaults shown):

| Var | Default | Purpose |
|-----|---------|---------|
| `API_BASE_URL` | `http://127.0.0.1:8000` | Where the target API is running |
| `MCP_HOST` | `127.0.0.1` | Host this MCP server binds to |
| `MCP_PORT` | `9000` | Port this MCP server listens on |

Set `API_BASE_URL` to match the port you started the API on (e.g.
`http://127.0.0.1:8080`).

## 3. Run the target API separately

From the repo root (not this folder), in its own terminal:

```bash
pip install -e ".[dev]"
uvicorn src.main:app --port 8000
```

## 4. Start the MCP server

```bash
python server.py
```

It prints its listen URL to stderr and stays running:

```
asset-tracker-mcp listening on http://127.0.0.1:9000/mcp (API_BASE_URL=http://127.0.0.1:8000)
```

Sanity check without starting the server (prints config, pings the API, exits):

```bash
python server.py --selftest
```

## 5. Register with the MCP client

Register by URL — no path to `server.py` needed:

```bash
claude mcp add --transport http asset-tracker http://127.0.0.1:9000/mcp
```

Or add it to `.mcp.json`:

```json
{
  "mcpServers": {
    "asset-tracker": {
      "type": "http",
      "url": "http://127.0.0.1:9000/mcp"
    }
  }
}
```

## 6. Verify

```bash
claude mcp list        # should show asset-tracker connected
```

## 7. Note

Restart Claude Code so the new server's tools load — a freshly registered
server is not usable in the session that registered it.

## 8. Example prompts

- "List all assets that are in maintenance status."
- "Show me the drives at the Milwaukee plant, then get details for asset 3."
- "Create a new PLC named CompactLogix 5480 with tag PLC-1099 at location 1."
- "Schedule a maintenance task for asset 3 due 2025-01-15: replace cooling fan."

## 9. Optional: HTTPS and auth

Not needed for local use. `server.py` binds to `127.0.0.1` and speaks plain
HTTP with no auth — fine when only this machine reaches it. You only need TLS
and a token if you expose the server beyond localhost (another host, a LAN, the
internet).

`server.py` itself implements neither, and the simplest way to add both without
touching the code is a reverse proxy (Caddy, nginx, Traefik) in front of it.

**Bind to localhost only, let the proxy face the network:**

```bash
# .env — keep the app private; the proxy is the only public listener
MCP_HOST=127.0.0.1
MCP_PORT=9000
```

**HTTPS + bearer-token check via Caddy** (example `Caddyfile`):

```
mcp.example.com {
    @noauth not header Authorization "Bearer {env.MCP_TOKEN}"
    respond @noauth 401

    reverse_proxy 127.0.0.1:9000
}
```

Caddy fetches a real cert automatically; nginx/Traefik work too if you prefer.

**Register the client with the HTTPS URL and the token header:**

```bash
claude mcp add --transport http asset-tracker https://mcp.example.com/mcp \
  --header "Authorization: Bearer YOUR_TOKEN"
```

Or in `.mcp.json`:

```json
{
  "mcpServers": {
    "asset-tracker": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

Keep tokens out of committed config — reference an env var or a secrets store
instead of pasting the literal value.
