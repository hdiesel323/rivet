# Rivet — next-level recommendations

The idea is sharp. The gap is **proof you can feel in production**, not more manifesto.

Written 27 Sep 2026 from the proof/MVP cut.

## Keep

- One API, their OAuth, `rivet_usd = 0`
- Classifier as a slot, not a religion (`jev` / `classifier:<id>` / `rules` / `none`)
- Ledger you can reopen
- Honest MVP (mocked routing until a worker is live)

## Change

1. **Stop selling architecture. Sell one week of their traffic.**  
   A visitor should paste 200 anonymized prompts *or* hit “replay last 50 from fixture” and see: routes, $, Jev-vs-rules, a promote button. Diagrams don’t convert. A before/after bill does.

2. **Make the receipt the object.**  
   Persist rows (SQLite is enough). Filter by cluster, cell, classifier, provider. Deep-link one call. If they can’t reopen Tuesday’s “code review” cluster, it isn’t an orchestrator yet.

3. **Live one connector.**  
   Pick a single OAuth (OpenAI *or* a local OpenAI-compatible). Mock Connect is fine for a printout; a next-level demo needs one real grant and one real `chat.completions` through Rivet. Everything else can stay fake.

4. **Put the slot in the console.**  
   Dropdown: `jev / rules / none / classifier:local`. Same playground. That’s how people understand “Jev version vs not” without reading `ORCHESTRATOR.md`.

5. **Split test as a first-class policy, not a paragraph.**  
   `10% challenger on task=code`. Show two columns: control vs challenger, tokens, $, win rate when a score exists. No score → don’t pretend accuracy improved.

## Improve (in order)

| Order | Thing | Why it levels up |
|---|---|---|
| 1 | Ledger + CSV export | FinOps can take it into a meeting |
| 2 | One real worker path | Demo stops being a cartoon |
| 3 | Fixture eval set (50–100 prompts, labeled task) | You can claim “rules vs jev” with numbers *on that set* |
| 4 | Holdout + promote | The loop becomes visible |
| 5 | Cache + exact-match first | Instant “we didn’t spend” stories |
| 6 | GitHub Pages for `/app` | Link in the README, no `python -m http.server` |

## Don’t do yet

- 200-provider catalog
- Visual agent canvas
- Token markup / marketplace
- Training a foundation model
- Perfect Jev integration before the ledger exists

## Positioning line

> Paste your traces. Rivet will classify (or not), split similar work, and show which connected model won on *your* distribution — without taking a cut.

## Two-week cut

- SQLite ledger + receipt UI
- Slot dropdown on the console
- Rules + `none` live; Jev behind a flag
- One OpenAI-compatible worker
- 50-prompt fixture + a page that says “challenger saved $X, quality Δ on N scored rows”
- Pages deploy of the console

That’s the jump from “cool switchboard story” to “I would run next month’s traffic through this.”
