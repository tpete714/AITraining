"""Render repo-wiki markdown (wiki/) to HTML, with mermaid diagram support.

Two modes:
  --export   write a static wiki-html/ mirror once
  --serve    run a local server that renders each .md on request

Cross-platform (Windows/macOS/Linux). No external service - the only
dependency is the `markdown` PyPI package, installed on first use if
missing. Mermaid rendering uses a vendored, offline copy of mermaid.min.js
shipped alongside this script (assets/mermaid.min.js) - no CDN.

Usage:
    python render_html.py --export --source wiki --out wiki-html
    python render_html.py --serve --source wiki --port 8765
"""
import argparse
import html
import http.server
import os
import posixpath
import re
import shutil
import subprocess
import sys
import urllib.parse

try:
    import markdown
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "markdown"])
    import markdown

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MERMAID_JS = os.path.join(os.path.dirname(SCRIPT_DIR), "assets", "mermaid.min.js")

MD_EXTENSIONS = ["extra", "fenced_code", "tables", "toc", "sane_lists"]

# Rockwell brand tokens - matches src/static/index.html exactly so the wiki
# reads as part of the same app, not a generic doc theme.
PAGE_CSS = """
:root {
  color-scheme: light dark;
  --red: #CD163F; --red-dark: #A8112F; --red-light: #FEF2F2;
  --navy: #1B2A4A; --body: #5A6470; --caption: #8A929E;
  --border: #D8DBDF; --surface: #F6F7F8; --white: #FFFFFF;
  --bg: var(--surface); --fg: var(--body); --code-bg: #EEF0F2;
  --sidebar-bg: var(--white); --link: var(--red);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #10131a; --fg: #c7ccd4; --border: #2b3550; --code-bg: #1b2338;
    --sidebar-bg: #161d30; --surface: #10131a; --white: #1b2338;
    --red-light: #2a1620; --link: #ff6b86;
  }
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; font-family: "Barlow", -apple-system,
       "Segoe UI", Roboto, Arial, sans-serif; background: var(--bg);
       color: var(--fg); -webkit-font-smoothing: antialiased; }
header.topbar { display: flex; align-items: center; gap: 10px; height: 56px;
       padding: 0 24px; background: var(--navy); border-bottom: 3px solid var(--red); }
header.topbar .brand { color: var(--white); font-weight: 700; font-size: 18px;
       letter-spacing: -0.01em; }
header.topbar .sub { color: var(--red-light); opacity: 0.85; font-size: 13px;
       margin-left: 4px; }
.layout { display: flex; min-height: calc(100vh - 56px); }
nav.sidebar { width: 260px; flex-shrink: 0; background: var(--sidebar-bg);
       border-right: 1px solid var(--border); padding: 1.5rem 1rem; overflow-y: auto; }
nav.sidebar h3 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
       font-weight: 700; color: var(--red); margin: 1.25rem 0 0.5rem; }
nav.sidebar a { display: block; padding: 0.35rem 0.6rem; border-radius: 6px;
       border-left: 3px solid transparent; color: var(--navy); text-decoration: none;
       font-size: 0.9rem; font-weight: 500; }
nav.sidebar a:hover { background: var(--surface); }
nav.sidebar a.active { background: var(--red-light); border-left-color: var(--red);
       color: var(--red-dark); font-weight: 600; }
main { flex: 1; max-width: 900px; margin: 0 auto; padding: 2.5rem 2rem; overflow-x: auto; }
main h1, main h2, main h3 { color: var(--navy); }
main img, main pre { max-width: 100%; }
pre, code { background: var(--code-bg); border-radius: 6px; }
pre { padding: 1rem; overflow-x: auto; }
code { padding: 0.15rem 0.35rem; font-size: 0.9em; }
pre code { padding: 0; background: none; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
thead th { background: var(--navy); color: var(--white); font-weight: 700;
       text-transform: uppercase; font-size: 11px; letter-spacing: 0.04em; }
th, td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; text-align: left; }
a { color: var(--link); }
pre.mermaid { background: none; padding: 0; }
"""

