---
name: resume
description: "Resume an interrupted Gearbox run from persistent state without replaying completed workers or broad discovery. Reconcile git drift, stale locks, budgets, evidence and remote IDs before continuing."
argument-hint: "[run-id | issue number | PR number] [--approve-plan] [--break-stale-lock]"
disable-model-invocation: true
---
# Resume a Gearbox run

Read `references/control-plane.md`, `references/state-machine.md`, `references/spec-clarification.md`, `references/evidence-ledger.md`, `references/evidence-reuse.md`, `references/worker-lifecycle.md`, `references/usage-accounting.md`, `references/model-routing.md`, and the shared engineering loop.

Locate the matching `.gearbox/runs/<run-id>/state.json`. Acquire its lock. If no exact run exists, show plausible matches rather than guessing.

Validate repository identity, branch, stored base/head SHAs, worktrees, existing issue/PR IDs, budget usage and evidence. Reconcile `children.json` before redispatching anything: recover non-empty expected artifacts, surface stale/orphaned children, and do not duplicate live work. Reconcile external git drift conservatively. Completed work at the same relevant SHA with reusable evidence is not rerun.

Continue from the first incomplete/invalid gate. For `AWAITING_APPROVAL` + `PLAN_APPROVAL_REQUIRED`, show the stored plan/routing and stop unless `--approve-plan` is supplied or this conversation contains unambiguous approval of that exact plan. Then call `run_state.py plan-approve` while locked; a digest mismatch means show the changed plan and ask again. Product mutation stays worker-owned. For `SPEC_BLOCKED`, surface stored questions, record answers, refresh spec/acceptance, recheck completeness, then clear the blocker. Do not redo broad reconnaissance unless answers change the domain. Other blockers must be resolved first; `BUDGET_EXHAUSTED` needs an explicit increase. Plan approval never waives safety gates, budgets, merge/deploy restrictions, or later materially changed plans. Preserve model assignments unless policy/model availability changed.

Release the lock on orderly completion. Never create a second PR when state already records one.
