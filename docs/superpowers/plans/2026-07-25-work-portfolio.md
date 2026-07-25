# Work Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portfolio of 8 shipped case studies that renders from one Markdown source to both web pages on iswain.dev and a single attachable PDF.

**Architecture:** One Markdown file per case study in `~/portfolio/work/`, each with YAML frontmatter and four fixed body sections. A Python generator (`build_work.py`) parses them, renders through HTML templates that reuse the site's existing `style.css`, and writes an index page, eight case-study pages, and a print page. Headless Chrome converts the print page to PDF. Nothing new is added to the site's runtime — GitHub Pages serves committed HTML.

**Tech Stack:** Python 3 + `markdown` (already installed) · existing `style.css` (Space Grotesk / Inter / Space Mono) · `google-chrome --headless --print-to-pdf` (verified at `/usr/bin/google-chrome`) · pytest for generator tests.

**Spec:** `~/ISDev_Projects/06_Memory_and_Docs/HANDOFFS/SPEC_work_portfolio_2026-07-25.md`

## Global Constraints

- **Voice:** first person, past tense, outcome-led, plain. No jargon, no hype, no emoji. Matches iswain.dev ("I run the tech and operations side of your business…").
- **Author is Ian Swain.** No AI tool is named anywhere in the output — not in copy, not in a stack list, not in a commit message body.
- **No personal names** in public copy. The moving company's founder, the artist behind I AM MAJOR KEY, and OPERARI's three users are never named.
- **Under-claim by default.** No invented metrics. Where there is no verifiable number, state what shipped and that it runs.
- **Two-reader split, every page:** sections 1–3 (problem / what I built / result) are plain English and name no technologies. Section 4 (**Stack & implementation**) is visually separated and names everything. This is how `~/portfolio/CLAUDE.md`'s "no tech brand names in client-facing copy" rule and a hiring manager's needs coexist.
- **Status vocabulary is fixed:** `live` · `live-private` · `demo`. Nothing else. "Shipped", "complete", "final" do not appear.
- **Excluded entirely:** partnership/civic decks, Green Soul, the Mayor's Playbook, Philadelphia Creative Alliance, the games as case studies, `demos.iswain.dev` (returns 503).
- **No payment links.** `~/portfolio/CLAUDE.md`: no Stripe, no deposit text on the public site.
- **Deploy is `git push`** on the `~/portfolio` repo (GitHub Pages, IASC-00.github.io). Live in ~60s.

---

## File Structure

| File | Responsibility |
|---|---|
| `~/portfolio/work/<slug>.md` × 8 | Case study source — frontmatter + 4 sections. The only place content is edited. |
| `~/portfolio/work-templates/page.html` | Single case-study page shell |
| `~/portfolio/work-templates/index.html` | `/work/` index shell |
| `~/portfolio/work-templates/print.html` | All case studies concatenated for PDF |
| `~/portfolio/build_work.py` | Parse → render → write. Also the URL verification gate. |
| `~/portfolio/work-print.css` | Print-only styles (page breaks, no nav, black on white) |
| `~/portfolio/tests/test_build_work.py` | pytest suite for the generator |
| `~/portfolio/work/index.html`, `work/<slug>.html`, `work/print.html` | **Generated.** Committed so Pages serves them. |
| `~/portfolio/index.html:#work` | Modified — the four bare links become links into `/work/` |

---

### Task 1: Generator core — parse a case study

**Files:**
- Create: `~/portfolio/build_work.py`
- Create: `~/portfolio/tests/test_build_work.py`

**Interfaces:**
- Produces: `CaseStudy` dataclass with fields `slug: str`, `title: str`, `one_line: str`, `url: str`, `status: str`, `role: str`, `stack: list[str]`, `order: int`, `sections: dict[str, str]` (section heading → rendered HTML). Function `parse_case_study(path: Path) -> CaseStudy`. Function `load_all(dirpath: Path) -> list[CaseStudy]` returning items sorted by `order`.

- [ ] **Step 1: Write the failing test**

