# Contributing

## Setup

```bash
cp app/server/.env.sample app/server/.env
cd app/server && uv sync --all-extras
cd ../client && npm install
```

## Checks

```bash
cd app/server && uv run pytest -q
cd ../client && npm run build
```

Do not paste live API keys into issues, pull requests, or fixtures.

## Scope

This repo is the **token plane**: OpenAI-shaped routing, a classifier slot, and a ledger.

It is not Command, Control, Kanister, or a model marketplace. Keep `rivet_usd = 0` on BYO workers.

## Tests

Add a test when the change can fail an observable contract (routing, receipt shape, cache, slot semantics). Do not add tests that pin wording or field copies.
