#!/usr/bin/env python3
"""Build the /work portfolio: Markdown case studies -> HTML pages + print sheet + PDF.

Source of truth is work/*.md. Everything under work/*.html is generated —
edit the Markdown, re-run this script, never hand-edit the output.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from pathlib import Path

import markdown

VALID_STATUSES = {"live", "live-private", "demo"}
REQUIRED_SECTIONS = ["The problem", "What I built", "Result", "Stack & implementation"]


@dataclass
class CaseStudy:
    slug: str
    title: str
    one_line: str
    url: str
    status: str
    role: str
    stack: list[str]
    order: int
    sections: dict[str, str] = field(default_factory=dict)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    if not raw.startswith("---"):
        raise ValueError("missing frontmatter")
    _, fm, body = raw.split("---", 2)
    meta: dict = {}
    for line in fm.strip().splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value
    return meta, body


def parse_case_study(path: Path) -> CaseStudy:
    meta, body = _parse_frontmatter(path.read_text())
    status = meta.get("status", "")
    if status not in VALID_STATUSES:
        raise ValueError(
            f"{path.name}: status {status!r} not in {sorted(VALID_STATUSES)}"
        )

    sections: dict[str, str] = {}
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    for heading, content in zip(parts[1::2], parts[2::2]):
        sections[heading.strip()] = markdown.markdown(content.strip())

    return CaseStudy(
        slug=meta["slug"],
        title=meta["title"],
        one_line=meta["one_line"],
        url=meta["url"],
        status=status,
        role=meta.get("role", ""),
        stack=meta.get("stack", []),
        order=int(meta.get("order", 99)),
        sections=sections,
    )


def load_all(dirpath: Path) -> list[CaseStudy]:
    items = [parse_case_study(p) for p in sorted(dirpath.glob("*.md"))]
    return sorted(items, key=lambda c: c.order)


# ── Rendering ────────────────────────────────────────────────────────────────

STATUS_LABELS = {"live": "Live", "live-private": "Live · private", "demo": "Demo"}

CLIENT_SECTIONS = ["The problem", "What I built", "Result"]
TECH_SECTION = "Stack & implementation"


def _esc(text: str) -> str:
    """Escape text destined for HTML body content."""
    return html.escape(text, quote=True)


def render_page(cs: CaseStudy, template: str) -> str:
    client_html = "".join(
        f'<h2 class="section-title">{_esc(name)}</h2>{cs.sections.get(name, "")}'
        for name in CLIENT_SECTIONS
    )
    stack_tags = "".join(f'<span class="work-tag">{_esc(s)}</span>' for s in cs.stack)
    tech_html = (
        '<div class="work-tech">'
        f'<h2 class="section-title">{_esc(TECH_SECTION)}</h2>'
        f'<div class="work-tags">{stack_tags}</div>'
        f"{cs.sections.get(TECH_SECTION, '')}"
        "</div>"
    )
    return (
        template.replace("{title}", _esc(cs.title))
        .replace("{slug}", cs.slug)
        .replace("{one_line}", _esc(cs.one_line))
        .replace("{url}", _esc(cs.url))
        .replace("{role}", _esc(cs.role))
        .replace("{status_label}", STATUS_LABELS[cs.status])
        .replace("{client_html}", client_html)
        .replace("{tech_html}", tech_html)
    )


ALSO_BUILT = [
    (
        "microtools",
        "22 small AI tools that run entirely on my own hardware — no per-seat fees, "
        "and nothing leaves the machine.",
    ),
    ("Cadence", "Scheduling and habit-tracking web app."),
    (
        "AppForge",
        "Turns a plain-English description of an app into a working single-file build.",
    ),
    ("Cosmic Rift", "Browser game — physics, nine missions, and progression."),
    ("Futuristamantes", "Site build for a creative venture."),
    ("CRM demo", "Contact and pipeline tracker, live at crm.iswain.dev."),
]


def render_index(items: list[CaseStudy], template: str) -> str:
    cards = "".join(
        f'<a class="work-card" href="/work/{cs.slug}.html">'
        f'<div class="work-card-head"><h2>{_esc(cs.title)}</h2>'
        f'<span class="work-status">{STATUS_LABELS[cs.status]}</span></div>'
        f"<p>{_esc(cs.one_line)}</p>"
        '<div class="work-tags">'
        + "".join(f'<span class="work-tag">{_esc(s)}</span>' for s in cs.stack[:3])
        + "</div></a>"
        for cs in items
    )
    also = "".join(
        f"<li><strong>{_esc(name)}</strong> — {_esc(desc)}</li>"
        for name, desc in ALSO_BUILT
    )
    return template.replace("{cards}", cards).replace(
        "{also_built}", f"<ul>{also}</ul>"
    )


# ── Build ────────────────────────────────────────────────────────────────────


def main() -> None:
    root = Path(__file__).resolve().parent
    work = root / "work"
    items = load_all(work)

    def tpl(name: str) -> str:
        return (root / "work-templates" / name).read_text()

    page_tpl = tpl("page.html")
    for cs in items:
        (work / f"{cs.slug}.html").write_text(render_page(cs, page_tpl))
    (work / "index.html").write_text(render_index(items, tpl("index.html")))

    print(f"built {len(items)} case study page(s) + index")


if __name__ == "__main__":
    main()
