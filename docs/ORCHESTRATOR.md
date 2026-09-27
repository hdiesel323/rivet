# Rivet token orchestrator

Rivet is not only a door. It is the place every token is **classified (optional), metered, compared, and replayed**.

The **classifier is a slot**, not the product. Jev is the default *if you want System One*. You can also plug another classifier, use rules only, or run with no classifier at all.

```
request
  → classifier slot   jev | other | rules | none
  → policy + ledger
  → worker model (their OAuth provider or local)
  → optional judge / human score
  → ledger row you can reopen
```

## Classifier slot

Set per workspace or per route. The ledger always records which slot ran.

| Mode | Who decides the route | When to use |
|---|---|---|
| `jev` | TypeSafe Jev — typed labels + confidence, one pass | Fast structured routing, split-cell assignment |
| `classifier:<id>` | Any connected model or small local classifier that returns the same label schema | You already have a router model, or Jev is not allowed |
| `rules` | Deterministic policy only (pin model, cheap-first by name, residency) | Air-gapped, zero extra calls, audits that hate learned routers |
| `none` | Pass-through: `model` from the request, or workspace default | Bring-your-own routing in the app; Rivet is just the door + ledger |

Same receipt shape in every mode. If the slot is `none` or `rules`, `classifier` and `confidence` are null. Tokens and `$` still land in the ledger so you can add a classifier later and compare eras.

You can **split-test classifiers too**: cell A = Jev, cell B = rules, cell C = a small local model — on the same work cluster. That is how you decide whether Jev earns its keep.

## What a classifier returns (when one is on)

One forward pass, typed questions, probabilities. Typical questions:

| Field | Type | Use |
|---|---|---|
| `task` | choice | code, prose, extract, tool, chat |
| `hardness` | score | cheap path vs escalate |
| `residency` | noul | must stay local |
| `experiment` | choice | control / challenger / holdout |
| `duplicate_of` | noul | already answered; cache |

Low confidence → escalate the *routing* decision, not necessarily the whole job.

Classifier tokens (Jev or otherwise) are metered on the same receipt. They still get a ledger line so routing cost is visible.

## What the ledger owns

Every Rivet call writes a row you can revisit:

- request hash / cluster (“similar work”)
- classifier id + labels + confidence (null if `none` / `rules`)
- `model_used`, provider, experiment cell
- input / output tokens, `vendor_usd`, `rivet_usd`
- latency, fallback, cache hit
- quality score when one exists (judge, human, eval set)

Revisit means: filter last month’s “code review” cluster, see which model won on score per dollar, promote that route.

## Split tests

Similar work (same task label + embedding cluster, or rules bucket) can be assigned to cells:

- **control** — current default route
- **challenger** — another connected model
- **holdout** — occasional frontier check so the cheap path cannot silently rot

Traffic split is a policy, not a one-off script. The orchestrator assigns the cell *before* the worker runs, so the comparison is on the same class of work.

## Improve the route

Loop:

1. Classify if a slot is on
2. Serve (worker)
3. Score (judge / human / golden set)
4. Promote the winner on that cluster
5. Keep a holdout so you notice regressions

Accuracy here is “better answers on *your* distribution,” not a public leaderboard.

## Pricing (unchanged)

Connectors, classifier slot, ledger, split assignment: **$0 product fee**.  
Worker tokens on their OAuth’d account: **their vendor**.  
Jev / other paid classifier calls: **that vendor’s meter**, on the same receipt.  
Rivet-hosted judge or long-running agents: billed later.
