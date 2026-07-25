#!/usr/bin/env python3
"""Render the software-track résumé to /resume.html.

Source of truth is the Markdown in the job-search tracker, so the web résumé
and the DOCX generator never drift. Run after editing that file:

    python3 build_resume.py

The page is light-on-white on purpose: a résumé gets printed and saved to PDF,
and the site's dark theme prints badly.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

SOURCE = Path.home() / "job-search-tracker" / "data" / "resume_software.md"
OUT = Path(__file__).resolve().parent / "resume.html"
TEMPLATE = Path(__file__).resolve().parent / "work-templates" / "resume.html"


def linkify(html: str) -> str:
    """Turn bare domains the résumé writes as plain text into real links."""
    replacements = {
        "iswain.dev/work": "https://iswain.dev/work/",
        "github.com/IASC-00": "https://github.com/IASC-00",
    }
    for text, href in replacements.items():
        # Only linkify a standalone mention: not already inside an anchor, and
        # not the prefix of a longer path (github.com/IASC-00/some-repo), which
        # would link half a URL and leave the rest as plain text.
        html = re.sub(
            rf"(?<!\">)(?<!/){re.escape(text)}(?![/\w])(?![^<]*</a>)",
            f'<a href="{href}">{text}</a>',
            html,
            count=1,
        )
    return html


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"résumé source not found: {SOURCE}")

    raw = SOURCE.read_text()

    # Consecutive "**Label:** ..." lines (the skills block) are separated by
    # single newlines in the source, which Markdown folds into one paragraph.
    # Give each its own paragraph so the block stays scannable.
    raw = re.sub(r"\n(\*\*[A-Z][^*]*:\*\*)", r"\n\n\1", raw)

    body = markdown.markdown(raw, extensions=["tables", "sane_lists"])

    # The <h1> and the contact line are both rendered by the page header
    # instead, so drop them from the body rather than showing them twice.
    body = re.sub(r"<h1>.*?</h1>\s*", "", body, count=1)
    body = re.sub(r"^\s*<p>[^<]*@[^<]*Philadelphia[^<]*</p>\s*", "", body, count=1)
    body = linkify(body)

    OUT.write_text(TEMPLATE.read_text().replace("{resume_body}", body))
    print(f"built {OUT.relative_to(OUT.parent)} from {SOURCE.name}")


if __name__ == "__main__":
    main()
