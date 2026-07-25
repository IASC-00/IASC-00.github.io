#!/usr/bin/env python3
"""Build the /work portfolio: Markdown case studies -> HTML pages + print sheet + PDF.

Source of truth is work/*.md. Everything under work/*.html is generated —
edit the Markdown, re-run this script, never hand-edit the output.
"""

from __future__ import annotations

import datetime
import http.client
import html
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
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
    repo: str = ""  # public source URL, or "" when the source is not public
    extra_urls: list[str] = field(default_factory=list)
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


SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_case_study(path: Path) -> CaseStudy:
    meta, body = _parse_frontmatter(path.read_text())

    for key in ("slug", "title", "one_line", "url"):
        if not meta.get(key):
            raise ValueError(f"{path.name}: missing required frontmatter key {key!r}")

    slug = meta["slug"]
    if not SLUG_RE.match(slug):
        # slug becomes a filename and a URL; anything else is a path-traversal
        # or attribute-injection footgun.
        raise ValueError(f"{path.name}: slug {slug!r} must be lowercase-with-hyphens")

    status = meta.get("status", "")
    if status not in VALID_STATUSES:
        raise ValueError(
            f"{path.name}: status {status!r} not in {sorted(VALID_STATUSES)}"
        )

    sections: dict[str, str] = {}
    parts = re.split(r"^## (.+)$", body, flags=re.MULTILINE)
    for heading, content in zip(parts[1::2], parts[2::2]):
        sections[heading.strip()] = markdown.markdown(content.strip())

    unknown = [h for h in sections if h not in REQUIRED_SECTIONS]
    if unknown:
        raise ValueError(
            f"{path.name}: unrecognised section heading(s) {unknown} — "
            f"headings must be exactly {REQUIRED_SECTIONS}"
        )
    missing = [h for h in REQUIRED_SECTIONS if not sections.get(h, "").strip()]
    if missing:
        raise ValueError(f"{path.name}: missing or empty section(s) {missing}")

    order_raw = meta.get("order", "99")
    try:
        order = int(order_raw)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{path.name}: order {order_raw!r} is not a number") from e

    return CaseStudy(
        slug=slug,
        title=meta["title"],
        one_line=meta["one_line"],
        url=meta["url"],
        status=status,
        role=meta.get("role", ""),
        stack=meta.get("stack", []),
        order=order,
        repo=meta.get("repo", ""),
        extra_urls=meta.get("extra_urls", []),
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
    url_links = " ".join(
        f'<a class="txt-link" href="{_esc(u)}" target="_blank" '
        f'rel="noopener noreferrer">{_esc(u)}</a>'
        for u in [cs.url, *cs.extra_urls]
    )
    if cs.repo:
        source_html = (
            f'<a class="txt-link" href="{_esc(cs.repo)}" target="_blank" '
            f'rel="noopener noreferrer">Read the source</a>'
        )
    else:
        source_html = (
            '<span class="work-private">Private — walkthrough on request</span>'
        )

    return (
        template.replace("{title}", _esc(cs.title))
        .replace("{slug}", cs.slug)
        .replace("{url_links}", url_links)
        .replace("{source_html}", source_html)
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
        (
            "22 small AI tools that run entirely on my own hardware — "
            "no per-seat fees, and nothing leaves the machine."
        ),
    ),
    ("Cadence", "Scheduling and habit-tracking web app."),
    (
        "AppForge",
        "Turns a plain-English description of an app into a working single-file build.",
    ),
    (
        "Cosmic Rift",
        "Browser card game — nine-mission campaign, ability engine, "
        "and an opponent AI. Pre-launch.",
    ),
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
    return template.replace("{cards}", cards).replace(
        "{also_built}", f"<ul>{_also_built_items()}</ul>"
    )


def _also_built_items() -> str:
    return "".join(
        f"<li><strong>{_esc(name)}</strong> — {_esc(desc)}</li>"
        for name, desc in ALSO_BUILT
    )


def render_print(items: list[CaseStudy], template: str) -> str:
    studies = []
    for cs in items:
        body = "".join(
            f"<h3>{_esc(name)}</h3>{cs.sections.get(name, '')}"
            for name in CLIENT_SECTIONS + [TECH_SECTION]
        )
        studies.append(
            f'<article class="work-study">'
            f"<h2>{_esc(cs.title)}</h2>"
            f'<p class="work-oneline">{_esc(cs.one_line)}</p>'
            f'<p class="work-meta">{STATUS_LABELS[cs.status]} · {_esc(cs.url)}</p>'
            f"{body}</article>"
        )
    return template.replace("{studies}", "".join(studies)).replace(
        "{also_built}", _also_built_items()
    )


# ── Verification gate ────────────────────────────────────────────────────────


ALLOWED_SCHEMES = ("http", "https")


def _same_host(a: str, b: str) -> bool:
    """True if two URLs share a host, ignoring a leading www."""

    def host(u: str) -> str:
        return urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")

    return host(a) == host(b)


def _head_status(url: str, timeout: int) -> int:
    """HTTP status for url, or 0 if it could not be reached as claimed.

    Only http/https are fetched — a case study URL is always a public web
    address, so anything else (file:, ftp:, custom schemes) is an authoring
    mistake and is rejected rather than opened.

    A redirect that lands on a different host returns 0, not 200. Without this
    a lapsed domain parked on a registrar's for-sale page would still satisfy
    the gate, and the page would keep claiming the build is live.
    """
    if urllib.parse.urlparse(url).scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"refusing to fetch non-web URL: {url!r}")

    req = urllib.request.Request(  # noqa: S310 - scheme validated immediately above
        url, method="GET", headers={"User-Agent": "iswain-dev-build"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - scheme validated above
            if not _same_host(url, resp.url):
                return 0
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (OSError, http.client.HTTPException):
        # Unreachable host, DNS failure, timeout, malformed response — all mean
        # "this link does not work", which verify_urls treats as a build failure.
        return 0


def verify_urls(items: list[CaseStudy], timeout: int = 15) -> list[tuple[str, int]]:
    """Every URL a case study claims is live must return 200 on its own host.

    Covers extra_urls and the source repo too, so a study that asserts several
    running apps — or links code a reader is invited to read — has every one of
    them checked rather than just the headline link.
    """
    failures = []
    seen: set[str] = set()
    for cs in items:
        for url in [cs.url, *cs.extra_urls, *([cs.repo] if cs.repo else [])]:
            if url in seen:
                continue
            seen.add(url)
            code = _head_status(url, timeout)
            if code != 200:
                failures.append((url, code))
    return failures


# ── PDF ──────────────────────────────────────────────────────────────────────

CHROME_CANDIDATES = ("google-chrome", "chromium", "chromium-browser")
MIN_PDF_BYTES = 20_000  # a blank Chrome PDF is ~1KB; the real one is >100KB


def _find_chrome() -> str:
    """Absolute path to a Chrome binary, or raise with a usable message."""
    for name in CHROME_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit(
        "no Chrome binary found (tried: "
        + ", ".join(CHROME_CANDIDATES)
        + ") — the PDF export needs one"
    )


def export_pdf(html_path: Path, out_path: Path) -> None:
    """Render html_path to a PDF, and confirm a real file came out the far side.

    Headless Chrome exits 0 in cases where it wrote nothing usable, so the
    build checks the artifact rather than trusting the return code.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603 - absolute binary from _find_chrome, fixed args, no shell
        [
            _find_chrome(),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_path}",
            html_path.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    if not out_path.exists() or out_path.stat().st_size < MIN_PDF_BYTES:
        size = out_path.stat().st_size if out_path.exists() else 0
        raise SystemExit(
            f"PDF export produced {size} bytes at {out_path} — expected at least "
            f"{MIN_PDF_BYTES}. Chrome exited cleanly but wrote nothing usable."
        )


# ── Build ────────────────────────────────────────────────────────────────────


def main() -> None:
    root = Path(__file__).resolve().parent
    work = root / "work"
    items = load_all(work)

    def tpl(name: str) -> str:
        return (root / "work-templates" / name).read_text()

    # Verify before writing anything, so a dead link never reaches the output.
    failures = verify_urls(items)
    if failures:
        detail = ", ".join(f"{url} -> {code}" for url, code in failures)
        raise SystemExit(
            f"URL verification failed: {detail}\n"
            "Cut the case study rather than softening its wording."
        )

    page_tpl = tpl("page.html")
    for cs in items:
        (work / f"{cs.slug}.html").write_text(render_page(cs, page_tpl))
    (work / "index.html").write_text(render_index(items, tpl("index.html")))
    print_path = work / "print.html"
    print_path.write_text(render_print(items, tpl("print.html")))

    pdf_path = (
        Path.home()
        / "Desktop/ISDev Projects/09_Live_Products/Work_Portfolio"
        / f"Ian_Swain_Portfolio_{datetime.date.today():%Y-%m-%d}.pdf"
    )
    export_pdf(print_path, pdf_path)

    print(f"built {len(items)} case study page(s) + index")
    print(f"pdf -> {pdf_path}")


if __name__ == "__main__":
    main()
