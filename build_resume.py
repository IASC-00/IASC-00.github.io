#!/usr/bin/env python3
"""Render the software-track résumé to /resume.html.

Content and structure both come from the Markdown in the job-search tracker,
via that repo's parser — so the web page, the DOCX and the Markdown cannot
disagree, and the section order is whatever the Markdown says it is.

    python3 build_resume.py [source.md]

The page is light-on-white on purpose: a résumé gets printed and saved to PDF,
and the site's dark theme prints badly. It sets Georgia rather than the site's
Space Grotesk/Inter, matching the DOCX ("Style 3") so the two artifacts read as
the same document. Georgia is web-safe, so the page loads no webfonts at all.
"""

from __future__ import annotations

import html
import importlib.util
import sys
from pathlib import Path

TRACKER = Path.home() / "job-search-tracker"
PARSER = TRACKER / "resume_parse.py"
DEFAULT_SOURCE = TRACKER / "data" / "resume_software.md"
OUT = Path(__file__).resolve().parent / "resume.html"
TEMPLATE = Path(__file__).resolve().parent / "work-templates" / "resume.html"


def load_parser():
    """Import resume_parse.py from the tracker repo.

    Imported rather than shelled out to: it is stdlib-only by design, so it
    needs no virtualenv, and importing keeps its exceptions intact instead of
    flattening them into a subprocess exit code.
    """
    if not PARSER.exists():
        raise SystemExit(f"résumé parser not found: {PARSER}")
    spec = importlib.util.spec_from_file_location("resume_parse", PARSER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_links(links: list[dict]) -> list[str]:
    """The meta line's links: labelled ("Live: …") or bare, anchored if a URL."""
    out = []
    for link in links:
        label = (
            f'<span class="cv-link-label">{esc(link["label"])}</span> '
            if link["label"]
            else ""
        )
        if link["href"]:
            body = f'<a href="{esc(link["href"])}">{esc(link["text"])}</a>'
        else:
            body = esc(link["text"])
        out.append(label + body)
    return out


def render_entry(entry: dict) -> str:
    """One role or project. Dates are metadata, set apart from the title."""
    parts = [
        '<article class="cv-entry">',
        '<div class="cv-entry-head">',
        f"<h3>{esc(entry['title'])}</h3>",
    ]
    if entry["dates"]:
        parts.append(f'<span class="cv-dates">{esc(entry["dates"])}</span>')
    parts.append("</div>")

    meta = (
        [f'<span class="cv-stack">{esc(entry["meta"])}</span>'] if entry["meta"] else []
    )
    meta += render_links(entry["links"])
    if meta:
        parts.append(
            '<p class="cv-meta">'
            + '<span class="cv-sep"> · </span>'.join(meta)
            + "</p>"
        )

    if entry["bullets"]:
        parts.append(
            "<ul>" + "".join(f"<li>{esc(b)}</li>" for b in entry["bullets"]) + "</ul>"
        )
    for paragraph in entry["prose"]:
        parts.append(f"<p>{esc(paragraph)}</p>")

    parts.append("</article>")
    return "".join(parts)


def render_body(data: dict) -> str:
    """Sections in the order the Markdown declares them."""
    renderers = {
        "profile": lambda: f'<p class="cv-profile">{esc(data["profile"])}</p>',
        "skills": lambda: (
            '<dl class="cv-skills">'
            + "".join(
                f"<dt>{esc(s['label'])}</dt><dd>{esc(s['value'])}</dd>"
                for s in data["skills"]
            )
            + "</dl>"
        ),
        "experience": lambda: "".join(render_entry(e) for e in data["experience"]),
        "projects": lambda: "".join(render_entry(p) for p in data["projects"]),
        "certifications": lambda: (
            '<ul class="cv-certs">'
            + "".join(f"<li>{esc(c)}</li>" for c in data["certifications"])
            + "</ul>"
        ),
    }

    out = []
    for key in data["order"]:
        render = renderers.get(key)
        if not render or not data.get(key):
            continue
        heading = data["headings"].get(key, key.title())
        out.append(
            f'<section class="cv-sec" id="{esc(key)}">'
            f"<h2>{esc(heading)}</h2>{render()}</section>"
        )
    return "\n".join(out)


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        raise SystemExit(f"résumé source not found: {source}")

    parser = load_parser()
    data = parser.parse(source)
    parser.validate(data, source.name)

    page = TEMPLATE.read_text()
    page = page.replace("{resume_body}", render_body(data))
    page = page.replace(
        "{contact}",
        " · ".join(
            f'<a href="mailto:{esc(p)}">{esc(p)}</a>'
            if "@" in p
            else f'<a href="https://{esc(p)}">{esc(p)}</a>'
            if "." in p and " " not in p
            else esc(p)
            for p in data["contact"]
        ),
    )
    OUT.write_text(page)

    print(
        f"built {OUT.name} from {source.name} — "
        f"{len(data['skills'])} skill groups, {len(data['experience'])} roles, "
        f"{len(data['projects'])} projects, {len(data['certifications'])} certifications"
    )


if __name__ == "__main__":
    main()
