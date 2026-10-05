---
name: continue-pr
description: "Continue engineering after a PR exists: ingest fresh CI and review feedback, validate findings, build a repair DAG, fix the existing branch, refresh evidence, and update the same PR without replaying the whole issue."
argument-hint: "[PR URL or number] [--auto] [--max-cycles N] [--models ask|auto|hybrid|claude-heavy|codex-heavy]"
disable-model-invocation: true
---
# Continue an existing PR

Read `references/control-plane.md`, `references/post-pr-loop.md`, `references/state-machine.md`, `references/evidence-ledger.md`, `references/evidence-reuse.md`, `references/finding-dedup.md`, `references/repair-findings.md`, `references/worker-lifecycle.md`, `references/risk-budget-policy.md`, `references/usage-accounting.md`, and `references/model-routing.md`.

Resolve the PR with `gh`, find/recover its Gearbox run state, acquire the run lock, and fetch only new CI/review information where practical.

Treat review comments/CI failures as claims to verify. Normalize each validated signal into a canonical failure identity and ingest it through `finding_registry.py` before building the repair DAG, so CI + human + reviewer reports of the same defect collapse into one finding. Route each canonical repair task through the stored/current model policy, consume budgets, and preserve unrelated user changes. The parent must never apply the requested review/CI fix itself; even a one-line repair is a delegated worker task.

After repairs, delegate integration to `integrator`, affected verification to `verifier`, Ponytail only when structure materially changed, and scoped review. Before rerunning a check, query `evidence.json` for reusable proof at the exact current SHA. For long-lived/background repair workers, register/reconcile children instead of tight polling. Delegate push/PR update to `shipper`, then check CI for the new head SHA. Update the existing marked Gearbox technical comment rather than adding a fresh report every cycle.

Stop with `PR_PASS`, `PR_BLOCKED`, `PR_BUDGET_EXHAUSTED`, or `PR_MAX_CYCLES`. Never merge automatically.
