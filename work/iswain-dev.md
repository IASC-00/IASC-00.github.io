---
slug: iswain-dev
title: iswain.dev
one_line: My own site — hand-written, no framework, no build step, and it scores at the top of Lighthouse.
url: https://iswain.dev
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

Checked with Lighthouse on 25 July 2026: **100 for accessibility, 100 for best practices, 100 for SEO, and 99 for performance.** Performance moves between 99 and 100 between runs, which is measurement noise rather than a change in the page.

Anyone can run that audit against the site themselves in about thirty seconds. That is the point of including it here — it is the one claim in this portfolio that a reader can independently verify without taking my word for anything.

## Stack & implementation

Hand-written HTML, CSS, and vanilla JavaScript served as static files from GitHub Pages. Structured data through JSON-LD. Forms post to a hosted form endpoint with an email auto-reply, so there is no backend to run or secure.

The accessibility score is the one that takes actual work: every image carries a considered alt attribute, interactive controls expose their state, the navigation is operable from the keyboard, and the contrast ratios were chosen against the standard rather than checked afterward. A browser-driven test suite in the repository asserts those properties — alt text present, no duplicate ARIA labels, the mobile menu's expanded state correct — so a future edit that breaks accessibility fails a test instead of quietly shipping.

One known limitation, stated plainly: GitHub Pages cannot serve custom security headers, so there is no Content-Security-Policy or HSTS on this domain. Fixing it means fronting the domain with a proxy or moving hosts. For a static marketing site with no authentication and no user data, I judged that not worth the added moving parts — but it is a real gap and I would not make the same call on a site that logged anyone in.