```python
# ~/portfolio/tests/test_build_work.py
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from build_work import parse_case_study, load_all, VALID_STATUSES


def test_parses_frontmatter_and_sections(tmp_path):
    md = tmp_path / "sample.md"
    md.write_text(
        "---\n"
        "slug: sample\n"
        "title: Sample Build\n"
        "one_line: A thing that runs.\n"
        "url: https://example.com\n"
        "status: live\n"
        "role: Design, build, deploy\n"
        "stack: [Flask, Postgres]\n"
        "order: 1\n"
        "---\n"
        "\n"
        "## The problem\n\nIt was broken.\n\n"
        "## What I built\n\nI fixed it.\n\n"
        "## Result\n\nIt runs.\n\n"
        "## Stack & implementation\n\nFlask on Postgres.\n"
    )
    cs = parse_case_study(md)
    assert cs.slug == "sample"
    assert cs.title == "Sample Build"
    assert cs.stack == ["Flask", "Postgres"]
    assert cs.order == 1
    assert cs.status in VALID_STATUSES
    assert "It was broken." in cs.sections["The problem"]
    assert list(cs.sections) == [
        "The problem",
        "What I built",
        "Result",
        "Stack & implementation",
    ]


def test_rejects_unknown_status(tmp_path):
    md = tmp_path / "bad.md"
    md.write_text(
        "---\nslug: b\ntitle: B\none_line: x\nurl: https://e.com\n"
        "status: shipped\nrole: r\nstack: [X]\norder: 1\n---\n\n## The problem\n\nx\n"
    )
    try:
        parse_case_study(md)
    except ValueError as e:
        assert "shipped" in str(e)
    else:
        raise AssertionError("expected ValueError for status 'shipped'")


def test_load_all_sorts_by_order(tmp_path):
    for slug, order in [("b", 2), ("a", 1)]:
        (tmp_path / f"{slug}.md").write_text(
            f"---\nslug: {slug}\ntitle: {slug}\none_line: x\nurl: https://e.com\n"
            f"status: live\nrole: r\nstack: [X]\norder: {order}\n---\n\n## The problem\n\nx\n"
        )
    assert [c.slug for c in load_all(tmp_path)] == ["a", "b"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_work'`

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
"""Build the /work portfolio: Markdown case studies -> HTML pages + print sheet."""
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
        raise ValueError(f"{path.name}: status {status!r} not in {sorted(VALID_STATUSES)}")

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: 3 passed

- [ ] **Step 5: Fix the stale path in the existing smoke test**

`tests/test_portfolio.py` line ~24 has `directory="/home/iswai/portfolio"` — a dead path on this machine, so the suite cannot run. Change to `/home/ias/portfolio`.

- [ ] **Step 6: Commit**

```bash
cd ~/portfolio
git add build_work.py tests/test_build_work.py tests/test_portfolio.py
git commit -m "feat(work): case study parser with fixed section + status validation"
```

---

### Task 2: Render one case study end-to-end

**Files:**
- Create: `~/portfolio/work-templates/page.html`
- Modify: `~/portfolio/build_work.py`
- Modify: `~/portfolio/tests/test_build_work.py`
- Create: `~/portfolio/work/i-am-major-key.md`

**Interfaces:**
- Consumes: `CaseStudy`, `load_all` from Task 1.
- Produces: `render_page(cs: CaseStudy, template: str) -> str`; `STATUS_LABELS: dict[str, str]` mapping `live` → "Live", `live-private` → "Live · private", `demo` → "Demo".

- [ ] **Step 1: Write the failing test**

```python
def test_render_page_splits_client_and_technical_halves():
    from build_work import render_page, CaseStudy

    cs = CaseStudy(
        slug="s", title="S", one_line="One line.", url="https://e.com",
        status="live", role="Design, build, deploy", stack=["Flask"], order=1,
        sections={
            "The problem": "<p>Broken.</p>",
            "What I built": "<p>Built it.</p>",
            "Result": "<p>Runs.</p>",
            "Stack & implementation": "<p>Flask.</p>",
        },
    )
    template = "<title>{title}</title>{client_html}{tech_html}{status_label}"
    html = render_page(cs, template)
    assert "Broken." in html and "Built it." in html and "Runs." in html
    assert "Flask." in html
    assert html.index("Runs.") < html.index("Flask.")  # technical half comes last
    assert "Live" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py::test_render_page_splits_client_and_technical_halves -v`
