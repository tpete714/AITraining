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
