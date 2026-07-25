---
slug: iswain-dev
title: iswain.dev
one_line: My own site — hand-written, no framework, no build step, and it scores at the top of Lighthouse.
url: https://iswain.dev
repo: https://github.com/IASC-00/IASC-00.github.io
dates: February 2026 – present · 217 commits
status: live
role: Design, build, deploy
stack: [HTML, CSS, JavaScript, GitHub Pages, JSON-LD]
order: 8
---

## The problem

Most small-business sites are slow because of what was used to build them, not because of what they contain. A brochure site with six sections does not need a framework, a bundler, or a hundred requests — but that is what most of them ship, and the owner pays for it in load time and in the cost of every future change.

I wanted my own site to be the argument against that, since a prospective client can check it themselves.

## What I built

The site I run my business from. It explains what I do, shows the work, and takes enquiries through a structured intake form that qualifies a project before a call rather than during one.

It is hand-written — no framework, no build step, no dependency to update. That is not nostalgia; it is a maintenance decision. A site with no build step still deploys in five years, and changing a headline is editing a line rather than reinstalling a toolchain.

## Result

Checked with Lighthouse on 25 July 2026: **100 for accessibility, 100 for best practices, 100 for SEO, and 99 for performance** — performance moves between 99 and 100 run to run, which is measurement noise rather than a change in the page.

Anyone can run that audit themselves in about thirty seconds. That is why it is here: it is the one claim in this portfolio a reader can verify without taking my word for anything.

## Stack & implementation

Hand-written HTML, CSS, and vanilla JavaScript served as static files from GitHub Pages. Structured data through JSON-LD. Forms post to a hosted endpoint with an email auto-reply, so there is no backend to run or secure.

Accessibility is the score that takes real work: considered alt text on every image, interactive controls that expose their state, keyboard-operable navigation, and contrast ratios chosen against the standard rather than checked afterward. A browser-driven test suite covers the homepage — alt text present, no duplicate ARIA labels, the mobile menu's expanded state correct — so an edit that breaks one of those fails a test rather than quietly shipping. That suite does not yet cover these case-study pages; they are checked with Lighthouse by hand, which is weaker, and extending the suite to them is on the list.

The case studies on this site are generated rather than hand-written: one Markdown file per project, a Python script that renders them to these pages and to a PDF, and a build that fails if any URL a page claims is live stops returning 200 on its own host. That last part matters more than it sounds — a redirect to a parked domain would otherwise pass as "live" while the page kept saying so.

I also had this portfolio reviewed by someone who had not written it, specifically told to try to break it. It came back with a claim I had gotten wrong — I had described one of my games as a physics game when it is a card game, and called a feature delivered when it was still pending a playtest. It also found that the page failed a contrast check on the very site whose headline claim is a perfect accessibility score. I fixed all of it. I would rather be told by a reviewer than by an interviewer.

One known limitation: GitHub Pages cannot serve custom security headers, so there is no Content-Security-Policy or HSTS here. Fixing it means fronting the domain with a proxy or changing hosts. For a static site with no authentication and no user data I judged that not worth the moving parts — but it is a real gap, and I would not make the same call on a site that logged anyone in.
