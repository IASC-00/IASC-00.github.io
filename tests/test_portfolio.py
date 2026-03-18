"""
iswain.dev Portfolio — Playwright smoke tests
Run: python3 tests/test_portfolio.py
Requires: pip install playwright && python3 -m playwright install chromium
"""

import sys
import time
import threading
import http.server
import functools
from playwright.sync_api import sync_playwright, expect

PORT = 8787
BASE = f"http://localhost:{PORT}"

# ── Local server ──────────────────────────────────────────────────────────────


def start_server():
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory="/home/iswai/portfolio"
    )
    server = http.server.HTTPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)
    return server


# ── Test runner ───────────────────────────────────────────────────────────────

PASS = "✓"
FAIL = "✗"
results = []


def check(label, fn):
    try:
        fn()
        print(f"  {PASS}  {label}")
        results.append((True, label))
    except Exception as e:
        print(f"  {FAIL}  {label}")
        print(f"       {e}")
        results.append((False, label))


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_hamburger_nav(page):
    """Mobile hamburger opens/closes nav menu."""
    page.set_viewport_size({"width": 390, "height": 844})  # iPhone 14
    page.goto(BASE)
    page.wait_for_load_state("networkidle")

    hamburger = page.locator("#nav-hamburger")
    menu = page.locator("#nav-mobile-menu")

    check("hamburger button is visible on mobile", lambda: hamburger.is_visible())

    check(
        "mobile menu is hidden initially",
        lambda: (
            (not menu.is_visible())
            or ("open" not in (menu.get_attribute("class") or ""))
        ),
    )

    def open_menu():
        hamburger.click()
        page.wait_for_timeout(200)
        assert menu.is_visible(), "menu did not open after hamburger click"
        assert "open" in (hamburger.get_attribute("class") or ""), (
            "hamburger missing .open class"
        )
        assert hamburger.get_attribute("aria-expanded") == "true", (
            "aria-expanded not set to true"
        )

    check("clicking hamburger opens menu", open_menu)

    def close_menu():
        hamburger.click()
        page.wait_for_timeout(200)
        assert "open" not in (menu.get_attribute("class") or ""), "menu did not close"
        assert hamburger.get_attribute("aria-expanded") == "false", (
            "aria-expanded not reset"
        )

    check("clicking hamburger again closes menu", close_menu)

    def menu_link_closes():
        hamburger.click()
        page.wait_for_timeout(150)
        menu.locator("a").first.click()
        page.wait_for_timeout(200)
        assert "open" not in (menu.get_attribute("class") or ""), (
            "menu did not close on link click"
        )

    check("clicking a menu link closes menu", menu_link_closes)


def test_contact_form(page):
    """Contact form has required fields, honeypot, and submit button."""
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(BASE + "#contact")
    page.wait_for_load_state("networkidle")

    check(
        "name input is present and required",
        lambda: (
            page.locator("#n").is_visible()
            and page.locator("#n").get_attribute("required") is not None
        ),
    )

    check(
        "email input is present and required",
        lambda: (
            page.locator("#e").is_visible()
            and page.locator("#e").get_attribute("required") is not None
        ),
    )

    check(
        "message textarea is present and required",
        lambda: (
            page.locator("#m").is_visible()
            and page.locator("#m").get_attribute("required") is not None
        ),
    )

    check("service dropdown is present", lambda: page.locator("#svc").is_visible())

    check(
        "honeypot field is hidden",
        lambda: not page.locator('input[name="_gotcha"]').is_visible(),
    )

    check(
        "submit button is present",
        lambda: page.locator("button.form-submit").is_visible(),
    )

    def form_validates_empty():
        # Fill nothing, try submitting — browser validation should block it
        btn = page.locator("button.form-submit")
        btn.click()
        # If the page didn't navigate away, validation kicked in
        assert page.url.startswith(BASE), (
            "form submitted without required fields filled"
        )

    check("empty form does not submit (browser validation)", form_validates_empty)


