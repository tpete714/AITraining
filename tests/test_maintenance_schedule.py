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
