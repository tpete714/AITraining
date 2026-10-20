# Maintenance Schedule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each asset a fixed-interval maintenance schedule and compute its last-performed and next-due dates.

**Architecture:** A new `maintenance_schedules` table holds one row per asset. Two new routes, `PUT` and `GET /assets/{id}/maintenance-schedule`, manage it. Completed services are logged through the existing `POST /assets/{id}/maintenance` with `completed: true`, and `GET` reads the latest completed `due_at` from `maintenance_events` to compute the next due date. Existing maintenance-event endpoints are not changed.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, aiosqlite, pytest + pytest-asyncio + httpx.

**Spec:** `docs/superpowers/specs/2026-10-20-maintenance-schedule-design.md`

## Global Constraints

- Python `>=3.11`; FastAPI `>=0.115.0,<0.120.0`; Pydantic `>=2.0,<3.0`; aiosqlite `>=0.20.0,<0.21.0`.
- Tests use in-memory SQLite (`DB_PATH=":memory:"`, set in `tests/conftest.py`) and the `client` fixture.
- Asset tags match `^[A-Z]{2,4}-\d{4,6}$`.
- Status values are `active`, `maintenance`, `retired`.
- All endpoints return JSON.
- Existing `POST`/`GET /assets/{id}/maintenance` behavior must not change.
- This project is not a git repository, so there are no commit steps. Each task ends with a test run instead.

---

### Task 1: Add the `maintenance_schedules` table

**Files:**
- Modify: `src/database.py:35-43` (add a `CREATE TABLE` after the `maintenance_events` block)
- Test: `tests/test_maintenance_schedule.py` (create)

**Interfaces:**
- Consumes: `create_schema(db)` from `src/database.py`
- Produces: table `maintenance_schedules(asset_id INTEGER PRIMARY KEY REFERENCES assets(id), task TEXT NOT NULL, interval_days INTEGER NOT NULL CHECK (interval_days > 0))`

- [ ] **Step 1: Write the failing test**

Create `tests/test_maintenance_schedule.py`:

```python
import aiosqlite
import pytest

from src.database import create_schema


@pytest.mark.asyncio
async def test_create_schema_creates_maintenance_schedules_table():
    async with aiosqlite.connect(":memory:") as db:
        await create_schema(db)
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'maintenance_schedules'"
        )
        assert await cursor.fetchone() is not None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_maintenance_schedule.py::test_create_schema_creates_maintenance_schedules_table -v`
Expected: FAIL with `assert None is not None`

- [ ] **Step 3: Write the minimal implementation**

In `src/database.py`, inside `create_schema`, add this block directly after the `maintenance_events` `CREATE TABLE` block and before the `# Seed default locations if empty` comment:

```python
    await db.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            asset_id INTEGER PRIMARY KEY REFERENCES assets(id),
            task TEXT NOT NULL,
            interval_days INTEGER NOT NULL CHECK (interval_days > 0)
        )
    """)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_maintenance_schedule.py::test_create_schema_creates_maintenance_schedules_table -v`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: all existing tests still PASS.

---

### Task 2: Add request and response schemas

**Files:**
- Modify: `src/schemas.py` (append after `MaintenanceEventOut`)

**Interfaces:**
- Consumes: nothing new
- Produces:
  - `MaintenanceScheduleIn(task: str, interval_days: int)`; `task` is 1–500 chars, `interval_days` > 0
  - `MaintenanceScheduleOut(asset_id: int, task: str, interval_days: int, last_performed_at: Optional[str], next_due_at: Optional[str])`

This task has no test of its own. Its behavior is covered by the endpoint tests in Tasks 3 and 4.

- [ ] **Step 1: Add the schemas**

Append to `src/schemas.py`:

```python
class MaintenanceScheduleIn(BaseModel):
    task: str = Field(..., min_length=1, max_length=500)
    interval_days: int = Field(..., gt=0)

class MaintenanceScheduleOut(BaseModel):
    asset_id: int
    task: str
    interval_days: int
    last_performed_at: Optional[str] = None
    next_due_at: Optional[str] = None
```

- [ ] **Step 2: Run the full suite**

Run: `pytest -v`
Expected: all tests still PASS (the new classes are unused until Task 3).

---

### Task 3: `PUT /assets/{id}/maintenance-schedule` (set or replace)

**Files:**
- Modify: `src/main.py` (import the new schema; add the route after `list_maintenance_events`, before the `# Serve the static dashboard UI` comment)
- Test: `tests/test_maintenance_schedule.py` (append)

**Interfaces:**
- Consumes: `MaintenanceScheduleIn`, `MaintenanceScheduleOut` (Task 2); `_require_asset(asset_id, db)` already in `src/main.py`
- Produces: route `PUT /assets/{asset_id}/maintenance-schedule` returning `MaintenanceScheduleOut` with 200