Expected: FAIL — `ImportError: cannot import name 'render_page'`

- [ ] **Step 3: Implement `render_page`**

```python
STATUS_LABELS = {"live": "Live", "live-private": "Live · private", "demo": "Demo"}

CLIENT_SECTIONS = ["The problem", "What I built", "Result"]
TECH_SECTION = "Stack & implementation"


def render_page(cs: CaseStudy, template: str) -> str:
    client_html = "".join(
        f'<h2 class="section-title">{name}</h2>{cs.sections.get(name, "")}'
        for name in CLIENT_SECTIONS
    )
    stack_tags = "".join(f'<span class="card-tag">{s}</span>' for s in cs.stack)
    tech_html = (
        '<div class="work-tech">'
        f'<h2 class="section-title">{TECH_SECTION}</h2>'
        f'<div class="card-tags">{stack_tags}</div>'
        f'{cs.sections.get(TECH_SECTION, "")}'
        "</div>"
    )
    return (
        template.replace("{title}", cs.title)
        .replace("{one_line}", cs.one_line)
        .replace("{url}", cs.url)
        .replace("{role}", cs.role)
        .replace("{status_label}", STATUS_LABELS[cs.status])
        .replace("{client_html}", client_html)
        .replace("{tech_html}", tech_html)
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: 4 passed

- [ ] **Step 5: Write `work-templates/page.html`**

Copy the `<head>` block from `index.html` (fonts, favicon, OG tags, referrer meta), swap the title/description for the case study, link `/style.css`, reuse `.nav`/`.section`/`.section-inner`/`.footer` markup. Placeholders: `{title}`, `{one_line}`, `{url}`, `{role}`, `{status_label}`, `{client_html}`, `{tech_html}`. Add a "← All work" link to `/work/`. **No CTA on this page** — the index carries the only one.

- [ ] **Step 6: Write the first case study**

`~/portfolio/work/i-am-major-key.md`. Frontmatter: `slug: i-am-major-key` · `title: I AM MAJOR KEY` · `url: https://iammajorkey.com` · `status: live` · `role: Design, build, deploy` · `stack: [WordPress, PHP, Custom theme, LiteSpeed]` · `order: 1`.

Verified facts to draw on (do not exceed them): a Philadelphia recording artist had no website. Ian built a custom one-page WordPress theme (v1.1.0) and it is live and public. Source is a git repo at `~/major-key` with a `DEPLOY.md` restore runbook and a WP-installable theme zip. `functions.php` was security-hardened. A companion plugin fixes an author-enumeration redirect at `plugins_loaded` priority 0. Host runs LiteSpeed with a 7-day full-page cache, so deploys require a cache purge — mention this as the operational detail that makes a handover real, not as a problem. **Never name the artist.**

- [ ] **Step 7: Build and eyeball**

Run: `cd ~/portfolio && python3 build_work.py && python3 -m http.server 8788 &` then open `http://localhost:8788/work/i-am-major-key.html`
Expected: page renders with site styling, technical block visually separate and below.

- [ ] **Step 8: Commit**

```bash
cd ~/portfolio
git add build_work.py tests/test_build_work.py work-templates/page.html work/i-am-major-key.md work/i-am-major-key.html
git commit -m "feat(work): render case study pages, first study live"
```

---

### Task 3: The remaining seven case studies

**Files:**
- Create: `~/portfolio/work/{exonerated-moving,operari,demo-infrastructure,decipher,automation-audit,rag-assistant,iswain-dev}.md`

**Interfaces:**
- Consumes: the frontmatter schema and four-section body from Tasks 1–2. No code changes.

Each file uses the same four sections and obeys every Global Constraint. Verified fact sheets:

