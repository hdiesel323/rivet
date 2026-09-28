# Rivet — agent notes

Rivet is a **part**. Other pieces of the agentic operating system call it; they do not live here.

## What this repo is

OpenAI-shaped token orchestrator: classifier slot, policy route, exact cache, SQLite ledger, `rivet_usd = 0`.

## What this repo is not

Command (Astra/Codex), Control (`aw`), Jev itself, Kanister, Goliath, Orca session control, issue claims, or PR merge.

## Bolt-in

Point any OpenAI SDK or worker at Rivet:

```
OPENAI_BASE_URL=http://127.0.0.1:8000/v1
OPENAI_API_KEY=not-used-unless-RIVET_API_KEY-is-set
```

Every completion returns a `rivet` receipt. Persist that object next to the job (Kanister / packet). Do not invent quality scores from the fixture compare endpoint.

Classifier slot `jev` POSTs `{ "text": "..." }` to `JEV_URL` and expects the label schema in `docs/ORCHESTRATOR.md`.

## Working here

- Server: `app/server` (FastAPI, `uv run pytest`)
- Console: `app/client` (Vite + TypeScript)
- Contract: `specs/001-token-orchestrator.md`
- Do not add a marketplace cut.