PAGE_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<header class="topbar"><span class="brand">Rockwell Asset Tracker</span><span class="sub">Wiki</span></header>
<div class="layout">
<nav class="sidebar">{sidebar}</nav>
<main>
{body}
</main>
</div>
<script>{mermaid_js}</script>
<script>mermaid.initialize({{
  startOnLoad: true,
  theme: "base",
  themeVariables: {{
    primaryColor: "#FEF2F2", primaryTextColor: "#1B2A4A", primaryBorderColor: "#CD163F",
    lineColor: "#5A6470", secondaryColor: "#F6F7F8", tertiaryColor: "#FFFFFF",
    fontFamily: "Barlow, -apple-system, Segoe UI, Arial, sans-serif"
  }}
}});</script>
</body>
</html>
"""


def convert_mermaid_blocks(md_text):
    """Turn ```mermaid fenced blocks into a placeholder the HTML step restores
    as <pre class="mermaid"> (python-markdown would otherwise wrap them as a
    plain code block)."""
    pattern = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)

    def repl(m):
        code = html.escape(m.group(1).strip())
        return f'<div class="mermaid-block">{code}</div>'

    return pattern.sub(repl, md_text)


def render_body(md_text):
    pre_processed = convert_mermaid_blocks(md_text)
    body = markdown.markdown(pre_processed, extensions=MD_EXTENSIONS)
    # restore mermaid divs as <pre class="mermaid"> for mermaid.js to pick up
    body = re.sub(
        r'<p><div class="mermaid-block">(.*?)</div></p>',
        r'<pre class="mermaid">\1</pre>',
        body,
        flags=re.DOTALL,
    )
    body = re.sub(
        r'<div class="mermaid-block">(.*?)</div>',
        r'<pre class="mermaid">\1</pre>',
        body,
        flags=re.DOTALL,
    )
    return body


def discover_pages(source_dir):
    """Return (root_pages, feature_pages) as lists of relative posix paths."""
    root_pages = sorted(
        f for f in os.listdir(source_dir)
        if f.endswith(".md") and os.path.isfile(os.path.join(source_dir, f))
    )
    feature_dir = os.path.join(source_dir, "feature")
    feature_pages = []
    if os.path.isdir(feature_dir):
        feature_pages = sorted(
            f"feature/{f}" for f in os.listdir(feature_dir) if f.endswith(".md")
        )
    return root_pages, feature_pages


def build_sidebar(root_pages, feature_pages, active_rel, link_ext):
    # Relative (not absolute) hrefs: works for both a plain file:// export
    # and the http:// server, and doesn't break when a page lives one
    # directory deeper (feature/*.html) than the pages it links to.
    current_dir = posixpath.dirname(active_rel)

    def links(pages):
        out = []
        for rel in pages:
            title = os.path.splitext(os.path.basename(rel))[0]
            target = rel[:-3] + link_ext
            href = posixpath.relpath(target, current_dir) if current_dir else target
            cls = " class=\"active\"" if rel == active_rel else ""
            out.append(f'<a href="{href}"{cls}>{html.escape(title)}</a>')
        return "\n".join(out)

    parts = ["<h3>Wiki</h3>", links(root_pages)]
    if feature_pages:
        parts += ["<h3>Features</h3>", links(feature_pages)]
    return "\n".join(parts)


def render_page(source_dir, rel_path, link_ext=".html"):
    root_pages, feature_pages = discover_pages(source_dir)
    md_path = os.path.join(source_dir, rel_path)
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    body = render_body(md_text)
    sidebar = build_sidebar(root_pages, feature_pages, rel_path, link_ext)
    title = os.path.splitext(os.path.basename(rel_path))[0]
    with open(MERMAID_JS, "r", encoding="utf-8") as f:
        mermaid_js = f.read()
    return PAGE_TEMPLATE.format(
        title=title, css=PAGE_CSS, sidebar=sidebar, body=body, mermaid_js=mermaid_js
    )


def export_static(source_dir, out_dir):
    root_pages, feature_pages = discover_pages(source_dir)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    os.makedirs(os.path.join(out_dir, "feature"), exist_ok=True)

    all_pages = root_pages + feature_pages
    if not all_pages:
        print(f"No markdown pages found under {source_dir}/", file=sys.stderr)
        return

    for rel in all_pages:
        html_out = render_page(source_dir, rel, link_ext=".html")
        out_path = os.path.join(out_dir, rel[:-3] + ".html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_out)

    # index.html mirrors the first root page (01-overview.md) if present
    if root_pages:
        first = render_page(source_dir, root_pages[0], link_ext=".html")
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(first)

    print(f"Exported {len(all_pages)} page(s) to {out_dir}/")


def make_handler(source_dir):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = urllib.parse.unquote(self.path.lstrip("/"))
            if path == "" or path == "index.html":
                root_pages, _ = discover_pages(source_dir)
                if not root_pages:
                    self.send_error(404, "No wiki pages found")
                    return
                rel = root_pages[0]
            elif path.endswith(".html"):
                rel = path[:-5] + ".md"
            else:
                rel = path

            full = os.path.join(source_dir, rel)
            if not os.path.isfile(full):
                self.send_error(404, f"Not found: {rel}")
                return

            body = render_page(source_dir, rel, link_ext=".html").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    return Handler


def serve(source_dir, port):
    handler = make_handler(source_dir)
    server = http.server.HTTPServer(("127.0.0.1", port), handler)
    print(f"Serving {source_dir}/ live at http://127.0.0.1:{port}/ (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--export", action="store_true", help="write a static HTML mirror")
    mode.add_argument("--serve", action="store_true", help="run a local live-render server")
    parser.add_argument("--source", default="wiki", help="markdown source dir (default: wiki)")
    parser.add_argument("--out", default="wiki-html", help="export output dir (default: wiki-html)")
    parser.add_argument("--port", type=int, default=8765, help="serve port (default: 8765)")
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        print(f"Source directory not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    if args.export:
        export_static(args.source, args.out)
    else:
        serve(args.source, args.port)


if __name__ == "__main__":
    main()