- [ ] **Step 1: `exonerated-moving.md`** — order 2, `status: live`, url `https://exoneratedmovers.com`, stack `[WordPress, PHP, Custom theme, Responsive CSS]`.
  Facts: a new Philadelphia moving and logistics company built on second-chance hiring needed a site and a brand. Ian built the brand direction (navy/amber, Archivo + Inter + Space Grotesk), generated the photography locally, and built and deployed a custom WordPress theme. Live since 2026-06-20. A separate "My Story" page was added and deployed. Quote form wired through `wp_mail`. Site copy went through the owner's revisions and shipped. **Never name the founder.** Do not claim lead volume or revenue — no such number exists.

- [ ] **Step 2: `operari.md`** — order 3, `status: live-private`, url `https://operarihq.com`, stack `[FastAPI, Python, React, Vite, Tailwind, PostgreSQL, Supabase, Cloudflare R2, Docker]`.
  Facts: a small team was losing work across email, chat, and drive folders. Ian built a private operations hub — projects, tasks, contacts, invoices, file attachments, comments, an activity log, a calendar, and a workspace-grounded assistant. Every API route requires an authenticated, allowlisted user; row-level security denies by default on all tables; file storage is private and served through signed URLs. File storage was migrated off a capped free tier onto Cloudflare R2 — 233 files, zero failures. 160 backend tests pass. It is live and in daily use by its three users. Note it is private, so there is no public login — that is why there is no demo link. Do not name the users. Do not call it a product, priced, or purchasable.

- [ ] **Step 3: `demo-infrastructure.md`** — order 4, `status: live`, url `https://decipher.iswain.dev`, stack `[Docker, Docker Compose, Caddy, Let's Encrypt, Ubuntu, ufw, fail2ban]`.
  Facts: four demo apps kept going offline because free hosting tiers expired or idled out — one returned 404, another exhausted its credit. Ian moved all four onto a single virtual server: Docker Compose runs one container per app behind Caddy, which handles automatic HTTPS certificates. Firewall limited to ports 22/80/443, fail2ban and unattended upgrades on, containers set to restart unless stopped so everything survives a reboot. Total cost about $7/month, replacing four unreliable free services. Redeploy is an rsync and one compose command. This is the ops case study — lead with the reliability problem, not the tooling.

- [ ] **Step 4: `decipher.md`** — order 5, `status: live`, url `https://decipher.iswain.dev`, stack `[Flask, Python, PostgreSQL, SQLite, Gunicorn, Flask-Limiter]`.
  Facts: a browser-based puzzle game that teaches programming — four rounds covering Python, JavaScript, HTML/CSS, and bug-finding. Runs on the same database layer against either SQLite or Postgres through one `db_exec` utility. The puzzle seeder is idempotent and self-heals on a cold start, so a fresh deploy comes up with content and no manual step. Rate limiting via Flask-Limiter. Live and playable.

- [ ] **Step 5: `automation-audit.md`** — order 6, `status: live`, url `https://audit.iswain.dev`, stack `[FastAPI, Python, Pydantic, slowapi]`.
  Facts: scoping automation work for a business meant a long manual conversation before anyone knew what was worth automating. Ian built a service that takes structured intake answers and returns a scored report with ranked recommendations — `app/engine/scoring.py` and `app/engine/recommendations.py` hold the logic. Request validation through Pydantic models, rate limiting through slowapi, 8 tests. Live.

- [ ] **Step 6: `rag-assistant.md`** — order 7, `status: live`, url `https://rag.iswain.dev`, stack `[Flask, Python, ChromaDB, Vector embeddings, OpenRouter]`.
  Facts: answering questions against a set of documents meant reading all of them. Ian built a retrieval-augmented assistant: `ingest.py` chunks and embeds documents into a ChromaDB vector store, `query.py` retrieves the relevant passages and passes them to a language model so answers stay grounded in the source documents. Live with a sample corpus. Flag honestly that it runs on a free hosted model, which is a deliberate cost choice and a known fragility — free models get deprecated.

