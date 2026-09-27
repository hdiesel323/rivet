# Rivet

**One API. Your providers. Zero toll.**

Rivet is a control plane in front of models you already pay for. Connect OpenAI, Anthropic, Google, Azure, and local runtimes with OAuth (or a local adapter). Rivet routes, falls back, and prints a receipt. It does not resell tokens.

- Connectors + orchestration: **free**
- Inference on *your* connected account: **your vendor bill**
- Inference Rivet hosts (optional later): billed separately

This repo is the proof / MVP: a working console you can demo and a one-pager you can print.

## Demo

Open `app/index.html` in a browser (no build step):

```bash
cd app && python3 -m http.server 8765
# http://localhost:8765
```

Print sheet: `app/print.html` → File → Print → A4 / Letter.

## What the MVP shows

1. OAuth-style connector cards (simulated grant; no tokens leave the page).
2. Policy: cheap-first cascade, residency, max $ per call.
3. Playground: one `/v1/chat/completions`-shaped request.
4. Router decision + receipt (`model_used`, `why`, `vendor_usd`, `rivet_usd = 0`).
5. Trace log you can screenshot for a pitch.

Routing in this MVP is deterministic mock logic so the story is visible without keys.

## Product rule

> Connectors and orchestration: $0.  
> Work on Rivet machines: billed.  
> Work on the customer’s OAuth’d provider: $0 from Rivet.

## Repo layout

```
app/index.html    interactive console
app/print.html    one-pager for print / PDF
docs/ONEPAGER.md  same copy in markdown
```

## Status

Proof of idea. Not a production gateway. Do not paste real API keys into the demo.
