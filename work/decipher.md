---
slug: decipher
title: Decipher
one_line: A browser puzzle game that teaches programming — four rounds, accounts, a leaderboard, and a duel mode. Playable now.
url: https://decipher.iswain.dev
repo: https://github.com/IASC-00/decipher
dates: March 2026 – present
status: live
role: Design, build, deploy
stack: [Flask, Python, PostgreSQL, SQLite]
order: 5
---

## The problem

Most people who try to learn programming quit during setup. Installing a language, picking an editor, and configuring a toolchain all happen before anyone writes a line that does something — and that is where the motivation goes.

## What I built

A puzzle game that runs in a browser. Four rounds cover Python, JavaScript, HTML and CSS, and finding a bug in code that looks correct. The bug-finding round is the one I care about most, because reading broken code is the skill people actually need and almost nothing teaches it directly.

Players work through puzzles in sequence with their progress saved. Around that sits the reason people come back: accounts, a ranked leaderboard, achievements, and a duel mode where two players race the same puzzle. Six tables carry it — puzzles, sessions, answers, high scores, players, achievements.

I built this one alone, start to finish, including the server it runs on.

## Result

Live and playable. It runs continuously on infrastructure I control, after two earlier hosted versions went offline when their free tiers expired.

## Stack & implementation

Python and Flask with Gunicorn, rate-limited at the application layer.

**One database layer, two databases.** It runs on SQLite locally and PostgreSQL in production through a single `db_exec` function, so no application code branches on which database it is talking to. That function does three things: rewrites `INSERT OR IGNORE INTO x` into `INSERT INTO x … ON CONFLICT DO NOTHING`, swaps `?` placeholders for `%s`, and returns a cursor from either driver. A companion `_scalar` helper normalises row access, because SQLite hands back a `sqlite3.Row` and the Postgres driver hands back a dict — code that indexed one broke silently on the other.

This started as a fix for a deploy that kept failing on Postgres-only syntax, and it became the reason deploys stopped failing. The payoff is local development with zero configuration: no `DATABASE_URL`, no container, no migration step. Clone it and run it.

**Where that approach breaks, since a reviewer will find it anyway:** the placeholder swap is a plain string replacement, so a literal `?` inside a quoted SQL string would be corrupted. Nothing in the codebase does that today, and the real fix is to parse rather than replace. At this size an ORM would cost more than it saves — but I would rather name the limit than pretend it is not there.

**The seeder is idempotent and self-heals on cold start.** It checks what content already exists and inserts only what is missing, so a fresh deploy comes up fully populated with no manual migration step, and a database that loses rows repairs itself on the next boot. Adding puzzles means extending a list and raising a threshold, not writing a migration.

**Connections close on every request, including failed ones.** The teardown handler runs on the error path too, which is where connection leaks usually come from.

Six tests cover the health endpoint, the pages a logged-out visitor must be able to load, and that `/play` refuses an unauthenticated request. That is thin, and it is the first thing I would grow.
