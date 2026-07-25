"""Tests for build_work.py — the /work portfolio generator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_work import parse_case_study, load_all, VALID_STATUSES  # noqa: E402


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
    from build_work import render_page, CaseStudy

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
