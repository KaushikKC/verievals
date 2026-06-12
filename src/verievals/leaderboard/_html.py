"""Minimal, dependency-free HTML rendering for leaderboards.

Produces a self-contained page (inline CSS, no external assets) suitable for
hosting on GitHub Pages or any static host.
"""

from __future__ import annotations

from html import escape

_STYLE = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 2.5rem 1rem; font: 16px/1.5 -apple-system, BlinkMacSystemFont,
  "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1a1a1a; background: #f7f7f8;
}
.wrap { max-width: 980px; margin: 0 auto; }
h1 { font-size: 1.9rem; margin: 0 0 .25rem; }
.sub { color: #555; margin: 0 0 1.5rem; }
.meta { font-size: .85rem; color: #555; margin: 0 0 1.25rem; }
code { background: #eceef2; padding: .1rem .35rem; border-radius: 4px;
  font: 13px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; word-break: break-all; }
table { border-collapse: collapse; width: 100%; background: #fff; border-radius: 10px;
  overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
th, td { padding: .7rem .9rem; text-align: left; border-bottom: 1px solid #eee; font-size: .92rem; }
th { background: #fafafa; font-weight: 600; color: #333; }
tr:last-child td { border-bottom: none; }
.tier { font-weight: 600; padding: .15rem .55rem; border-radius: 999px; font-size: .8rem;
  white-space: nowrap; }
.reproduced { background: #d6f5dd; color: #0a7c2f; }
.verified { background: #d8e8ff; color: #1257c4; }
.signed { background: #fff2cc; color: #9a6b00; }
.self_reported { background: #ffe0e0; color: #b02020; }
.legend { margin: 1.1rem 0 0; font-size: .82rem; color: #555; }
footer { margin: 2rem 0 0; font-size: .8rem; color: #777; }
a { color: #1257c4; }
"""

_LEGEND = (
    '<span class="tier reproduced">reproduced 1.00</span> '
    '<span class="tier verified">verified 0.80</span> '
    '<span class="tier signed">signed 0.50</span> '
    '<span class="tier self_reported">self-reported 0.20</span>'
)


def e(value: object) -> str:
    """HTML-escape a value."""
    return escape(str(value))


def render_page(
    *,
    title: str,
    subtitle: str,
    root: str,
    generated_at: str,
    entry_count: int,
    table_html: str,
    show_legend: bool = False,
) -> str:
    """Wrap a table in a complete, self-contained HTML page."""
    legend = f'<p class="legend">Trust tiers: {_LEGEND}</p>' if show_legend else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<style>{_STYLE}</style>
</head>
<body>
<div class="wrap">
  <h1>{e(title)}</h1>
  <p class="sub">{e(subtitle)}</p>
  <p class="meta">Merkle root: <code>{e(root)}</code><br>
     Generated: {e(generated_at)} &middot; Entries: {e(entry_count)}</p>
  {table_html}
  {legend}
  <footer>
    Every row is backed by a signed, content-addressed record committed under the
    Merkle root above. Verify any entry yourself:
    <code>pip install verievals &amp;&amp; verievals verify &lt;record&gt;.json</code>.
  </footer>
</div>
</body>
</html>
"""
