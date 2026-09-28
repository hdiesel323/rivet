# Feature: Rivet token orchestrator (MVP)

## Feature Description

Ship a clone-and-run OpenAI-shaped gateway that routes a chat completion onto a connected worker, meters the call, and writes a ledger row you can reopen. Rivet takes no cut (`rivet_usd = 0`). This repo is a **part**: the token plane of a larger agentic operating system. Other parts (Command, Control, Jev, Kanister) bolt on through the same API and receipt.

## User Story

As a team that already pays OpenAI / a local GPU
I want one `base_url` that classifies (or not), routes, falls back, and prints a receipt
So that my app never changes SDKs and FinOps can reopen Tuesday’s spend without a marketplace tax

## Problem Statement

The previous cut was a static HTML mock. It could not run a worker, persist a ledger, or be used as `OPENAI_BASE_URL`. A public GitHub repo that claims to be a switchboard must actually switch.

## Solution Statement

A FastAPI server plus a Vite console:

1. `POST /v1/chat/completions` (non-streaming subset)
2. Classifier slot: `none` | `rules` | `classifier:heuristic` | `jev`
3. SQLite ledger with CSV export
4. Demo worker (no keys) and one live OpenAI-compatible worker
5. Exact-match cache (`vendor_usd = 0` on hit)
6. 50-prompt fixture + compare endpoint that does **not** invent quality scores

## API contract

### `POST /v1/chat/completions`

Request (OpenAI shape + optional `rivet` object):

```json
{
  "model": "auto",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0,
  "max_tokens": 256,
  "stream": false,
  "rivet": {
    "slot": "rules",
    "route": "cascade",
    "residency": "any",
    "max_usd": 0.05,
    "split_challenger_pct": 0
  }
}
```

Response must include `id`, `object=chat.completion`, `created`, `model` (the worker model, not `auto`), `choices[0].finish_reason`, `usage`, and `rivet`:

```json
{
  "rivet": {
    "receipt_id": "chatcmpl_rvt_…",
    "model_used": "demo-small",
    "provider": "demo",
    "why": "…",
    "vendor_usd": 0.0,
    "rivet_usd": 0.0,
    "escalated": false,
    "fallback": false,
    "cache_hit": false,
    "classifier": {"slot": "rules", "labels": null, "confidence": null},
    "experiment_cell": "control",
    "cluster": "chat:abc123",
    "latency_ms": 12
  }
}
```

Errors use OpenAI’s envelope: `{"error": {"message": "…", "type": "…", "code": "…"}}`.

`stream: true` → 400 `stream_not_supported`.

### Slot semantics

| Slot | Who routes | Receipt `classifier` |
|---|---|---|
| `none` | Request `model`, or workspace default if `auto` | labels/confidence null |
| `rules` | Deterministic policy (cascade / pin / residency / max $) | null |
| `classifier:heuristic` | Same label schema as Jev, local regex/heuristic | labels + confidence |
| `jev` | HTTP POST to `JEV_URL` | labels + confidence; 400 if unset |

Low classifier confidence (< 0.4) escalates the **routing** decision (prefer frontier if it fits `max_usd`).

`rules` hardness uses word boundaries. It must **not** match `improve` via `prove`, or `illegal` via `legal`.

### Other endpoints

- `GET /health`
- `GET /v1/models`
- `GET /v1/connectors`
- `GET /v1/ledger?limit=&cluster=&cell=&slot=`
- `GET /v1/ledger/{id}`
- `GET /v1/ledger.csv`
- `GET /v1/eval/fixture`
- `POST /v1/eval/run` `{ "slot": "rules", "limit": 50 }`
- `POST /v1/eval/compare` `{ "slots": ["rules", "none"], "limit": 50 }` — spend/route columns only; no quality delta unless scores exist (they do not in MVP)

## Workers

- **demo**: always on unless a real worker is configured and `RIVET_DEMO` is not forced on. `vendor_usd = 0`. Never leaves the machine.
- **openai**: `OPENAI_API_KEY` + optional `OPENAI_BASE_URL` (default `https://api.openai.com/v1`).
- **local**: `LOCAL_BASE_URL` OpenAI-compatible (vLLM / Ollama).

OAuth connectors are the destination, not this cut.

## Agentic OS bolt-in

Rivet is the token plane. Command/Control/workers point `OPENAI_BASE_URL` at Rivet. Receipts are the cost/evidence object for Kanister and `aw`. The classifier slot may bind to Jev — the same classifier Command uses for task buckets. Rivet does not claim issues, dispatch hosts, or merge PRs.

## Acceptance

- Clone, `./scripts/start.sh`, send `model: auto` with no keys → demo receipt, `rivet_usd = 0`
- With `OPENAI_API_KEY`, the same request can hit a live worker
- Ledger reopen by id and CSV export
- Fixture has 50 labeled prompts
- Tests cover hardness false-positives, receipt shape, cache hit, slot `none` vs `rules`
- LICENSE is complete MIT
