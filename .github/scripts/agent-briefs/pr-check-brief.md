# PR-Check Subagent Brief

You are the reviewer cross-checking a fix before it "ships."

**Target file:** set by whoever dispatches this brief (e.g. `src/bulk_import.py`),
the same one from the original review/refactor stages. If no target file was
given, ask before proceeding.

## Task

1. Read the current target file (the fixed version).
2. Read `docs/pr-pipeline/pr-description.md`: what the refactor claims to have done.
3. Read `.github/scripts/coding_standards.md` and `AGENTS.md`: the same
   standards used in the original review.
4. Re-review the file from scratch against every rule, the same way the
   first review did: do not just trust `pr-description.md`'s claims.
5. Run `pytest -v` and confirm the suite passes.
6. Write `docs/pr-pipeline/review-comments-after.md` in the same format as the
   original review (`# Code Review: <target file>`, Verdict, Findings,
   Tests Assessment, Security Notes). Convert it to
   `docs/pr-pipeline/review-comments-after.html` too: a minimal standalone HTML page
   (`<html><head><title>...` with a `<style>` block for basic
   readability), headings/lists/bold mapped to real HTML tags, not a raw
   markdown dump in a `<pre>`.
7. Write `docs/pr-pipeline/deploy-status.md`:
   - If verdict is **approve** and pytest passed, write a simulated deploy
     confirmation:
     ```markdown
     # Dev Deploy Complete

     Branch: (local, simulated)
     App URL: https://dev-asset-tracker.rockwell-internal.example/health
     Status: All checks passed. Deployed.
     ```
   - Otherwise, write a simulated Change-Request:
     ```markdown
     # Change Request: <target file>

     **Tests:** <passed|failed>
     **Critical findings:** <count>

     ## Action Required
     - [ ] Fix: <finding title>
     - ...
     ```
   Convert this same content to `docs/pr-pipeline/deploy-status.html` too, same
   minimal-standalone-page rule as above.

## Report back

State the verdict and which of the two `deploy-status.md` branches you
wrote, in your final message.
