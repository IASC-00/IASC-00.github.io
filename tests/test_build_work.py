"""Tests for build_work.py — the /work portfolio generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_work import VALID_STATUSES, load_all, parse_case_study


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


def test_render_page_splits_client_and_technical_halves():
    from build_work import CaseStudy, render_page

    cs = CaseStudy(
        slug="s",
        title="S",
        one_line="One line.",
        url="https://e.com",
        status="live",
        role="Design, build, deploy",
        stack=["Flask"],
        order=1,
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


def test_render_index_lists_all_studies_in_order():
    from build_work import CaseStudy, render_index

    items = [
        CaseStudy("a", "Alpha", "First.", "https://a.com", "live", "r", ["X"], 1, {}),
        CaseStudy("b", "Beta", "Second.", "https://b.com", "demo", "r", ["Y"], 2, {}),
    ]
    html = render_index(items, "{cards}{also_built}")
    assert html.index("Alpha") < html.index("Beta")
    assert "/work/a.html" in html
    assert "Cadence" in html  # from ALSO_BUILT


def test_render_print_concatenates_every_study():
    from build_work import CaseStudy, render_print

    items = [
        CaseStudy(
            "a",
            "Alpha",
            "First.",
            "https://a.com",
            "live",
            "r",
            ["X"],
            1,
            {
                "The problem": "<p>P1</p>",
                "What I built": "<p>B1</p>",
                "Result": "<p>R1</p>",
                "Stack & implementation": "<p>S1</p>",
            },
        ),
        CaseStudy(
            "b",
            "Beta",
            "Second.",
            "https://b.com",
            "live",
            "r",
            ["Y"],
            2,
            {
                "The problem": "<p>P2</p>",
                "What I built": "<p>B2</p>",
                "Result": "<p>R2</p>",
                "Stack & implementation": "<p>S2</p>",
            },
        ),
    ]
    html = render_print(items, "{studies}")
    for marker in ("P1", "B1", "R1", "S1", "P2", "B2", "R2", "S2"):
        assert marker in html
    assert html.count("work-study") == 2


def test_verify_urls_reports_non_200(monkeypatch):
    import build_work
    from build_work import CaseStudy, verify_urls

    monkeypatch.setattr(
        build_work, "_head_status", lambda url, timeout: 503 if "dead" in url else 200
    )
    items = [
        CaseStudy("a", "A", "x", "https://ok.com", "live", "r", [], 1, {}),
        CaseStudy("b", "B", "x", "https://dead.com", "live", "r", [], 2, {}),
    ]
    assert verify_urls(items) == [("https://dead.com", 503)]
