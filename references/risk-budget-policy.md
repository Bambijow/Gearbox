# Risk and execution budgets

Gearbox scales review and model spend with concrete risk. Review severity/action is calibrated by `references/review-calibration.md`; plausible failure cost, not maximal defensiveness, determines what blocks integration.

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

## Final integrated review depth

Per-task review topology above stays mandatory where configured. The **final integrated** review is separately routed by consequence using `references/final-review-routing.md` and `scripts/final_review_router.py`:

- `lite`: no new final model dispatch when task gates passed and failure is loud/local;
- `focused`: one fresh adversarial integration reviewer for silent/mixed or high-risk-but-bounded failure;
- `full`: comprehensive integration review for critical/high-consequence boundaries or material architecture/contract changes, plus a cross-provider peer in hybrid when available.

Changed-line count may force `full` only as a broad-change backstop. It can never earn `lite`. This keeps review spend proportional to plausible failure cost rather than diff cosmetics.

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
  max_total_tokens: null          # optional; only from measured/reported usage
  max_reported_cost_usd: null     # optional; no built-in pricing guesses
```

Every worker, reviewer, and model escalation increments usage in `state.json`. When provider/host token or cost telemetry exists, record it through `scripts/usage_ledger.py` under `references/usage-accounting.md`. Optional token/reported-cost caps apply only to actual telemetry or an explicit next-dispatch estimate; Gearbox never invents pricing. On exhaustion, stop with `BUDGET_EXHAUSTED`; do not silently exceed the budget.

Budgets are guardrails, not targets. A small issue should use far less.


## Repair breaker

Repair dispatches are additionally bounded per finding by `references/repair-findings.md` and `scripts/repair_findings.py`. The default allows two attempts with one material strategy before mandatory re-diagnosis and five total attempts before controller adjudication. Global cycle/dispatch budgets still win when they are lower.