The `GET` response includes `last_performed_at` and `next_due_at`. PUT does not compute them. It returns `last_performed_at=None` and `next_due_at=None`. Task 4 fills them in for GET.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_maintenance_schedule.py`:

```python
async def _create_asset(client, tag="PLC-0001", installed_date=None):
    payload = {"name": "CompactLogix 5380", "asset_tag": tag, "category": "plc"}
    if installed_date is not None:
        payload["installed_date"] = installed_date
    r = await client.post("/assets", json=payload)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_put_schedule_creates_schedule(client):
    asset_id = await _create_asset(client)
    r = await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    assert r.status_code == 200
    assert r.json() == {
        "asset_id": asset_id,
        "task": "Quarterly inspection",
        "interval_days": 90,
        "last_performed_at": None,
        "next_due_at": None,
    }


@pytest.mark.asyncio
async def test_put_schedule_replaces_existing_schedule(client):
    asset_id = await _create_asset(client)
    await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    r = await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Yearly calibration", "interval_days": 365},
    )
    assert r.status_code == 200
    assert r.json()["task"] == "Yearly calibration"
    assert r.json()["interval_days"] == 365


@pytest.mark.asyncio
@pytest.mark.parametrize("interval", [0, -5])
async def test_put_schedule_rejects_non_positive_interval(client, interval):
    asset_id = await _create_asset(client)
    r = await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Inspection", "interval_days": interval},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_put_schedule_asset_not_found(client):
    r = await client.put(
        "/assets/9999/maintenance-schedule",
        json={"task": "Inspection", "interval_days": 30},
    )
    assert r.status_code == 404
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_maintenance_schedule.py -v`
Expected: the four `put_schedule` tests FAIL with 404 or 405 (route not defined).

- [ ] **Step 3: Write the minimal implementation**

In `src/main.py`, add the two new schema names to the `from .schemas import (...)` block:

```python
    MaintenanceScheduleIn,
    MaintenanceScheduleOut,
```

Then add this route after `list_maintenance_events` and before the `# Serve the static dashboard UI` comment:

```python
@app.put(
    "/assets/{asset_id}/maintenance-schedule",
    response_model=MaintenanceScheduleOut,
)
async def set_maintenance_schedule(
    asset_id: int,
    body: MaintenanceScheduleIn,
    db: aiosqlite.Connection = Depends(get_db),
):
    await _require_asset(asset_id, db)
    await db.execute(
        "INSERT INTO maintenance_schedules (asset_id, task, interval_days) "
        "VALUES (?, ?, ?) "
        "ON CONFLICT(asset_id) DO UPDATE SET "
        "task = excluded.task, interval_days = excluded.interval_days",
        (asset_id, body.task, body.interval_days),
    )
    await db.commit()
    return {
        "asset_id": asset_id,
        "task": body.task,
        "interval_days": body.interval_days,
        "last_performed_at": None,
        "next_due_at": None,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_maintenance_schedule.py -v`
Expected: all four `put_schedule` tests PASS.

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: all tests PASS.

---

### Task 4: `GET /assets/{id}/maintenance-schedule` (with due dates)

**Files:**
- Modify: `src/main.py` (add `from datetime import date, timedelta` to the imports; add the GET route directly after the PUT route from Task 3)
- Test: `tests/test_maintenance_schedule.py` (append)

**Interfaces:**
- Consumes: `maintenance_schedules` table (Task 1); `MaintenanceScheduleOut` (Task 2); `_require_asset` (existing)
- Produces: route `GET /assets/{asset_id}/maintenance-schedule` returning `MaintenanceScheduleOut`, 404 if the asset or schedule is missing

