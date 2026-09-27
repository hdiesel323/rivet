# Rivet — one-pager

**One API. Your providers. Zero toll.**

## The problem
Teams already pay OpenAI, Anthropic, Google, and a local GPU box. A second marketplace tax on those same tokens is the wrong product. They need one door, a route they can explain, and a receipt.

## The product
Rivet is the control plane in front of models the customer already owns.

```
app  →  Rivet API  →  connected providers (OAuth) + local adapters
```

The app always calls Rivet. Rivet picks the worker, escalates when the cheap path fails, and logs `model_used`, `why`, `vendor_usd`, `rivet_usd`.

## Pricing
| Surface | Price |
|---|---|
| OAuth connectors | $0 |
| Routing, fallback, traces | $0 |
| Tokens on the customer’s vendor | $0 from Rivet |
| Hosted Rivet models / long-running agents | billed |

## Why not OpenRouter
OpenRouter is a merchant. Rivet is not. Keys and OAuth grants stay with the customer. Rivet never takes a cut of their Anthropic or OpenAI invoice.

## Proof
Open `app/index.html`. Connect mock providers. Send one prompt. Print the receipt. That is the MVP.
