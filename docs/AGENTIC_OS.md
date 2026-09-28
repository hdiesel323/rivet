# Rivet in the agentic operating system

Rivet is the **token plane**. It does not own work. It answers `POST /v1/chat/completions` and remembers what it spent.

Approved operating flow (Command → Control → workers) from the fleet architecture:

```
You → Command (Astra / Codex)
        → Jev (task advice)
        → issue / task bucket
        → aw Control (validate, dispatch)
        → isolated workers
        → receipt / review
        → Kanister
```

Workers and Command need models. That is Rivet:

```
worker / Command
    → Rivet /v1/chat/completions
         ├ classifier slot  (none | rules | heuristic | jev)
         ├ policy           (cascade, pin, residency, max $)
         ├ OpenAI-compatible or local worker
         └ ledger row       (tokens, vendor_usd, rivet_usd = 0)
```

## Bindings

| OS concern | Rivet surface |
|---|---|
| Drop-in SDK | `OPENAI_BASE_URL=http://rivet:8000/v1` |
| Task classifier (Jev) | slot `jev` + `JEV_URL` |
| Cost evidence | `response.rivet` + `GET /v1/ledger/{id}` |
| Residency / budget | `rivet.residency`, `rivet.max_usd` |
| Split tests | `rivet.split_challenger_pct` |

Rivet does not claim GitHub issues, pick hosts, or accept PRs. Control still dispatches. Kanister still curates decisions. This repo stays independently useful without the rest of the OS.

## Current honesty

This cut uses env keys and a local OpenAI-compatible base URL, not OAuth grants. Demo worker runs with no keys so the clone works.
