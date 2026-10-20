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