- [ ] **Step 7: `iswain-dev.md`** — order 8, `status: live`, url `https://iswain.dev`, stack `[HTML, CSS, JavaScript, GitHub Pages, Formspree, JSON-LD]`.
  Facts: Ian's own site. Hand-written HTML and CSS, no framework and no build step, served from GitHub Pages. Scores 100/100/100/100 on Lighthouse — performance, accessibility, best practices, SEO — with zero audit failures, and every outbound link resolves. Structured data via JSON-LD. Includes a multi-step intake form. Use it as the proof that Ian holds a quality bar on his own work, since a reader can run Lighthouse against it themselves.

- [ ] **Step 8: Build all eight and check for parse errors**

Run: `cd ~/portfolio && python3 build_work.py`
Expected: eight pages written, no `ValueError`.

- [ ] **Step 9: Commit**

```bash
cd ~/portfolio
git add work/
git commit -m "feat(work): seven remaining case studies"
```

---

### Task 4: Index page and the "Also built" list

**Files:**
- Create: `~/portfolio/work-templates/index.html`
- Modify: `~/portfolio/build_work.py`
- Modify: `~/portfolio/tests/test_build_work.py`

**Interfaces:**
- Consumes: `load_all`, `STATUS_LABELS`.
- Produces: `render_index(items: list[CaseStudy], template: str) -> str`; module constant `ALSO_BUILT: list[tuple[str, str]]` of (name, one-line) pairs.

- [ ] **Step 1: Write the failing test**

```python
def test_render_index_lists_all_studies_in_order():
    from build_work import render_index, CaseStudy

    items = [
        CaseStudy("a", "Alpha", "First.", "https://a.com", "live", "r", ["X"], 1, {}),
        CaseStudy("b", "Beta", "Second.", "https://b.com", "demo", "r", ["Y"], 2, {}),
    ]
    html = render_index(items, "{cards}{also_built}")
    assert html.index("Alpha") < html.index("Beta")
    assert '/work/a.html' in html
    assert "Cadence" in html  # from ALSO_BUILT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py::test_render_index_lists_all_studies_in_order -v`
Expected: FAIL — `ImportError: cannot import name 'render_index'`

- [ ] **Step 3: Implement**

```python
ALSO_BUILT = [
    ("microtools", "22 local AI tools running on my own hardware — no per-seat fees, no data leaving the machine."),
    ("Cadence", "Scheduling and habit-tracking web app."),
    ("AppForge", "Turns a plain-English description into a working single-file web app."),
    ("Cosmic Rift", "Browser game — nine missions, physics, and progression."),
    ("Futuristamantes", "Site build for a creative venture."),
    ("CRM demo", "Contact and pipeline tracker at crm.iswain.dev."),
]


def render_index(items: list[CaseStudy], template: str) -> str:
    cards = "".join(
        f'<a class="project-card" href="/work/{cs.slug}.html">'
        f'<div class="card-header"><h3 class="card-title">{cs.title}</h3>'
        f'<span class="card-status">{STATUS_LABELS[cs.status]}</span></div>'
        f'<p class="card-desc">{cs.one_line}</p>'
        f'<div class="card-tags">'
        + "".join(f'<span class="card-tag">{s}</span>' for s in cs.stack[:3])
        + "</div></a>"
        for cs in items
    )
    also = "".join(f"<li><strong>{name}</strong> — {desc}</li>" for name, desc in ALSO_BUILT)
    return template.replace("{cards}", cards).replace("{also_built}", f"<ul class='work-also'>{also}</ul>")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: 5 passed

- [ ] **Step 5: Write `work-templates/index.html`**

Same head/nav/footer pattern as `page.html`. Intro paragraph, first person, two sentences: what this is and that everything listed runs. Then `{cards}` in a `.projects-grid`, then an "Also built" section with `{also_built}`, then **the single CTA** — one link to `/intake.html`. Title: "Work — Ian Swain". Meta description names the four strongest builds.

- [ ] **Step 6: Commit**

```bash
cd ~/portfolio
git add build_work.py tests/test_build_work.py work-templates/index.html work/index.html
git commit -m "feat(work): index page with also-built list"
```

---

### Task 5: PDF export

**Files:**
- Create: `~/portfolio/work-templates/print.html`
- Create: `~/portfolio/work-print.css`
- Modify: `~/portfolio/build_work.py`

**Interfaces:**
- Consumes: `load_all`, `render_page` internals.
- Produces: `render_print(items: list[CaseStudy], template: str) -> str` and `export_pdf(html_path: Path, out_path: Path) -> None`.

- [ ] **Step 1: Write the failing test**

```python
def test_render_print_concatenates_every_study():
    from build_work import render_print, CaseStudy

    items = [
        CaseStudy("a", "Alpha", "First.", "https://a.com", "live", "r", ["X"], 1,
                  {"The problem": "<p>P1</p>", "What I built": "<p>B1</p>",
                   "Result": "<p>R1</p>", "Stack & implementation": "<p>S1</p>"}),
        CaseStudy("b", "Beta", "Second.", "https://b.com", "live", "r", ["Y"], 2,
                  {"The problem": "<p>P2</p>", "What I built": "<p>B2</p>",
                   "Result": "<p>R2</p>", "Stack & implementation": "<p>S2</p>"}),
    ]
    html = render_print(items, "{studies}")
    for marker in ("P1", "B1", "R1", "S1", "P2", "B2", "R2", "S2"):
        assert marker in html
    assert html.count("work-study") == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py::test_render_print_concatenates_every_study -v`
Expected: FAIL — `ImportError: cannot import name 'render_print'`

- [ ] **Step 3: Implement**

```python
import subprocess


