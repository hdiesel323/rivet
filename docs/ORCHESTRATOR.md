# Rivet token orchestrator

Rivet is not only a door. It is the place every token is **classified, metered, compared, and replayed**.

Jev (TypeSafe System One) sits in front of the workers. It does not write the answer. It decides.

```
request
  → Jev   classify task, risk, complexity, split-cell
  → policy + ledger
  → worker model (their OAuth provider or local)
  → optional judge / human score
  → ledger row you can reopen
```

## What Jev owns

One forward pass, typed questions, probabilities. Typical questions:

| Field | Type | Use |
|---|---|
| `task` | choice | code, prose, extract, tool, chat |
| `hardness` | score | cheap path vs escalate |
| `residency` | noul | must stay local |
| `experiment` | choice | control / challenger / holdout |
| `duplicate_of` | noul | already answered; cache |

Uncertain Jev → escalate the *routing* decision, not necessarily the whole job.

Jev tokens are metered too. They are cheap and output-free. They still get a ledger line so routing cost is visible.

## What the ledger owns

Every Rivet call writes a row you can revisit:

- request hash / cluster (“similar work”)
- Jev labels + confidence
- `model_used`, provider, experiment cell
- input / output tokens, `vendor_usd`, `rivet_usd`
- latency, fallback, cache hit
- quality score when one exists (judge, human, eval set)

Revisit means: filter last month’s “code review” cluster, see which model won on score per dollar, promote that route.

## Split tests

Similar work (same Jev task + embedding cluster) can be assigned to cells:

- **control** — current default route
- **challenger** — another connected model
- **holdout** — occasional frontier check so the cheap path cannot silently rot

Traffic split is a policy, not a one-off script. The orchestrator assigns the cell *before* the worker runs, so the comparison is on the same class of work.

## Improve the route

Loop:

1. Classify (Jev)
2. Serve (worker)
3. Score (judge / human / golden set)
4. Promote the winner on that cluster
5. Keep a holdout so you notice regressions

Accuracy here is “better answers on *your* distribution,” not a public leaderboard.

## Pricing (unchanged)

Connectors, Jev routing, ledger, split assignment: **$0 product fee**.  
Worker tokens on their OAuth’d account: **their vendor**.  
Jev calls if they use TypeSafe’s API: **TypeSafe’s meter**, shown on the same receipt.  
Rivet-hosted judge or long-running agents: billed later.
