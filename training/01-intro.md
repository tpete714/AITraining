# Step 1: Introduction

## What this training program is

A set of hands-on exercises built on the Rockwell Asset Tracker: a small
REST API plus a single-page dashboard for tracking manufacturing assets
(PLCs, sensors, drives, HMIs, robots) across plant locations. Stack:
FastAPI + SQLite (async via aiosqlite) + Pydantic v2, tested with pytest
and httpx.

The app is deliberately compact (a handful of source files, one static
dashboard page) so each exercise below stays focused on the skill it's
teaching rather than the app itself.

## What this training contains, in order

1. **Initial setup** (`02-initial-setup.md`): get the repo installed and
   the test suite passing from a fresh clone.
2. **Review + Refactor agent demo** (`03-review-refactor-demo.md`): a
   local, no-API-key exercise chaining three Claude Code subagents
   (review, refactor, PR-check) around one seeded bad file. Teaches an
   AI-assisted code review and fix workflow.
3. **Custom MCP server** (`04-mcp-server.md`): run a standalone MCP
   server that wraps the API as tools, connect it to Claude Code, and
   drive the app through natural-language tool calls instead of curl.
4. **Documentation generation** (`05-doc-generation.md`): generate
   browsable code documentation with CodeWiki.

Each step's file ends with a link to the next one. Start at
`02-initial-setup.md`.

## Repo map

| Path | Role |
|---|---|
| `src/main.py` | FastAPI app, all route handlers |
| `src/database.py` | SQLite connection, schema init, seed data |
| `src/schemas.py` | Pydantic request/response models |
| `src/static/index.html` | Dashboard UI (vanilla HTML/CSS/JS) |
| `tests/` | pytest + httpx async tests |
| `asset-tracker-mcp/` | Standalone MCP server wrapping the API (Step 3) |
| `.github/scripts/` | Review/refactor agent briefs and standards used in Step 2 |
| `AGENTS.md` | Project conventions and backlog, read by both trainees and agents |

## Next

Step 2: `02-initial-setup.md`