def render_print(items: list[CaseStudy], template: str) -> str:
    studies = []
    for cs in items:
        body = "".join(
            f"<h3>{name}</h3>{cs.sections.get(name, '')}"
            for name in CLIENT_SECTIONS + [TECH_SECTION]
        )
        studies.append(
            f'<article class="work-study"><h2>{cs.title}</h2>'
            f'<p class="work-oneline">{cs.one_line}</p>'
            f'<p class="work-meta">{STATUS_LABELS[cs.status]} · {cs.url}</p>'
            f"{body}</article>"
        )
    return template.replace("{studies}", "".join(studies))


def export_pdf(html_path: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={out_path}",
            html_path.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: 6 passed

- [ ] **Step 5: Write `work-print.css` and `work-templates/print.html`**

Print CSS: `@page { margin: 18mm; }`, `.work-study { page-break-inside: avoid; page-break-before: always; }` with `:first-child { page-break-before: avoid; }`, black on white, no nav, no footer links, URLs printed as visible text. Cover block at top: "Ian Swain — Selected Work", the tagline, `iswain.dev`, `contact@iswain.dev`, Philadelphia, and the build date. Use the site's fonts with a serif-free fallback so the PDF renders without network fonts.

- [ ] **Step 6: Wire `main()` and export**

```python
def main() -> None:
    root = Path(__file__).resolve().parent
    items = load_all(root / "work")
    tpl = lambda n: (root / "work-templates" / n).read_text()

    for cs in items:
        (root / "work" / f"{cs.slug}.html").write_text(render_page(cs, tpl("page.html")))
    (root / "work" / "index.html").write_text(render_index(items, tpl("index.html")))
    (root / "work" / "print.html").write_text(render_print(items, tpl("print.html")))

    failures = verify_urls(items)
    if failures:
        raise SystemExit(f"URL verification failed: {failures}")

    export_pdf(
        root / "work" / "print.html",
        Path.home() / "Desktop/ISDev Projects/09_Live_Products/Work_Portfolio"
        / "Ian_Swain_Portfolio_2026-07-25.pdf",
    )
    print(f"built {len(items)} case studies + index + PDF")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: Build and open the PDF**

Run: `cd ~/portfolio && python3 build_work.py`
Expected: PDF written to the ISDev path. Open it and confirm every case study starts on its own page and nothing is clipped.

- [ ] **Step 8: Commit**

```bash
cd ~/portfolio
git add build_work.py tests/test_build_work.py work-templates/print.html work-print.css work/print.html
git commit -m "feat(work): print sheet and PDF export"
```

---

### Task 6: Verification gate

**Files:**
- Modify: `~/portfolio/build_work.py`
- Modify: `~/portfolio/tests/test_build_work.py`

**Interfaces:**
- Produces: `verify_urls(items: list[CaseStudy], timeout: int = 15) -> list[tuple[str, int]]` returning `(url, status_code)` for anything that is not 200. `live-private` entries are still checked — the marketing page must resolve even though the app requires a login.

- [ ] **Step 1: Write the failing test**

```python
def test_verify_urls_reports_non_200(monkeypatch):
    from build_work import verify_urls, CaseStudy
    import build_work

    monkeypatch.setattr(build_work, "_head_status", lambda url, timeout: 503 if "dead" in url else 200)
    items = [
        CaseStudy("a", "A", "x", "https://ok.com", "live", "r", [], 1, {}),
        CaseStudy("b", "B", "x", "https://dead.com", "live", "r", [], 2, {}),
    ]
    assert verify_urls(items) == [("https://dead.com", 503)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py::test_verify_urls_reports_non_200 -v`
Expected: FAIL — `ImportError: cannot import name 'verify_urls'`

- [ ] **Step 3: Implement**

```python
import urllib.request
import urllib.error


def _head_status(url: str, timeout: int) -> int:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "iswain-dev-build"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def verify_urls(items: list[CaseStudy], timeout: int = 15) -> list[tuple[str, int]]:
    failures = []
    for cs in items:
        code = _head_status(cs.url, timeout)
        if code != 200:
            failures.append((cs.url, code))
    return failures
```

- [ ] **Step 4: Run the full suite**

Run: `cd ~/portfolio && python3 -m pytest tests/test_build_work.py -v`
Expected: 7 passed

- [ ] **Step 5: Run the real build with the gate live**

Run: `cd ~/portfolio && python3 build_work.py`
Expected: exits 0. If any URL is not 200, the build stops — cut that case study rather than softening its language.

- [ ] **Step 6: Commit**

```bash
cd ~/portfolio
git add build_work.py tests/test_build_work.py
git commit -m "feat(work): fail the build when a portfolio URL stops resolving"
```

---

### Task 7: Wire the site to the portfolio

**Files:**
- Modify: `~/portfolio/index.html` (`#work` section)
- Modify: `~/portfolio/sitemap.xml`

**Interfaces:**
- Consumes: `/work/index.html` and the eight generated pages from Tasks 2–5.

- [ ] **Step 1: Point the four client links at their case studies**

In `#work`, the cards linking `iammajorkey.com`, `exoneratedmovers.com`, `futuristamantes.com`, and `operarihq.com` currently go straight offsite. Change the three with case studies (`iammajorkey.com` → `/work/i-am-major-key.html`, `exoneratedmovers.com` → `/work/exonerated-moving.html`, `operarihq.com` → `/work/operari.html`) to point at the case study, keeping the live URL as a secondary link inside the case study. Leave the `futuristamantes.com` card pointing offsite — it has no case study, by decision.

- [ ] **Step 2: Add a "See all work" link**

At the end of `#work`, add a `.btn-secondary` link to `/work/`.

- [ ] **Step 3: Add the nine new URLs to `sitemap.xml`**

`/work/` plus the eight case-study pages, `<changefreq>monthly</changefreq>`, `<lastmod>2026-07-25</lastmod>`.

- [ ] **Step 4: Run the existing smoke test**

Run: `cd ~/portfolio && python3 tests/test_portfolio.py`
Expected: passes (the path fix from Task 1 Step 5 is what lets it run at all).

- [ ] **Step 5: Verify every new page returns 200 locally**

```bash
cd ~/portfolio && python3 -m http.server 8788 &
sleep 2
for p in /work/ /work/i-am-major-key.html /work/exonerated-moving.html /work/operari.html \
         /work/demo-infrastructure.html /work/decipher.html /work/automation-audit.html \
         /work/rag-assistant.html /work/iswain-dev.html; do
  printf "%s %s\n" "$(curl -s -o /dev/null -w '%{http_code}' localhost:8788$p)" "$p"
done
kill %1
```
Expected: nine `200` lines.

- [ ] **Step 6: Commit**

```bash
cd ~/portfolio
git add index.html sitemap.xml
git commit -m "feat(work): link the site's work section into the case studies"
```

---

### Task 8: Voice check, exit-gate, and ship

**Files:**
- Modify: any case study the voice check flags
- Create: `~/ISDev_Projects/06_Memory_and_Docs/HANDOFFS/SESSION_work_portfolio_2026-07-25.md`

- [ ] **Step 1: Voice check every case study**

Run the `ian-voice-check` agent against the eight `work/*.md` files. It returns line-level rewrites. Apply what it flags on voice, attribution, and claim strength.

- [ ] **Step 2: Claim audit — read all eight against the Global Constraints**

Check by hand: no AI tool named · no personal names · no invented metric · no "shipped/complete/final" · every number traceable to something verified this session · OPERARI never described as a product or purchasable · Due Sorelle not called a client.

- [ ] **Step 3: Static analysis on the generator**

Run: `cd ~/portfolio && uvx ruff check --select S build_work.py tests/test_build_work.py`
Expected: clean. `subprocess.run` with a list and `check=True` is not a shell injection path; if S603 fires, confirm the argument list is fully literal before adding a targeted `# noqa`.

- [ ] **Step 4: Fresh-context adversarial review**

Dispatch the `exit-gate-auditor` agent on `git diff master..HEAD` in `~/portfolio`. Fix anything it rates Critical or High.

- [ ] **Step 5: Rebuild after fixes and re-verify**

Run: `cd ~/portfolio && python3 build_work.py && python3 -m pytest tests/test_build_work.py -v`
Expected: build exits 0, all tests pass, PDF regenerated.

- [ ] **Step 6: Push**

```bash
cd ~/portfolio
git push
```
Then wait ~60s and verify live: `curl -s -o /dev/null -w '%{http_code}\n' https://iswain.dev/work/`
Expected: `200`.

- [ ] **Step 7: Write the handoff**

`SESSION_work_portfolio_2026-07-25.md` — what was built, the file table, the decisions (two-reader split, Futuristamantes held back, no CTA on case-study pages), and the open items carried from the spec: Harry permission check before the PDF goes outside, optional OPERARI screenshots, and the fact that the PDF must be re-exported whenever a case study changes.

- [ ] **Step 8: Update memory**

Add a line to `project_portfolio.md` recording the `/work/` section and the generator, and a pointer in `MEMORY.md` if one is not already implied.

---

## Self-Review

**Spec coverage:** Source of truth → Task 1. Generator → Tasks 1–5. Web front door → Tasks 2–4, 7. PDF front door → Task 5. Two-reader split → Task 2 Step 3 (`render_page` orders client sections before the technical block). Eight case studies → Tasks 2–3. "Also built" list → Task 4. Honesty gate → Task 6 (automated) + Task 8 Step 2 (manual claim audit). Voice → Task 8 Step 1. Open items carried → Task 8 Step 7. Every spec section maps to a task.

**Placeholder scan:** No TBD/TODO. Every code step has runnable code; every content step has a verified fact sheet rather than "write something good."

**Type consistency:** `CaseStudy` field order is used positionally in the Task 4 and Task 5 tests — it matches the dataclass declaration in Task 1 (slug, title, one_line, url, status, role, stack, order, sections). `STATUS_LABELS` is defined in Task 2 and consumed in Tasks 4 and 5. `CLIENT_SECTIONS`/`TECH_SECTION` defined in Task 2, reused in Task 5. `_head_status` is monkeypatched by name in the Task 6 test and defined with that exact name.

**Known gap, deliberate:** the PDF is a build artifact, not a committed one — it regenerates from source on every build, so it can never silently drift from the web pages. It does have to be re-exported and re-sent after any content change; that is called out in the handoff.
