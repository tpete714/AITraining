Build a standalone, separately-deployable MCP server that wraps this repo's
REST API. Do not assume a framework, language, or endpoints — discover
everything from the repo. Work in two phases and confirm Phase 1 before coding.

## Phase 1 — Discover the API (evidence only, no guessing)

Find the source of truth for the API surface, trying these in order:
1. A running server's machine-readable spec, if reachable:
   - OpenAPI/Swagger: GET /openapi.json or /swagger.json or /v3/api-docs
   - GraphQL: introspection query
2. A spec file in the repo: openapi.yaml/json, swagger.*, *.proto, GraphQL SDL,
   Postman collection, or an api-docs/ folder.
3. If no spec exists, read the route definitions in source. Detect the stack
   first (grep for framework markers), then read the router/controller files
   and the request/response model definitions. Examples of what to look for:
     - FastAPI/Flask/Django (Python): @app.route, @router, urls.py, serializers
     - Express/Nest (Node): app.get/post, @Controller, DTOs
     - Spring (Java): @RestController, @RequestMapping
     - Rails (Ruby): config/routes.rb, controllers
   Also read env/config for the base URL and auth scheme.

Output a table before writing any code: method, path, path/query params,
request body fields (+types), response shape, auth required (y/n).
Note the base URL and how the API is started (from README/Makefile/compose).
Stop and confirm this table.

## Phase 2 — Build the MCP server

Create a NEW top-level folder `mcp-server/` (rename to `<api-name>-mcp/` if the
API has an obvious name) that is independently deployable and does NOT import
from the app's source. Structure:

  <folder>/
    server.py            # or index.ts — match a language the deployer prefers;
                         # default to Python + MCPServer (mcp>=2.0) unless the repo is
                         # JS/TS-only, then use @modelcontextprotocol/sdk
    pyproject.toml       # or package.json — own deps: mcp + an HTTP client
    README.md            # runbook (see below)
    .env.example         # API_BASE_URL=... plus any auth vars discovered
    Dockerfile           # optional, for container deploy

server.py rules:
- One MCP tool per endpoint discovered in Phase 1. Tool names = verb_noun.
- Docstrings are the tool descriptions the agent reads: say what each does and
  enumerate valid enum/allowed values pulled from the schema.
- Tool params and types must match the discovered request schemas exactly.
- Read base URL from env (API_BASE_URL). If the API needs auth, read the
  token/key from env too (document in .env.example) — never hardcode secrets.
- Reuse one HTTP client. Handle 404 and connection errors gracefully, returning
  readable strings. Return JSON as indented strings.
- Standard entrypoint that starts the server over stdio.

Keep it minimal: only the tools that map to real endpoints, only the config
needed to reach the API and authenticate. No speculative features. Do not
modify the target app's source.

## README.md — complete runbook (documentation only; do NOT run these)

Write README.md with copy-paste commands covering:

1. What it is — one line, and which API it wraps.
2. Prereqs — language runtime, `pip install mcp httpx` (or npm install).
3. Install:
     cd <folder> && pip install -e .
4. Configure:
     cp .env.example .env   # set API_BASE_URL and any auth vars
5. Run the target API separately (copy the exact start command discovered
   in Phase 1, e.g. uvicorn src.main:app --port 8000).
6. Run the MCP server standalone (sanity check):
     python server.py
7. Register with the MCP client (use an absolute path):
     claude mcp add <name> -- python /abs/path/<folder>/server.py
8. Verify:
     claude mcp list        # should show <name> connected
9. Note: restart Claude Code so the new server's tools load — a freshly
   registered server is not usable in the session that registered it.
10. Example prompts to test the tools (3-4 lines).

