---
slug: automation-audit
title: Automation Audit Generator
one_line: Turns a business's intake answers into a scored report on what's worth automating.
url: https://audit.iswain.dev
repo: https://github.com/IASC-00/automation-audit-generator
status: live
role: Design, build, deploy
stack: [FastAPI, Python, Pydantic]
order: 6
---

## The problem

Scoping automation work for a business meant a long unstructured conversation before anyone could say what was worth doing. That is slow for me and unconvincing for them — the owner has to take my word for which of their processes is the expensive one, and I am guessing until I have seen enough of the business to stop guessing.

## What I built

A service that takes structured answers about how a business currently operates — what tasks get repeated, how often, how long they take, how many people touch them — and returns a report that scores each process and ranks what to automate first.

The value is the ranking, not the list. Most owners can name ten things they wish were automatic; what they cannot do is tell which one pays for itself first. The scoring is explicit and consistent, so two businesses answering the same way get the same recommendation, and I can explain why a recommendation came out the way it did.

## Result

Live and usable. It turns the opening conversation from an unstructured interview into a document the business owner keeps, whether or not they hire me.

## Stack & implementation

Python and FastAPI. Request validation through Pydantic models, so malformed input is rejected at the boundary with a useful error rather than failing deeper in. Rate limiting via slowapi.

The scoring and recommendation logic sits in its own module (`app/engine/`) separate from the routes, which is what makes it testable — the rules can be exercised directly without going through HTTP. Eight tests cover the route layer.

Deployment history is part of this one: it originally ran on a hosted free tier that exhausted its credit and went offline. It now runs in a container on infrastructure I own, which is the reason the link above still works.
