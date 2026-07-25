---
slug: i-am-major-key
title: I AM MAJOR KEY
one_line: A Philadelphia recording artist had no website. Now they own one.
url: https://iammajorkey.com
dates: Built June 2026 · live since June 2026
status: live
role: Design, build, deploy
stack: [WordPress, PHP, Custom theme, LiteSpeed]
order: 1
---

## The problem

A working recording artist in Philadelphia had no website. Everything lived on social platforms — no single place that was theirs, nothing that would survive a platform changing its rules or an account going away. Booking inquiries had nowhere to land.

## What I built

I designed and built a one-page site around the music: a full-screen opening, the releases, and a direct way to reach the artist. It is deliberately one page, because an artist site that asks a visitor to navigate is a site that loses them.

I did the whole thing — design, build, and deploy onto the artist's own hosting — and locked down the parts of the platform that are exposed by default. I keep a versioned copy of the site and a written restore runbook, so it can be rebuilt from scratch if the host ever loses it.

This came to me through a business partner rather than a cold enquiry: he brought the client and handled the relationship, I did the build and the handover. That is how most of my client work arrives, and it means the brief usually reaches me secondhand — so the first thing I do is write down what I think was asked for and get it confirmed before building anything.

## Result

Live and public. It is the artist's own site on their own domain, and it is the first thing that shows up when someone goes looking for them.

## Stack & implementation

Custom WordPress theme, hand-written — no page builder, no purchased template. PHP templates with a hardened `functions.php`.

Two things worth naming. The host serves pages through LiteSpeed with a seven-day full-page cache, so a deploy that skips the cache purge looks like it silently failed — the runbook makes that step explicit rather than institutional knowledge. And rather than editing theme files on a host where file editing is disabled, I built a small companion plugin that hooks `plugins_loaded` at priority 0 and redirects author-enumeration probes before anything else runs.

The source is a git repository with a WordPress-installable release artifact, so a restore is an upload, not a rebuild.
