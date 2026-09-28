# Rivet token orchestrator

Rivet classifies (optional), routes, meters, and replays every call. The classifier is a **slot**, not the product.

```
request
  → classifier slot   none | rules | classifier:heuristic | jev
  → exact cache
  → policy route
  → worker (demo / OpenAI-compatible / local)
  → ledger row you can reopen
```

Workers write. A classifier may decide. The ledger always remembers.

## Classifier slot

| Mode | Who decides the route | Receipt |
|---|---|---|
| `none` | Request `model`, or cheap default if `auto` | `classifier.labels` null |
| `rules` | Deterministic policy (pin, cheap-first, residency, max $) | null |
| `classifier:heuristic` | Local labels + confidence, same schema as Jev | labels + confidence |
| `jev` | `POST JEV_URL` `{ "text" }` | labels + confidence; 400 if unset |

Low confidence (&lt; 0.4) escalates the **routing** decision, not necessarily the whole job.

### Label schema (when a classifier is on)

| Field | Type | Use |
|---|---|---|
| `task` | choice: code, prose, extract, tool, chat | cluster + later splits |
| `hardness` | number 0–1 | cheap path vs escalate |
| `residency` | bool | must stay local |
| `experiment` | choice or null | control / challenger / holdout |
| `duplicate_of` | string or null | already answered |

`rules` hardness uses word boundaries. `improve` does not match `prove`; `illegal` does not match `legal opinion`.

## Ledger

Every call writes a row: request hash, cluster, slot, labels, model, provider, cell, tokens, `vendor_usd`, `rivet_usd`, latency, fallback, cache hit, why.

Reopen: `GET /v1/ledger/{id}` or `GET /v1/ledger.csv`.

Exact cache: same messages + policy hash returns the prior completion with `cache_hit=true` and `vendor_usd=0`.

## Split tests

`rivet.split_challenger_pct` assigns a stable cell from the request hash **before** the worker runs. Challenger uses the other end of the cheap/frontier pair. Residency pins do not split onto cloud.

No quality delta is reported unless a score exists. The fixture is unscored.

## Pricing

Connectors, slot, ledger, split assignment: **$0 product fee**.  
Worker tokens on their account: **their vendor**.  
Classifier HTTP (Jev): **that vendor**, still on the same receipt.  
`rivet_usd` is 0.0 on every BYO worker path in this MVP.
