# Step 5: Documentation Generation

This step uses [CodeWiki](https://pypi.org/project/codewiki/), not the
`openwiki/` folder in this repo. `openwiki/` is a separate, older,
hand-written documentation effort unrelated to this step; ignore it here.
CodeWiki is an installable tool that reads the codebase itself and
generates a browsable, structured wiki from it (`docs/overview.md`,
`docs/index.html`, and supporting JSON module-tree files).

## Prerequisite

```bash
pip install codewiki
```

(Already installed in this environment; `pip show codewiki` confirms it.)

## Generate the docs

From the repo root:

```bash
codewiki generate --github-pages
```

This writes straight into the working tree's `docs/` directory. Add
`--create-branch` instead if you want the output written to a new
`docs/codewiki-*` git branch rather than the current one.

`docs/` in this repo already has output from a prior run
(`overview.md`, `index.html`, `module_tree.json`, `metadata.json`,
`first_module_tree.json`); re-running the command above regenerates it
to reflect the current code.

## View the docs

`docs/index.html` loads its Markdown and JSON at runtime with `fetch()`,
which browsers block over the `file://` protocol (CORS). Serve the
folder over HTTP instead of opening the file directly:

```bash
cd docs
python -m http.server 8001
```

Then open `http://localhost:8001`.

## What you get

A code-structure browser: a generated overview of the codebase plus a
navigable module tree, useful for orienting in a codebase you didn't
write, distinct from the hand-authored business/architecture context in
`AGENTS.md` and this `training/` folder.
