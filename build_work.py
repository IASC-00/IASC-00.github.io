#!/usr/bin/env python3
"""Build the /work portfolio: Markdown case studies -> HTML pages + print sheet + PDF.

Source of truth is work/*.md. Everything under work/*.html is generated —
edit the Markdown, re-run this script, never hand-edit the output.
"""

from __future__ import annotations

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
