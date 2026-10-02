# Risk and execution budgets

Gearbox scales review and model spend with concrete risk.

## Risk classes

Classify every DAG node `low`, `medium`, `high`, or `critical` using repository evidence.

Signals that raise risk include authentication/authorization, secrets/trust boundaries, billing, destructive migrations, public API/schema compatibility, persistence/data integrity, concurrency, production configuration, cryptography, and wide cross-cutting refactors.

Suggested policy:

```yaml
risk_policy:
  auth: high
  permissions: high
  billing: high
  destructive_migration: critical
  persistence: high
  concurrency: high
  public_api: medium
  ui: medium
human_gate:
  - destructive_migration
  - privilege_change
  - breaking_external_contract
  - production_config
```

`--auto` does not waive human gates for destructive/irreversible operations or missing product semantics.

## Review topology

In `hybrid`, provider diversity is mandatory for every implementation task before integration:

- Claude implementation → one task-scoped Codex review;
- Codex implementation → one task-scoped Claude review.

Scale the **reviewer model/effort** with task risk rather than skipping the review: bounded work uses Luna/low or Haiku/low; normal work uses Sol/medium or Sonnet/medium; deep work uses Sol/high or Opus/high; exceptional work may use Astra or Opus/xhigh.

For non-hybrid policies:

- low: worker self-review + orchestrator diff inspection;
- medium: add task reviewer when the change hits a contract/shared seam or evidence is weak;
- high: fresh task reviewer required, stronger model route, final cross-review where available;
- critical: plan/spec can proceed, but stop before the critical mutation unless explicitly authorized.

## Budgets

Default bounded resources:

```yaml
budget:
  max_cycles: 3
  max_worker_dispatches: 10
  max_codex_dispatches: 12
  max_review_dispatches: 14
  max_model_escalations: 3
  max_pr_repair_cycles: 3
```

Every worker, reviewer, and model escalation increments usage in `state.json`. On exhaustion, stop with `BUDGET_EXHAUSTED`; do not silently exceed the budget.

Budgets are guardrails, not targets. A small issue should use far less.
