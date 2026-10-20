import aiosqlite
import pytest

from src.database import create_schema


async def _columns(db, table):
    cursor = await db.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in await cursor.fetchall()}


@pytest.mark.asyncio
async def test_fresh_schema_has_next_service_date_column():
    async with aiosqlite.connect(":memory:") as db:
        await create_schema(db)
        assert "next_service_date" in await _columns(db, "assets")


@pytest.mark.asyncio
async def test_create_schema_adds_column_to_existing_assets_table():
    async with aiosqlite.connect(":memory:") as db:
        await db.execute("""
            CREATE TABLE assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                asset_tag TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                location_id INTEGER,
                installed_date TEXT,
                notes TEXT
            )
        """)
        await db.execute(
            "INSERT INTO assets (name, asset_tag, category) VALUES ('Old PLC', 'PLC-0001', 'plc')"
        )
        await create_schema(db)
        assert "next_service_date" in await _columns(db, "assets")
        cursor = await db.execute("SELECT name, next_service_date FROM assets")
        row = await cursor.fetchone()
        assert row[0] == "Old PLC"
        assert row[1] is None


async def _create(client, tag="PLC-0001", **extra):
    payload = {"name": "CompactLogix 5380", "asset_tag": tag, "category": "plc", **extra}
    r = await client.post("/assets", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_with_past_date_is_overdue(client):
    asset = await _create(client, next_service_date="2020-01-01")
    assert asset["next_service_date"] == "2020-01-01"
    assert asset["is_overdue"] is True


@pytest.mark.asyncio
async def test_create_with_future_date_is_not_overdue(client):
    asset = await _create(client, next_service_date="2999-01-01")
    assert asset["next_service_date"] == "2999-01-01"
    assert asset["is_overdue"] is False


@pytest.mark.asyncio
async def test_create_without_date_is_overdue(client):
    asset = await _create(client)
    assert asset["next_service_date"] is None
    assert asset["is_overdue"] is True


@pytest.mark.asyncio
async def test_retired_asset_with_past_date_is_overdue(client):
    asset = await _create(client, status="retired", next_service_date="2020-01-01")
    assert asset["is_overdue"] is True


@pytest.mark.asyncio
async def test_create_rejects_invalid_date(client):
    r = await client.post("/assets", json={
        "name": "CompactLogix 5380", "asset_tag": "PLC-0002", "category": "plc",
        "next_service_date": "2020-13-45",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_asset_returns_is_overdue(client):
    asset = await _create(client, next_service_date="2020-01-01")
    r = await client.get(f"/assets/{asset['id']}")
    assert r.status_code == 200
    assert r.json()["is_overdue"] is True
    assert r.json()["next_service_date"] == "2020-01-01"


@pytest.mark.asyncio
async def test_put_sets_date_and_clears_it_with_null(client):
    asset = await _create(client, next_service_date="2999-01-01")
    r = await client.put(f"/assets/{asset['id']}", json={"next_service_date": "2020-01-01"})
    assert r.status_code == 200
    assert r.json()["next_service_date"] == "2020-01-01"
    assert r.json()["is_overdue"] is True

    r = await client.put(f"/assets/{asset['id']}", json={"next_service_date": None})
    assert r.status_code == 200
    assert r.json()["next_service_date"] is None
    assert r.json()["is_overdue"] is True


@pytest.mark.asyncio
async def test_put_rejects_invalid_date(client):
    asset = await _create(client)
    r = await client.put(f"/assets/{asset['id']}", json={"next_service_date": "not-a-date"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_assets_reports_is_overdue(client):
    await _create(client, tag="PLC-0001", next_service_date="2020-01-01")
    await _create(client, tag="PLC-0002", next_service_date="2999-01-01")
    r = await client.get("/assets")
    assert r.status_code == 200
    by_tag = {a["asset_tag"]: a for a in r.json()}
    assert by_tag["PLC-0001"]["is_overdue"] is True
    assert by_tag["PLC-0002"]["is_overdue"] is False


@pytest.mark.asyncio
async def test_search_assets_reports_is_overdue(client):
    await _create(client, tag="PLC-0003", next_service_date="2020-01-01", name="Searchable Drive Unit")
    r = await client.get("/assets/search", params={"q": "Searchable"})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["is_overdue"] is True
