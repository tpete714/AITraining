# Step 2: Initial Setup

How to set up and test the Rockwell Asset Tracker from a fresh clone (never installed, never built).

## Prerequisites

- Python 3.11+ (`pyproject.toml` sets `requires-python = ">=3.11"`)

## Steps

```bash
# 1. Confirm Python version
python --version                 # -> Python 3.11.15

# 2. Create an isolated virtual environment (pin the version confirmed above)
py -3.11 -m venv .venv           # Windows (py launcher)
python3.11 -m venv .venv         # git bash / Linux / macOS

# 3. Activate it
#    cmd.exe:
.venv\Scripts\activate.bat
#    git bash:
source .venv/Scripts/activate

# 4. Editable install with dev extras (this is the "build" step)
pip install -e ".[dev]"

# 5. Run the test suite
pytest -v
```

There is no compile step. Python is not compiled to a binary. `pip install -e ".[dev]"` is the closest thing to a build: it resolves and installs dependencies from `pyproject.toml`, registers the package so `import src` works, and links `src/` in editable mode so code edits take effect without reinstalling.

There is no `requirements.txt` in this repo; `pyproject.toml` is the single
source of dependencies (runtime deps under `[project]`, dev-only deps under
the `[project.optional-dependencies].dev` extra), and `pip install -e ".[dev]"`
installs both in one step.

## What the dependencies are

Runtime: fastapi, uvicorn[standard], aiosqlite, pydantic
Dev extras (`[dev]`): pytest, pytest-asyncio, httpx

## What pytest does here

- Discovers tests in `tests/` (`test_*.py`)
- `pyproject.toml` sets `asyncio_mode = "auto"`, so async tests run without explicit marks
- Per-test fixture in `tests/conftest.py` opens a fresh in-memory SQLite DB (`:memory:`), runs `create_schema()` which also seeds 4 locations
- The demo assets are NOT seeded in tests (`seed_assets()` is skipped by the harness); tests insert their own data via the API
- Fires async httpx calls at the FastAPI app and asserts JSON responses
- Each test gets a clean DB; no `assets.db` file is touched

## Gotcha: broken pydantic-core

If `pytest` fails on import with an environment error (not a test failure) like:

```
ImportError while loading conftest 'tests\conftest.py'.
...
E   ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

the pydantic-core compiled C extension (`.pyd`) is missing or mismatched.
`pip install` can report deps as "already satisfied" while reusing a broken
cached copy. Force a clean reinstall to pull the correct compiled wheel:

```bash
pip install --force-reinstall --no-cache-dir pydantic pydantic-core
```

## Gotcha: broken global pytest plugin autoload (Windows)

If `pytest` fails on import with an error mentioning `opentelemetry` or
`logfire` (not from this project's own dependencies), a broken global
Python package on your machine is being autoloaded as a pytest plugin.
Run the project's own venv pytest directly instead of a `pytest` found
elsewhere on your `PATH`:

```bash
./.venv/Scripts/pytest.exe -v      # Windows, from the repo root
```

## Expected passing run

```
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.14.1, logfire-4.37.0, asyncio-1.4.0
asyncio: mode=Mode.AUTO

collected N items
...
============================== N passed in 0.1Ns ==============================
```

If everything above passes, the environment is ready.

## Next

Step 3: `03-review-refactor-demo.md`