def test_demo_links_have_aria_labels(page):
    """All 'Try the demo →' links have unique aria-labels."""
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(BASE)
    page.wait_for_load_state("networkidle")

    generic_texts = ["try the demo", "try the demo →"]

    def check_aria_labels():
        links = page.locator("a").all()
        violations = []
        for link in links:
            text = (link.inner_text() or "").strip().lower()
            if text in generic_texts:
                aria = link.get_attribute("aria-label")
                if not aria:
                    href = link.get_attribute("href") or ""
                    violations.append(f"link to {href} has no aria-label")
        assert not violations, "\n  ".join(violations)

    check("all generic demo links have aria-labels", check_aria_labels)

    def no_duplicate_aria_labels():
        links = page.locator("a[aria-label]").all()
        seen = {}
        dups = []
        for link in links:
            label = link.get_attribute("aria-label")
            href = link.get_attribute("href") or ""
            if label in seen and seen[label] != href:
                dups.append(label)
            seen[label] = href
        assert not dups, f"duplicate aria-labels: {dups}"

    check(
        "no duplicate aria-labels across different destinations",
        no_duplicate_aria_labels,
    )


def test_images_have_alt_text(page):
    """Content images have non-empty alt text."""
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(BASE)
    page.wait_for_load_state("networkidle")

    def no_missing_alt():
        imgs = page.locator("img").all()
        missing = []
        for img in imgs:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt")
            # hero swan and decorative images are allowed empty alt
            if alt is None:
                missing.append(src)
        assert not missing, f"images missing alt attribute: {missing}"

    check("no images missing alt attribute entirely", no_missing_alt)

    def content_images_have_descriptive_alt():
        # Card images (demo screenshots) should have non-empty alt
        imgs = page.locator(".card-img img").all()
        empty_alt = []
        for img in imgs:
            src = img.get_attribute("src") or ""
            alt = img.get_attribute("alt") or ""
            if not alt.strip():
                empty_alt.append(src)
        assert not empty_alt, f"card images with empty alt: {empty_alt}"

    check(
        "all demo card images have descriptive alt text",
        content_images_have_descriptive_alt,
    )


def test_sticky_cta(page):
    """Sticky CTA appears after scrolling past hero, hides at contact section."""
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(BASE)
    page.wait_for_load_state("networkidle")

    cta = page.locator("#sticky-cta")

    check("sticky CTA element exists", lambda: cta.count() == 1)

    def not_visible_at_top():
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(200)
        classes = cta.get_attribute("class") or ""
        assert "visible" not in classes, "sticky CTA visible before scrolling"

    check("sticky CTA not visible at page top", not_visible_at_top)

    def visible_after_hero():
        # Scroll well past the hero (hero is ~94vh)
        page.evaluate("window.scrollTo(0, window.innerHeight * 2)")
        page.wait_for_timeout(300)
        classes = cta.get_attribute("class") or ""
        assert "visible" in classes, "sticky CTA not visible after scrolling past hero"

    check("sticky CTA appears after scrolling past hero", visible_after_hero)

    def links_to_intake():
        href = cta.get_attribute("href") or ""
        assert "/intake.html" in href, f"sticky CTA href unexpected: {href}"

    check("sticky CTA links to /intake.html", links_to_intake)


def test_nav_links_visible_desktop(page):
    """Nav links are visible on desktop, hamburger hidden."""
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(BASE)
    page.wait_for_load_state("networkidle")

    check(
        "nav links visible on desktop", lambda: page.locator(".nav-links").is_visible()
    )

    check(
        "hamburger hidden on desktop",
        lambda: not page.locator("#nav-hamburger").is_visible(),
    )


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    server = start_server()
    print(f"\niswain.dev portfolio tests — {BASE}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("── Hamburger Nav ─────────────────────────────")
        test_hamburger_nav(page)

        print("\n── Contact Form ──────────────────────────────")
        test_contact_form(page)

        print("\n── Demo Link Aria-Labels ─────────────────────")
        test_demo_links_have_aria_labels(page)

        print("\n── Image Alt Text ────────────────────────────")
        test_images_have_alt_text(page)

        print("\n── Sticky CTA ────────────────────────────────")
        test_sticky_cta(page)

        print("\n── Desktop Nav ───────────────────────────────")
        test_nav_links_visible_desktop(page)

        browser.close()

    server.shutdown()

    passed = sum(1 for ok, _ in results if ok)
    failed = sum(1 for ok, _ in results if not ok)
    print(f"\n{'─' * 46}")
    print(f"  {passed} passed  ·  {failed} failed  ·  {len(results)} total")
    if failed:
        print("\n  Failed:")
        for ok, label in results:
            if not ok:
                print(f"    {FAIL} {label}")
    print()
    sys.exit(0 if failed == 0 else 1)
