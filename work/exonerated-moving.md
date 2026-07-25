---
slug: exonerated-moving
title: Exonerated Moving & Logistics
one_line: A new Philadelphia moving company built on second-chance hiring — brand, imagery, and site.
url: https://exoneratedmovers.com
status: live
role: Brand, imagery, build, deploy
stack: [WordPress, PHP, Custom theme, Responsive CSS]
order: 2
---

## The problem

A new Philadelphia moving and logistics company was starting from nothing: no name treatment, no colors, no photography, no website. It also had a harder problem than most new businesses. The company hires people coming out of incarceration, and that mission had to read as serious and dignified rather than as charity — to customers who mostly care whether their furniture arrives intact.

## What I built

I built the brand first, because the site could not be designed until the company knew what it looked like. That meant a color direction, typefaces, and a full set of imagery produced in-house rather than bought from a stock library, so the company did not look like every other moving company using the same three photos.

Then I designed and built the site and deployed it. The founder's own story runs on its own page, with the homepage leading into it — the mission gets room to be told properly instead of being compressed into a banner. After launch I took the owner's revisions to the copy and structure and deployed those too.

## Result

Live and public since June 2026. The company has a brand it owns, a site that explains what it does and who it hires, and a place to send customers.

## Stack & implementation

Custom WordPress theme, hand-built from a static source tree that a build script packages into an installable theme. No page builder.

The imagery was generated locally on my own hardware and then put through a grading pass I wrote, because the raw output has a flat, synthetic look that reads as fake to anyone paying attention. Composition-first prompting plus that pass is what got the images to a usable bar.

Two operational details that mattered more than the code: the host caches full pages aggressively, so same-filename asset swaps are invisible until the cache is purged — the build script now emits a version query string to force the update. And the theme deploys through an upload-and-replace flow, so I keep the source tree, the build script, and the packaged theme in one repository.
