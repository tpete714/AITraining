"""Sample 'bad' code to use as a demo PR diff.

This file intentionally has issues the AI reviewer should catch.
DO NOT merge this file. It exists for training purposes only.

Paste this diff into the demo to show how the agent catches problems.
"""

# --- Simulated diff: adds a bulk import endpoint with several issues ---

SAMPLE_DIFF = '''
diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -85,3 +85,45 @@ async def delete_asset(asset_id: int, db: aiosqlite.Connection = Depends(get_db)
     await db.commit()
     if cursor.rowcount == 0:
         raise HTTPException(status_code=404, detail="Asset not found")
+
+
+@app.post("/assets/bulk-import")
+async def bulk_import(data: dict, db: aiosqlite.Connection = Depends(get_db)):
+    """Import multiple assets from a dict payload."""
+    imported = []
+    for item in data.get("assets", []):
+        name = item["name"]
+        tag = item["asset_tag"]
+        cat = item.get("category", "other")
+        # BUG: SQL injection - using f-string instead of parameterized query
+        query = f"INSERT INTO assets (name, asset_tag, category, status) VALUES ('{name}', '{tag}', '{cat}', 'active')"
+        try:
+            await db.execute(query)
+            imported.append(tag)
+        except:
+            pass  # BUG: bare except, silently swallows errors
+    await db.commit()
+    return {"imported": imported, "count": len(imported)}
+
+
+@app.get("/assets/search")
+async def search_assets(q: str, db: aiosqlite.Connection = Depends(get_db)):
+    """Search assets by name."""
+    # BUG: SQL injection via string concatenation
+    query = "SELECT * FROM assets WHERE name LIKE '%" + q + "%'"
+    cursor = await db.execute(query)
+    rows = await cursor.fetchall()
+    return [dict(r) for r in rows]
+
+
+DB_PASSWORD = "rockwell_admin_2026"  # BUG: hardcoded secret
+
+
+@app.get("/debug/db")
+async def debug_db(db: aiosqlite.Connection = Depends(get_db)):
+    """Dump all tables for debugging."""
+    # BUG: exposes internal data, no auth check
+    cursor = await db.execute("SELECT sql FROM sqlite_master")
+    rows = await cursor.fetchall()
+    return {"schema": [dict(r) for r in rows]}
'''

# Issues the reviewer should find:
# 1. CRITICAL: SQL injection in bulk_import (f-string query)
# 2. CRITICAL: SQL injection in search_assets (string concat)
# 3. CRITICAL: Hardcoded password (DB_PASSWORD)
# 4. CRITICAL: Debug endpoint exposes DB schema, no auth
# 5. WARNING: Bare except clause in bulk_import
# 6. WARNING: No Pydantic model for bulk_import input (uses raw dict)
# 7. WARNING: No input validation on search query
# 8. NIT: "other" is not a valid category per AGENTS.md
# 9. NIT: No tests added for new endpoints
