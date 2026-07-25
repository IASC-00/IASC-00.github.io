---
slug: operari
title: OPERARI
one_line: A private operations hub for a small team — projects, tasks, files, and invoicing in one place.
url: https://operarihq.com
status: live-private
role: Architecture, build, deploy, ongoing
stack: [FastAPI, Python, React, PostgreSQL, Cloudflare R2, Docker]
order: 3
---

## The problem

A small team was running its work across email, chat threads, and shared drive folders. Nothing was wrong with any one of those tools; the problem was that the work lived in the gaps between them. Decisions were made in a thread nobody could find later, files were attached to messages instead of to projects, and the only person who knew the current state of anything was whoever had most recently touched it.

## What I built

I built the team a single place for the work: projects, tasks with owners and due dates, contacts, invoices, file attachments, comments, an activity log, and a calendar — all attached to the project they belong to rather than scattered.

Two parts go beyond a tracker. There is an assistant grounded in the team's own workspace, so asking what is outstanding on a project returns an answer from the actual data and can act on it — create tasks, add notes, mark work done. And there is a bulk capture flow: paste a wall of unstructured notes from a meeting, and it comes back sorted into proposed tasks, contacts, and a note for review before anything is saved.

Because it holds real business information, I treated access as the first requirement rather than a later hardening pass. Every route requires an authenticated user on an explicit allowlist. The database denies access by default at the row level, and files are private and served through expiring signed links rather than public URLs.

## Result

Live and in daily use by its three users. It is the team's actual system of record, not a pilot.

It is private and has no public sign-up, which is why there is no demo link here — the login is real and the data behind it is real. I can walk through it live on a call.

## Stack & implementation

Python and FastAPI on the backend, React and Vite on the front end, PostgreSQL for data, Docker for deploys. Over 200 automated tests cover the backend.

The piece I would point a technical reader at is the storage migration. File storage sat on a hosted free tier with a 1GB cap and had already blown through it. I made the storage layer dual-read — persisted paths route to the new store, anything older falls back to the old one — so the swap could ship before a single file moved. Then I migrated 233 files to object storage with a canary run first and zero failures, and reclaimed the old bucket. No downtime, no big-bang cutover, and a rollback path that stayed open the whole time.

Access control is enforced in one place rather than repeated per route: a shared check that honors project membership, which the assistant and the bulk-capture flow both delegate to instead of reimplementing.