Due-date rule: the base date is the latest completed `due_at` if one exists, otherwise `installed_date`. `next_due_at` is the base date plus `interval_days`, or `null` if there is no base date. `installed_date` is not validated when assets are created, so this assumes it is an ISO date (`YYYY-MM-DD`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_maintenance_schedule.py`:

```python
@pytest.mark.asyncio
async def test_get_schedule_not_found_without_schedule(client):
    asset_id = await _create_asset(client)
    r = await client.get(f"/assets/{asset_id}/maintenance-schedule")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_schedule_asset_not_found(client):
    r = await client.get("/assets/9999/maintenance-schedule")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_schedule_next_due_uses_installed_date_when_never_serviced(client):
    asset_id = await _create_asset(client, installed_date="2025-03-15")
    await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    r = await client.get(f"/assets/{asset_id}/maintenance-schedule")
    assert r.status_code == 200
    body = r.json()
    assert body["last_performed_at"] is None
    assert body["next_due_at"] == "2025-06-13"


@pytest.mark.asyncio
async def test_get_schedule_next_due_is_null_without_any_base_date(client):
    asset_id = await _create_asset(client)
    await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    r = await client.get(f"/assets/{asset_id}/maintenance-schedule")
    assert r.json()["next_due_at"] is None


@pytest.mark.asyncio
async def test_completed_service_moves_last_performed_and_next_due(client):
    asset_id = await _create_asset(client, installed_date="2025-03-15")
    await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    await client.post(f"/assets/{asset_id}/maintenance", json={
        "due_at": "2026-10-01",
        "task": "Quarterly inspection",
        "completed": True,
    })
    r = await client.get(f"/assets/{asset_id}/maintenance-schedule")
    body = r.json()
    assert body["last_performed_at"] == "2026-10-01"
    assert body["next_due_at"] == "2026-12-30"


@pytest.mark.asyncio
async def test_incomplete_event_does_not_count_as_performed(client):
    asset_id = await _create_asset(client, installed_date="2025-03-15")
    await client.put(
        f"/assets/{asset_id}/maintenance-schedule",
        json={"task": "Quarterly inspection", "interval_days": 90},
    )
    await client.post(f"/assets/{asset_id}/maintenance", json={
        "due_at": "2026-10-01",
        "task": "Quarterly inspection",
        "completed": False,
    })
    r = await client.get(f"/assets/{asset_id}/maintenance-schedule")
    assert r.json()["last_performed_at"] is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_maintenance_schedule.py -v`
Expected: the new GET tests FAIL with 405 (route not defined for GET on this path). The PUT tests still PASS.

- [ ] **Step 3: Write the minimal implementation**

In `src/main.py`, add to the imports at the top:

```python
from datetime import date, timedelta
```

Then add this route directly after the PUT route:

```python
@app.get(
    "/assets/{asset_id}/maintenance-schedule",
    response_model=MaintenanceScheduleOut,
)
async def get_maintenance_schedule(
    asset_id: int,
    db: aiosqlite.Connection = Depends(get_db),
):
    await _require_asset(asset_id, db)
    cursor = await db.execute(
        "SELECT asset_id, task, interval_days FROM maintenance_schedules WHERE asset_id = ?",
        (asset_id,),
    )
    schedule = await cursor.fetchone()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Maintenance schedule not found")

    cursor = await db.execute(
        "SELECT MAX(due_at) FROM maintenance_events WHERE asset_id = ? AND completed = 1",
        (asset_id,),
    )
    last_performed_at = (await cursor.fetchone())[0]

    cursor = await db.execute("SELECT installed_date FROM assets WHERE id = ?", (asset_id,))
    installed_date = (await cursor.fetchone())[0]

    base = last_performed_at or installed_date
    next_due_at = None
    if base is not None:
        next_due_at = (
            date.fromisoformat(base) + timedelta(days=schedule["interval_days"])
        ).isoformat()

    return {
        "asset_id": schedule["asset_id"],
        "task": schedule["task"],
        "interval_days": schedule["interval_days"],
        "last_performed_at": last_performed_at,
        "next_due_at": next_due_at,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_maintenance_schedule.py -v`
Expected: all tests in the file PASS.

- [ ] **Step 5: Run the full suite**

Run: `pytest -v`
Expected: all tests PASS.

---

### Task 5: Document the new endpoints

**Files:**
- Modify: `README.md` (endpoint table around line 58, next to the existing `/assets/{id}/maintenance` rows)

**Interfaces:**
- Consumes: the endpoints from Tasks 3 and 4
- Produces: documentation only

- [ ] **Step 1: Read the endpoint table**

Read `README.md` lines 45–70 to match the existing table format exactly.

- [ ] **Step 2: Add two rows after the `POST /assets/{id}/maintenance` row**

Add rows in the same format as the existing rows:

```
| PUT | `/assets/{id}/maintenance-schedule` | Set or replace the asset's maintenance schedule (task, interval in days) |
| GET | `/assets/{id}/maintenance-schedule` | Get the schedule with last performed date and next due date |
```

- [ ] **Step 3: Verify**

Run: `pytest -v`
Expected: all tests PASS (docs change only).

---

## Self-Review

**Spec coverage:**
- Schedule table (one row per asset, interval > 0): Task 1, Task 3 (validation tested).
- PUT set/replace: Task 3.
- GET with `last_performed_at` and `next_due_at`: Task 4.
- Next due uses `installed_date` when nothing completed: Task 4 test.
- Logging completed services via existing POST: Task 4 test `test_completed_service_moves_last_performed_and_next_due`.
- 404 for unknown asset and missing schedule: Tasks 3 and 4.
- Invalid `interval_days` returns 422: Task 3.
- Out of scope items (performed_by, notes, /events endpoint, overdue alerts): not in any task.

**Placeholder scan:** no TBD/TODO. Every code step has the full code.

**Type consistency:** `MaintenanceScheduleIn` and `MaintenanceScheduleOut` are defined in Task 2 and used with the same names in Tasks 3 and 4. `_require_asset` is the existing helper. The schedule's `asset_id` is `INTEGER PRIMARY KEY`, and the route uses `asset_id` as the lookup key throughout.
