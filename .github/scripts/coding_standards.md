# Rockwell IT Coding Standards (Python)

Each rule below has a Bad/Good example so reviewers and refactor agents can
quote it directly.

## General

- **Python 3.11+**

  Bad:
  ```python
  # relying on features removed before 3.11
  ```
  Good:
  ```python
  # pyproject.toml: requires-python = ">=3.11"
  ```

- **Type hints on all function signatures**

  Bad:
  ```python
  def get_asset(asset_id):
      ...
  ```
  Good:
  ```python
  def get_asset(asset_id: int) -> AssetOut:
      ...
  ```

- **No bare `except:` clauses (always specify exception type)**

  Bad:
  ```python
  try:
      await db.execute(query)
  except:
      pass
  ```
  Good:
  ```python
  try:
      await db.execute(query)
  except aiosqlite.Error:
      raise HTTPException(status_code=409, detail="Insert failed")
  ```

- **No hardcoded secrets or connection strings**

  Bad:
  ```python
  DB_PATH = "postgres://admin:s3cr3t@prod-db/assets"
  ```
  Good:
  ```python
  DB_PATH = os.environ.get("DB_PATH", "assets.db")
  ```

- **Use environment variables for config**

  Bad:
  ```python
  API_KEY = "sk-ant-hardcoded-value"
  ```
  Good:
  ```python
  API_KEY = os.environ["ANTHROPIC_API_KEY"]
  ```

## FastAPI

- **Use Pydantic models for all request/response bodies**

  Bad:
  ```python
  @router.post("/assets/bulk-import")
  async def bulk_import_assets(payload: dict):
      ...
  ```
  Good:
  ```python
  class BulkImportRequest(BaseModel):
      assets: list[AssetCreate]

  @router.post("/assets/bulk-import", response_model=BulkImportResult)
  async def bulk_import_assets(payload: BulkImportRequest):
      ...
  ```

- **Use Depends() for DB connections**

  Bad:
  ```python
  async def list_assets():
      db = await aiosqlite.connect(DB_PATH)
  ```
  Good:
  ```python
  async def list_assets(db: aiosqlite.Connection = Depends(get_db)):
      ...
  ```

- **Return proper HTTP status codes (201 for create, 204 for delete, 404 for not found)**

  Bad:
  ```python
  @router.post("/assets")
  async def create_asset(body: AssetCreate):
      ...
      return asset  # defaults to 200
  ```
  Good:
  ```python
  @router.post("/assets", status_code=201)
  async def create_asset(body: AssetCreate):
      ...
  ```

- **Validate path parameters**

  Bad:
  ```python
  @router.get("/assets/{asset_id}")
  async def get_asset(asset_id):
      ...
  ```
  Good:
  ```python
  @router.get("/assets/{asset_id}")
  async def get_asset(asset_id: int):
      ...
  ```

## Database

- **Parameterized queries only (no f-string SQL)**

  Bad:
  ```python
  await db.execute(f"SELECT * FROM assets WHERE name LIKE '%{q}%'")
  ```
  Good:
  ```python
  await db.execute("SELECT * FROM assets WHERE name LIKE ?", (f"%{q}%",))
  ```

- **Foreign key constraints enforced**

  Bad:
  ```sql
  CREATE TABLE assets (location_id INTEGER)
  ```
  Good:
  ```sql
  CREATE TABLE assets (location_id INTEGER REFERENCES locations(id))
  ```

- **Indexes on frequently queried columns**

  Bad:
  ```sql
  -- no index, full table scan on every search
  SELECT * FROM assets WHERE asset_tag = ?
  ```
  Good:
  ```sql
  CREATE INDEX idx_assets_asset_tag ON assets(asset_tag);
  ```

## Testing

- **Every new endpoint needs at least 2 tests (happy path + error case)**

  Bad:
  ```python
  # bulk-import endpoint shipped with zero tests
  ```
  Good:
  ```python
  async def test_bulk_import_success(client): ...
  async def test_bulk_import_rejects_invalid_asset(client): ...
  ```

- **Use pytest fixtures for shared setup**

  Bad:
  ```python
  async def test_x():
      conn = await aiosqlite.connect(":memory:")  # repeated in every test
  ```
  Good:
  ```python
  @pytest.fixture
  async def client():
      ...
  ```

- **Async tests with pytest-asyncio**

  Bad:
  ```python
  def test_create_asset(client):
      client.post(...)  # sync call on an async client
  ```
  Good:
  ```python
  @pytest.mark.asyncio
  async def test_create_asset(client):
      await client.post(...)
  ```

## Security

- **Input validation via Pydantic (regex patterns, min/max length)**

  Bad:
  ```python
  asset_tag: str
  ```
  Good:
  ```python
  asset_tag: str = Field(..., pattern=r"^[A-Z]{2,4}-\d{4,6}$")
  ```

- **No SQL injection vectors**

  Bad:
  ```python
  query = f"INSERT INTO assets (name) VALUES ('{name}')"
  ```
  Good:
  ```python
  query = "INSERT INTO assets (name) VALUES (?)"
  await db.execute(query, (name,))
  ```

- **No secrets in code or comments**

  Bad:
  ```python
  # TODO: remove before commit -- sk-ant-abc123...
  ```
  Good:
  ```python
  # API key read from ANTHROPIC_API_KEY env var
  ```

- **Rate limiting on public endpoints (when deployed)**

  Bad:
  ```python
  @router.get("/assets/search")
  async def search_assets(q: str):
      ...  # no throttling, unbounded query cost
  ```
  Good:
  ```python
  @router.get("/assets/search", dependencies=[Depends(rate_limiter)])
  async def search_assets(q: str):
      ...
  ```
