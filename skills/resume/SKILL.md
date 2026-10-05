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

Continue from the first incomplete or invalidated gate. If `status=AWAITING_APPROVAL` with `blocker.code=PLAN_APPROVAL_REQUIRED`, do not continue implementation by default. Show the stored compact plan summary/routing and stop. Only when `--approve-plan` is explicitly supplied, or the same conversation contains an unambiguous approval of that exact currently presented plan, call `run_state.py plan-approve` while holding the lock; if the digest check fails, present the changed plan and request approval again. Re-enter delegated control-plane mode: the parent may inspect and schedule, but every product mutation remains worker-owned. If the prior stop was `BLOCKED` with `blocker.code=SPEC_BLOCKED`, surface the persisted unanswered clarification questions directly, record the user's answers, update the working spec/acceptance scenarios, rerun the compact contradiction/completeness check, then clear the blocker before planning. Do not redo broad reconnaissance unless an answer materially changes the domain. For other `BLOCKED` states, verify the blocker is resolved before proceeding. If it was `BUDGET_EXHAUSTED`, require an explicit budget increase. `--approve-plan` authorizes only the currently hashed implementation plan; it does not waive spec blockers, human safety gates, budgets, merge/deploy restrictions, or future materially changed plans. Preserve model assignments unless the user changed model policy or an assigned model is unavailable.

Release the lock on orderly completion. Never create a second PR when state already records one.
