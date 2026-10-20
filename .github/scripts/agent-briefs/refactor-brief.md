# Refactor Subagent Brief

You are fixing a file that failed code review, then proving the fix works.

**Target file:** set by whoever dispatches this brief (e.g. `src/bulk_import.py`).
If no target file was given, ask before proceeding. Its matching test file
is `tests/test_<target module name>.py` (e.g. `src/bulk_import.py` ->
`tests/test_bulk_import.py`).

## Task

1. Read the target file: the file to fix.
2. Read `docs/pr-pipeline/review-comments.md`: the findings to fix.
3. Read `.github/scripts/coding_standards.md`: the full standards (not
   just what was flagged; fix any other violation you find against this
   doc too).
4. Read `AGENTS.md`: project conventions (asset tag pattern, status
   values, categories, test conventions).
5. Rewrite the target file fixing every CRITICAL and WARNING finding
   and every standards violation you can find: parameterized queries
   (no f-string SQL), no bare `except:`, type hints on every function
   signature, Pydantic models for request/response bodies, proper HTTP
   status codes.
6. Write the matching test file with at least 2 tests per endpoint
   (happy path + error case), following the existing test style in
   `tests/test_assets.py` (async, `pytest.mark.asyncio`, the shared
   `client` fixture).
7. Run `pytest -v` and confirm the full suite passes, including your new
   tests.
8. Write `docs/pr-pipeline/pr-description.md`:

   ```markdown
   # PR: Fix <target file> endpoints

   ## Summary
   <what you changed and why>

   ## Fixes
   - <finding title from review-comments.md>: <how you fixed it>
   - ...

   ## Tests
   <pytest command run and pass/fail count>
   ```

9. Convert that same content to `docs/pr-pipeline/pr-description.html`: a minimal
   standalone HTML page (`<html><head><title>...` with a `<style>` block
   for basic readability), headings/lists/bold mapped to real HTML tags,
   not a raw markdown dump in a `<pre>`.

## Report back

State the pytest result (X/Y passing) and which findings you fixed in
your final message.
