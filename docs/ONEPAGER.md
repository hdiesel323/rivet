# Rivet — one-pager

**One API. Your providers. Zero toll.**

## The problem

Teams already pay OpenAI, Anthropic, Google, and a local GPU box. A second marketplace tax on those same tokens is the wrong product. They need one door, a route they can explain, and a receipt.

## The product

Rivet is the token plane in front of models the customer already owns.

```
app  →  Rivet /v1/chat/completions  →  connected workers + ledger
```

The app always calls Rivet. Rivet picks the worker, caches exact repeats, and logs `model_used`, `why`, `usage`, `vendor_usd`, `rivet_usd`.

## Pricing

| Surface | Price |
|---|---|
| Connectors + orchestration | $0 |
| Tokens on the customer’s vendor | $0 from Rivet |
| Hosted Rivet models / long-running agents | billed later |

## Why not OpenRouter

OpenRouter is a merchant. Rivet is not. Keys stay with the customer. Rivet never takes a cut of their invoice.

## Proof

```bash
./scripts/start.sh
# console http://localhost:5173
# curl http://127.0.0.1:8000/v1/chat/completions
```

No keys required (demo worker). Set `OPENAI_API_KEY` for a live OpenAI-compatible worker.
