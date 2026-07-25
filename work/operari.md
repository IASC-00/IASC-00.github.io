---
slug: operari
title: OPERARI
one_line: A private operations hub for a small team — projects, tasks, files, and invoicing in one place.
url: https://operarihq.com
dates: May 2026 – present · 214 commits
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

I did not get the sharing model right the first time. Marking a project "shared" did not actually make it visible to the other two people, because visibility was computed from ownership and membership and quietly ignored the shared flag. Nobody found that in a test — it surfaced because two of them could not see work they had been told was theirs to see. I rewrote the rule so shared genuinely means visible to the whole team, and shipped it. Building something three named people use every day means being wrong in front of them and fixing it quickly, which is a different discipline from building something nobody has opened yet.

## Result

Live and in daily use by its three users. It is the team's actual system of record, not a pilot.

It is private and has no public sign-up, which is why there is no demo link here — the login is real and the data behind it is real. I can walk through it live on a call.

## Stack & implementation

Python and FastAPI on the backend, React and Vite on the front end, PostgreSQL for data, Cloudflare R2 for files, Docker for deploys.

**The storage migration.** File storage sat on a hosted free tier with a 1GB cap and had already blown through it. Rather than a cutover, I made the storage layer dual-read: a persisted path beginning `r2:` routes to the new object store and returns a presigned URL, anything else falls back to the old store untouched. That shipped and sat inert in production before a single file moved — with no `R2_BUCKET` configured it behaves exactly as before, so the risky code was exercised by real traffic while doing nothing.

Then the migration ran with a `--limit 1` canary first: move one file, open it on the live site, confirm, continue. **233 files, zero failures**, then the old bucket was reclaimed — 391MB down to 0.2MB. No downtime, no big-bang, and the rollback path stayed open the whole way because the old branch of the reader was never deleted.

**Access control lives in one module, not in the routes.** `backend/access.py` exposes `can_view`, `list_visible_projects` and `assert_project_access`, and the assistant and bulk-capture flows delegate to it rather than reimplementing the check. That consolidation is what made the sharing bug above a one-line class of fix instead of a hunt through every endpoint. An automated review of an earlier version caught an IDOR where the assistant could read a private project it had not been granted; that fix landed in the same shared check, and every caller inherited it.

**Defense in depth on the data.** Row-level security denies by default on all 17 tables — every permissive policy was dropped, so the database itself refuses anonymous reads even if application code has a bug. The backend holds the only key that bypasses it; the frontend key can no longer touch tables or files at all. The storage bucket is private and served through signed URLs with an expiry.

**Known gap, stated plainly:** signed URLs are gated on authentication and the allowlist, not per-project ACL. For three trusted users that is a deliberate stopping point rather than an oversight, and it is the first thing I would close before a fourth organisation touched it.

160 tests cover the backend.
