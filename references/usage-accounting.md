# Usage accounting and spend honesty

Gearbox should optimize cost from measured usage, not guessed model prices.

Each substantial run may maintain:

```text
.gearbox/runs/<run-id>/usage.json
```

Use `scripts/usage_ledger.py` to record provider/host-reported token or cost data when available.

## Rules

- never invent token counts or dollar costs;
- never hard-code a model price table into run artifacts;
- distinguish reported values from estimates;
- record each dispatch once with a stable dispatch id;
- cached-input tokens are tracked separately from input/output totals;
- absence of cost telemetry means `reported_cost_usd: null`, not zero cost.

Optional run budgets may set:

```json
{
  "max_total_tokens": null,
  "max_reported_cost_usd": null
}
```

When set, call `usage_ledger.py check` before an optional expensive dispatch when a useful next-cost estimate exists. Mandatory correctness/safety work that cannot fit a user-configured budget becomes BLOCKED; do not silently waive the budget.

## Retrospectives

`/retro` may use dispatch counts plus this ledger to quantify expensive repeated work. If cost telemetry is absent, report proxies such as “3 duplicate review dispatches”; do not manufacture dollars.

## Routing

Use repeated measured patterns to tune model routing. Do not retune the router from one anomalous expensive call.
