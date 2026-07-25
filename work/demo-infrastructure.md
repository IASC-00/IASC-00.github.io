---
slug: demo-infrastructure
title: Always-on demo infrastructure
one_line: Four demo apps kept going offline on free hosting. I moved them onto one server for about $7 a month.
url: https://decipher.iswain.dev
status: live
role: Architecture, provisioning, deploy
stack: [Docker, Caddy, Ubuntu, Let's Encrypt]
order: 4
---

## The problem

Four working applications were deployed across free hosting tiers, and they kept going dark. One returned a 404 after its service was reclaimed. Another stopped when its credit ran out. The rest slept after a period of inactivity, so the first visitor to arrive waited thirty seconds for a cold start — or gave up.

This is the worst possible failure for demo software. The apps worked. Anyone who went looking found them broken, and a broken link is worse than no link, because it says the work was abandoned.

## What I built

I moved all four onto a single small server that I control, with each application isolated in its own container behind a shared entry point that handles the domains and certificates. Everything restarts automatically after a reboot, and certificates renew without anyone touching them.

The server is locked down to the three ports it needs, with automatic security updates and repeated-failure banning enabled. Redeploying any application is a file sync and a single command.

## Result

All four run continuously — no sleeping, no cold starts, no expiry. Total cost is about $7 a month, replacing four unreliable free services, and I own the box rather than renting a platform that can change its terms.

## Stack & implementation

Ubuntu on a small cloud instance. Docker Compose runs one service per application plus Caddy as a reverse proxy, which handles automatic Let's Encrypt certificates and maps each subdomain to its container. Containers are set to restart unless explicitly stopped, so the whole stack survives a reboot without intervention.

Hardening is ufw limited to ports 22, 80, and 443, fail2ban, unattended upgrades, and key-only SSH with a dedicated deploy key — no password authentication.

Secrets live in an environment file that Compose substitutes at run time rather than in any image. One application keeps a named volume for its database; the rest are stateless and seed themselves on start, which means a rebuild is never a data-loss risk.

The honest tradeoff: this is one server with no redundancy, so a host failure takes all four demos down at once. For demo software that is the right trade — the alternative was four services that were already failing independently, and this one is cheaper and predictable.
