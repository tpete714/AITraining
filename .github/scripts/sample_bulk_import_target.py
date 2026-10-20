"""Sample bad code for the review + refactor agent training demo.

Deliberately violates .github/scripts/coding_standards.md:
- f-string SQL (SQL injection) in both endpoints
- bare `except:` swallowing all errors
- no Pydantic model for the bulk-import request body
- no type hints on parameters/returns
- no tests
"""

BULK_IMPORT_FILE_CONTENT = '''"""Bulk import and search endpoints for assets."""
from fastapi import APIRouter, Depends
import aiosqlite

from .database import get_db

router = APIRouter()


@router.post("/assets/bulk-import")
async def bulk_import_assets(payload: dict, db=Depends(get_db)):
    assets = payload["assets"]
    imported = 0
    try:
        for a in assets:
            name = a["name"]
            tag = a["asset_tag"]
            category = a["category"]
            query = (
                f"INSERT INTO assets (name, asset_tag, category, status) "
                f"VALUES ('{name}', '{tag}', '{category}', 'active')"
            )
            await db.execute(query)
            imported += 1
        await db.commit()
    except:
        pass
    return {"imported": imported}


@router.get("/assets/search")
async def search_assets(q: str = "", db=Depends(get_db)):
    query = f"SELECT * FROM assets WHERE name LIKE '%{q}%' OR asset_tag LIKE '%{q}%'"
    cursor = await db.execute(query)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
'''
