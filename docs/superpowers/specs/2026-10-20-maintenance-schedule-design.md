# Maintenance Schedule — Design

Backlog item 1 (GitHub Issues). Adds a fixed-interval maintenance schedule to each asset and computes the next due date from completed services.

## Scope

In scope:
- One fixed-interval maintenance schedule per asset.
- Computing the last performed date and next due date.

Out of scope:
- Overdue alerts or notifications.
- Usage-based triggers (operating hours, cycle counts).
- Multiple schedules per asset.
- Recording who performed a service and notes (`performed_by`, `notes`). Can be added later as optional fields.
- The `location_id` 500 bug (backlog item 4).

## Existing behavior (unchanged)

`POST /assets/{id}/maintenance` and `GET /assets/{id}/maintenance` already create and list maintenance **events** (`due_at`, `task`, `completed`). The MCP server, `tests/test_assets.py`, `README.md`, and `training/04-mcp-server.md` depend on that behavior, so it stays as it is.

Completed services are logged through the existing `POST /assets/{id}/maintenance` with `completed: true`. For a completed event, `due_at` holds the date the service was performed.

## Data model

### `maintenance_schedules` (new)

| column          | type                | notes                                        |
|-----------------|---------------------|----------------------------------------------|
| `asset_id`      | INTEGER PRIMARY KEY | references `assets(id)`; one row per asset   |
| `task`          | TEXT NOT NULL       | e.g. "Quarterly inspection"                  |
| `interval_days` | INTEGER NOT NULL    | `CHECK (interval_days > 0)`                  |

`maintenance_events` is not changed.

**Migration:** none. `CREATE TABLE IF NOT EXISTS` creates the new table in an existing `assets.db`.

## Endpoints

### `PUT /assets/{id}/maintenance-schedule`
Sets or replaces the asset's schedule.

- Body: `{ "task": str (1–500 chars), "interval_days": int (> 0) }`
- 404 if the asset does not exist.
- 200 with the stored schedule (same shape as GET).

### `GET /assets/{id}/maintenance-schedule`
Returns the schedule and its due dates.

- Response: `{ "asset_id", "task", "interval_days", "last_performed_at", "next_due_at" }`
- `last_performed_at` is the latest `due_at` among this asset's `maintenance_events` where `completed = 1`, or `null`.
- `next_due_at` = (`last_performed_at` or `installed_date`) + `interval_days`, as an ISO date. `null` if both are missing.
- 404 if the asset does not exist or has no schedule.

## Validation

- Request bodies are validated with Pydantic models in `src/schemas.py`.
- `interval_days` must be greater than 0. Invalid input returns 422.

## Errors

- Unknown asset: 404 on both endpoints.
- No schedule on GET: 404.

## Testing

pytest with `:memory:` SQLite, per `AGENTS.md`:

- PUT creates a schedule, and a second PUT replaces it.
- `interval_days` of 0 or below returns 422.
- Unknown asset returns 404 on PUT and GET.
- GET with no schedule returns 404.
- `next_due_at` uses `installed_date` when nothing has been completed.
- After a completed event is logged via POST, `last_performed_at` and `next_due_at` update.
