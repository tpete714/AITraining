---
name: repo-wiki
description: >-
  Generate and maintain a self-contained repository wiki under /wiki, with
  mermaid diagrams, covering overview+tech, architecture, integrations, db
  schema, technology, and per-feature docs. Creates the wiki if it doesn't
  exist, updates it in place if it does. Can also render the markdown to
  HTML (static export or a local live server). No external API key, no
  external service - the model does the discovery and writing itself using
  its own tools. Trigger on "generate wiki", "update wiki", "document this
  repo", "document the <feature> feature", "/repo-wiki", "serve the wiki",
  "render wiki to html".
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# repo-wiki

Build or refresh a repository wiki at `wiki/` using your own tools (Read,
Grep, Glob, Write, Edit, Bash for git/python). Do not call any external API
or require a key - you are the inference engine.

Read `reference/wiki-format.md` before writing anything. It is the source
of truth for page layout, section content, mermaid diagram types per page,
and the update-vs-create rules. Follow it precisely.

## Decide the mode first

1. **Named feature given** (e.g. "document the bulk import feature",
   "update wiki for maintenance events"): go straight to **Feature mode**.
   Do not touch root pages (`01`-`06`).
2. **No `wiki/` directory yet**: **Generate mode** - build root pages
   `01`-`06` from scratch.
3. **`wiki/` already exists, no feature named**: **Update mode** - refresh
   root pages that look stale against the current repo; leave accurate
   content alone; never touch `wiki/feature/*.md` in this mode.

## Generate mode

1. Confirm repo root. Run `git rev-parse HEAD` (capture for metadata) and
   `git log --oneline -20` for high-signal recent context. Not a git repo?
   Proceed, use empty `gitHead`.
2. Targeted discovery: `rg --files` (exclude `.git`, `node_modules`, `dist`,
   `build`, caches, `wiki/`, `wiki-html/`), entrypoints, package/config
   files, routing, data/schema files, domain folders, existing docs, tests,
   integration points (other services/servers/APIs this repo talks to or
   exposes). Short targeted reads, not exhaustive ones.
3. Write `wiki/01-overview.md` through `wiki/05-technology.md` per
   `reference/wiki-format.md`. Write `wiki/06-other.md` only if real content
   doesn't fit 01-05 - never a stub.
4. Skip `wiki/04-db-schema.md` entirely if the repo has no database.
5. Ground every claim in evidence (inline references like `` `src/main.py`
   lines 12-30` ``). Never invent files, modules, APIs, or behavior.
6. Write `wiki/.wiki-meta.json` (see format spec for exact shape).
7. Offer HTML output (see below).

## Update mode

1. Same discovery as generate mode, scoped to what changed: compare current
   repo state against what each root page claims. Use
   `git log --oneline <old-gitHead>..HEAD` from `wiki/.wiki-meta.json` if
   present to focus on what actually changed since the last run.
2. Refresh only the sections that are wrong or missing. Preserve accurate
   existing content and any inline references still valid. Do not rewrite a
   page wholesale just to touch one stale paragraph.
3. If a root page doesn't exist yet (e.g. repo grew a database since last
   run), create it now, following the same rules as generate mode.
4. Rewrite `wiki/.wiki-meta.json` with the new `updatedAt`/`gitHead`.
5. Offer HTML output (see below).

## Feature mode

1. Discover the named feature in source (routes/handlers, schema, tests,
   related docs). If you can't find it, say so - do not invent a feature
   page from guesswork.
2. `wiki/feature/<slug>.md` - `<slug>` is the feature name, kebab-case
   (e.g. `maintenance-events`, `bulk-import`).
3. If the file exists, update it the same way as an update-mode root page
   (refresh what's stale, preserve what's accurate). If it doesn't exist,
   create it per `reference/wiki-format.md`.
4. Do not touch any root page or any other feature page in this mode.
5. Update `wiki/.wiki-meta.json`'s `updatedAt` (leave `gitHead` as-is unless
   you also happened to run a root-page pass).
6. Offer HTML output (see below).

## HTML output (always offer, never assume)

After finishing any of the three modes above, ask the user:

> "Wiki written to `wiki/`. Want it rendered to HTML? I can export a static
> `wiki-html/` copy, start a local server that renders it live, or skip
> this."

Use `scripts/render_html.py` (see `reference/wiki-format.md` for its two
modes and exact invocation). Never run it unless the user says yes -
markdown under `wiki/` is the deliverable by default.

## Security & scope

- Never read or document secrets, credentials, private keys, tokens, or
  `.env` files. `.env.example` with placeholders is fine to mention by name.
- Keep all generated docs under `wiki/` (or `wiki-html/` for the HTML
  export). Don't modify source files.
- Never glob `**/*` from repo root.
