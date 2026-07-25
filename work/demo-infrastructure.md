---
slug: demo-infrastructure
title: Hosting that stays up
one_line: I run my own production server — hardened, automatic HTTPS, four apps that don't go down. The same setup I'd run for a client.
url: https://decipher.iswain.dev
extra_urls: [https://crm.iswain.dev, https://rag.iswain.dev, https://audit.iswain.dev]
status: live
role: Architecture, provisioning, deploy
stack: [Docker, Caddy, Ubuntu, Let's Encrypt]
order: 4
---

## The problem

Software that is live is only useful if it stays live, and most cheap hosting quietly fails at exactly that. Platforms reclaim inactive services, credits run out, and free tiers put an application to sleep so the first visitor waits thirty seconds or gives up. You usually find out because someone tells you your site is down.

I learned this on my own applications — four of them went dark across three different platforms — and it is the same failure a small business hits when the person who set up their site is no longer around and something silently expires.

## What I built

Infrastructure I control, running four applications continuously.

Each one is isolated so a fault in one cannot touch the others. A single entry point handles the domains and renews the HTTPS certificates automatically, with no annual scramble over an expired certificate. Everything restarts by itself after a reboot or a crash, which means recovery does not depend on me being awake.

The server is closed to everything except the three ports it needs, with automatic security patching and automatic banning of repeated login attempts. Deploying an update is one command, so a change is never postponed because deploying is a chore.

## Result

Four applications running continuously — no sleeping, no cold starts, nothing that expires on a schedule I do not control. The whole thing runs for a fraction of what the equivalent managed platforms charge.

This is the part of the work that clients usually pay for after something has already broken. It is also exactly what an ongoing care arrangement covers: the site stays up, the certificates renew, the patches land, and nobody has to remember to check.

## Stack & implementation

Ubuntu on a small cloud instance. Docker Compose runs one service per application plus Caddy as a reverse proxy, which handles automatic Let's Encrypt certificates and maps each subdomain to its container. Containers are set to restart unless explicitly stopped, so the whole stack survives a reboot without intervention.

Hardening is ufw limited to ports 22, 80, and 443, fail2ban, unattended upgrades, and key-only SSH with a dedicated deploy key — no password authentication.

Secrets live in an environment file that Compose substitutes at run time rather than in any image. One application keeps a named volume for its database; the rest are stateless and seed themselves on start, which means a rebuild is never a data-loss risk.

The honest tradeoff: this is one server with no redundancy, so a host failure takes all four demos down at once. For demo software that is the right trade — the alternative was four services that were already failing independently, and this one is cheaper and predictable.
