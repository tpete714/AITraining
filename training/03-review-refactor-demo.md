# Step 3: Review + Refactor Agent Demo

**Status: built and proven.** A live dry run of all three stages passed
end to end (review flagged 4 CRITICAL findings + zero tests, refactor
fixed all of them and added 6 tests, 20/20 suite passing, PR-check
re-reviewed from scratch and approved). The repo has been reset back to
its "ready to demo" state afterward, so running the sequence below
reproduces that same result live.

Local-only, no GitHub, no separate Anthropic API key. All three agent
stages run as Claude Code subagents inside a live session (using the
Agent tool), reusing this session's model access instead of a second
key. Only the code-seeding step is a plain Python script with no AI
involved.

## What's what (plain-English map)

Three different kinds of thing are involved. Mixing them up is the usual
source of confusion:

| Kind | Examples | What it is |
|---|---|---|
| **Setup script** | `setup_review_refactor_lab.py` | Plain Python, no AI. Run once with `python`. Writes the bad `src/bulk_import.py` and wires it into `src/main.py`. Not runnable on its own after that (don't `python src/bulk_import.py` — it's a FastAPI router module, not an entrypoint; it'll fail with a relative-import error). |
| **Agent brief** | `review-brief.md`, `refactor-brief.md`, `pr-check-brief.md` | Static instructions, not code. Never run directly. You hand one to the Agent tool as its task inside a live Claude Code session. |
| **Run output** | `docs/pr-pipeline/review-comments.md`, `pr-description.md`, `review-comments-after.md`, `deploy-status.md` (each also written as a matching `.html`) | Don't exist until a subagent writes them. Each is produced by exactly one brief (see Pipeline below) and consumed by the next stage. |

`docs/pr-pipeline/review-comments.md` specifically: output of the **review**
subagent only. Verdict + findings by severity + tests/security notes.
Doesn't exist until you've dispatched the review-brief subagent at least
once. The refactor subagent reads it to know what to fix; it never edits
code itself.

Also: the existing suite passing (`tests\test_assets.py ... 9 passed`) is
expected and means nothing about `bulk_import.py`'s planted bugs — that
file has zero tests of its own until the refactor subagent writes
`tests/test_bulk_import.py`. The bugs (SQL injection, bare except, etc.)
are caught by the review subagent *reading* the code, not by running tests.

### Exact prompts to type in the Claude Code session

No slash command for this — just plain English, one per stage, waiting for
the previous stage's output before dispatching the next:

```
Dispatch a subagent using the brief at .github/scripts/agent-briefs/review-brief.md, target file src/bulk_import.py.
```

Check `docs/pr-pipeline/review-comments.md` (expect verdict `request_changes`), then:

```
Dispatch a subagent using the brief at .github/scripts/agent-briefs/refactor-brief.md. docs/pr-pipeline/review-comments.md already exists.
```

Check `pytest -v` passes and `docs/pr-pipeline/pr-description.md` exists, then:

```
Dispatch a subagent using the brief at .github/scripts/agent-briefs/pr-check-brief.md. The fixed file and docs/pr-pipeline/pr-description.md already exist.
```

## Why there are several .md files here

Two different kinds of markdown are involved, and they're not the same
thing:

1. **The actual deliverable** (read this list, nothing else, to run the
   demo): `.github/scripts/coding_standards.md` and the three files in
   `.github/scripts/agent-briefs/`. These are permanent, checked-in
   content the pipeline reads every time it runs.
2. **Run output** (regenerated fresh every time you run the sequence,
   not checked in, safe to delete between runs): `review-comments.md`,
   `pr-description.md`, `review-comments-after.md`, `deploy-status.md`
   (plus a matching `.html` for each) under `docs/pr-pipeline/`, plus the
   refactor's edits to `src/bulk_import.py` and its new
   `tests/test_bulk_import.py`. None of these exist in the repo right
   now, only during/after a run.

This file is the third kind: a one-time design/runbook doc, kept here as
the single source of truth for how to run the demo. There's also an
implementation plan under `docs/superpowers/plans/` from when this was
built; that's a process record, not something a trainer running the demo
needs to open.

## Pipeline

```
setup_review_refactor_lab.py   (plain Python, no AI)
        |
        v
src/bulk_import.py  (bad code: f-string SQL, bare except, no types, no tests)
        |
        v
[Review subagent]  -->  docs/pr-pipeline/review-comments.md (+ .html)
        |
        v
[Refactor subagent]  -->  fixed src/bulk_import.py
                      -->  tests/test_bulk_import.py
                      -->  pytest run
                      -->  docs/pr-pipeline/pr-description.md (+ .html)  (simulated PR)
        |
        v
[PR-check subagent]  -->  docs/pr-pipeline/review-comments-after.md (+ .html)
        |
        v
verdict=approve AND tests pass?
    yes -> writes "Dev Deploy Complete" block to docs/pr-pipeline/deploy-status.md (+ .html)
    no  -> writes simulated Change-Request text to docs/pr-pipeline/deploy-status.md (+ .html)
```

## Components (the permanent deliverable)

| File | Responsibility |
|---|---|
| `.github/scripts/setup_review_refactor_lab.py` | Writes `src/bulk_import.py` (bad code) and wires its router into `src/main.py`. Only non-AI piece. Safe to re-run (idempotent). |
| `.github/scripts/sample_bulk_import_target.py` | Holds the actual bad-code text (`BULK_IMPORT_FILE_CONTENT`) that the setup script writes to `src/bulk_import.py`. Not run directly, only imported by the setup script. |
| `.github/scripts/coding_standards.md` | Every rule has an inline Bad/Good code snippet. Read directly by every subagent below. |
| `.github/scripts/agent-briefs/review-brief.md` | Task text for the **review subagent**: read the bad file + standards + `AGENTS.md`, write `docs/pr-pipeline/review-comments.md` (+ `.html`) with a verdict. |
| `.github/scripts/agent-briefs/refactor-brief.md` | Task text for the **refactor subagent**: read the bad file + `docs/pr-pipeline/review-comments.md` + standards + `AGENTS.md` directly, fix everything, add tests, write `docs/pr-pipeline/pr-description.md` (+ `.html`). |
| `.github/scripts/agent-briefs/pr-check-brief.md` | Task text for the **PR-check subagent**: re-review the fix from scratch, write `docs/pr-pipeline/review-comments-after.md` (+ `.html`), then a simulated deploy or Change-Request in `docs/pr-pipeline/deploy-status.md` (+ `.html`). |

Each brief is a static prompt file, dispatched as-is via the Agent tool
rather than typed fresh each time.

### Not part of this lab (different demo, still live elsewhere)

`.github/scripts/` also holds files for a separate, unrelated demo: the
real GitHub Actions PR-review flow (`pr_review_agent.py`, run by
`.github/workflows/pr-review.yml` on actual PRs, needs an
`ANTHROPIC_API_KEY`) and its local no-GitHub preview
(`demo_review_local.py`, using the sample diff in `sample_bad_pr.py`).
These three are real and used, just not by the sequence in this doc — the
Step 3 lab never calls them. Don't confuse them with the briefs above.

(Two files that used to live here, `setup_refactor_lab.py` and
`sample_refactor_target.py`, were an earlier, superseded draft of this
same lab that targeted `src/reports.py` instead of `src/bulk_import.py`
and weren't referenced by any training doc. Removed.)

## Prerequisites

- Python venv already set up per Step 2 (`02-initial-setup.md`).
- A running Claude Code session with the Agent tool available. No
  `ANTHROPIC_API_KEY`, no Node.js/promptfoo, no `git remote`, no `gh`.

## Sequence to run

```bash
python .github/scripts/setup_review_refactor_lab.py
pytest -v          # sanity check: app still boots, no tests for bulk_import yet
```

Then, inside the Claude Code session, dispatch three subagents in order,
each one waiting for the previous artifact to exist:

1. **Review**: dispatch a subagent with `.github/scripts/agent-briefs/review-brief.md` as its task. Check `docs/pr-pipeline/review-comments.md` (and `.html`): expect verdict `request_changes`, SQL injection + missing tests flagged.
2. **Refactor**: dispatch a subagent with `.github/scripts/agent-briefs/refactor-brief.md` as its task, telling it `docs/pr-pipeline/review-comments.md` already exists. Then run `pytest -v` yourself: expect all passing, including the new `tests/test_bulk_import.py`. Check `docs/pr-pipeline/pr-description.md` (and `.html`).
3. **PR-check**: dispatch a subagent with `.github/scripts/agent-briefs/pr-check-brief.md` as its task, telling it the fixed file and `docs/pr-pipeline/pr-description.md` already exist. Check `docs/pr-pipeline/review-comments-after.md` (expect verdict `approve`) and `docs/pr-pipeline/deploy-status.md` (expect the "Dev Deploy Complete" block), both plus their `.html` counterparts.

## Resetting between runs

The run output listed above (in "Why there are several .md files here")
is disposable. To reset for another live run:

```bash
git checkout HEAD -- src/bulk_import.py

REM cmd.exe
del /f tests\test_bulk_import.py docs\pr-pipeline\review-comments.md docs\pr-pipeline\review-comments.html docs\pr-pipeline\pr-description.md docs\pr-pipeline\pr-description.html docs\pr-pipeline\review-comments-after.md docs\pr-pipeline\review-comments-after.html docs\pr-pipeline\deploy-status.md docs\pr-pipeline\deploy-status.html

# git bash
rm -f tests/test_bulk_import.py docs/pr-pipeline/review-comments.md docs/pr-pipeline/review-comments.html docs/pr-pipeline/pr-description.md docs/pr-pipeline/pr-description.html docs/pr-pipeline/review-comments-after.md docs/pr-pipeline/review-comments-after.html docs/pr-pipeline/deploy-status.md docs/pr-pipeline/deploy-status.html
```

## Not in scope for this pass

- No real `git push` / `gh pr create` / GitHub Actions trigger. That's
  the existing `pr-review.yml` + `pr_review_agent.py` flow, unchanged,
  usable later as a "go live" upgrade of this same demo (that flow does
  use its own API key, since it must run headless in CI with no Claude
  Code session attached).
- No promptfoo eval, dropped since it would need its own model access
  (a live API key) to independently verify a subagent's output, and no
  key is available for this training.

## Next

Step 4: `04-mcp-server.md`
