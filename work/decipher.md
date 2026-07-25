---
slug: decipher
title: Decipher
one_line: A browser puzzle game that teaches programming — four rounds, playable now.
url: https://decipher.iswain.dev
repo: https://github.com/IASC-00/decipher
status: live
role: Design, build, deploy
stack: [Flask, Python, PostgreSQL, SQLite]
order: 5
---

## The problem

Most people who try to learn programming quit during setup. Installing a language, picking an editor, and configuring a toolchain all happen before anyone writes a line that does something — and that is where the motivation goes.

## What I built

A puzzle game that runs in a browser. Four rounds cover Python, JavaScript, HTML and CSS, and finding a bug in code that looks correct. The bug-finding round is the one I care about most, because reading broken code is the skill people actually need and almost nothing teaches it directly.

Players work through puzzles in sequence with their progress saved. There is no install, no account setup ceremony, and nothing to configure — the first puzzle is one click from the link.

## Result

Live and playable. It runs continuously on infrastructure I control, after two earlier hosted versions went offline when their free tiers expired.

## Stack & implementation

Python and Flask with Gunicorn, rate-limited at the application layer.

The detail worth naming is the database layer. It runs against SQLite locally and PostgreSQL in production through a single `db_exec` utility that normalizes the differences — parameter style, auto-increment syntax, datetime handling — so application code has no idea which database it is talking to. That was originally a fix for a broken deploy, and it became the reason deploys stopped breaking.

The puzzle seeder is idempotent and self-heals on cold start: it checks what content exists and inserts only what is missing. A fresh deploy comes up fully populated with no manual migration step, and adding puzzles is a matter of raising a threshold rather than writing a migration.
