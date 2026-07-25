---
slug: rag-assistant
title: Document assistant
one_line: Ask questions across a set of documents and get answers grounded in what they actually say.
url: https://rag.iswain.dev
repo: https://github.com/IASC-00/rag-chatbot
status: live
role: Design, build, deploy
stack: [Flask, Python, ChromaDB, Vector search]
order: 7
---

## The problem

A business accumulates documents — policies, contracts, manuals, past proposals — and answering a question about them means knowing which file to open. General-purpose chat tools will answer confidently from their own training instead of from your documents, which is worse than no answer, because it sounds right.

## What I built

An assistant that answers only from a supplied set of documents. Documents are processed once into a searchable index. When a question comes in, the system retrieves the passages that actually relate to it and answers from those, so the response is tied to the source material rather than to whatever the model already believed.

## Result

Live with a sample document set, so the behavior can be checked directly: ask something the documents cover and the answer tracks them.

## Stack & implementation

Python and Flask. Ingestion (`ingest.py`) chunks documents and stores embeddings in a ChromaDB vector store; the query path (`query.py`) embeds the question, retrieves the nearest passages, and passes only those to the language model as context.

The deliberate constraint is cost: it runs against a free hosted model through a provider-agnostic client, which keeps the running cost at zero. That is also its known fragility — free model endpoints get deprecated with little notice, and this one has already needed swapping once. The client is configured through environment variables specifically so changing models is a config edit and a restart, not a code change. For a client build I would put this on a paid endpoint and treat model choice as a stability decision rather than a cost one.
