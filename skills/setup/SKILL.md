---
name: setup
description: "Configure Gearbox for the current repository: paths, validation, solution memory, model/effort routing, risk gates, execution budgets, Codex/Ponytail availability, and resumable run state."
argument-hint: "[optional setup preferences]"
disable-model-invocation: true
---
# Configure Gearbox for this repository

## Legacy migration

Before reading project configuration, Gearbox automatically checks for the former `.steelthread/` project directory. If `.gearbox/` does not exist and no legacy run lock is active, the plugin renames `.steelthread/` to `.gearbox/` and rewrites only internal path references from `.steelthread/` to `.gearbox/`. Do not ask the user to rename it manually. Branch names, issue/PR identifiers, evidence, and historical run IDs are preserved. If both directories already exist, stop and ask the user which one is authoritative instead of merging them silently.

Read repository instructions, build/CI manifests and existing docs. Reuse conventions rather than creating a parallel bureaucracy.

Detect specs/ADR/runbook locations, repository-native tests/lint/typecheck/build/e2e commands, GitHub remote/base branch, UI evidence tooling, `codex`, and Ponytail availability. Keep `docs/solutions/` canonical.

## Model preflight

If the user has not already stated a preference, ask once which worker policy to persist: `auto`, `hybrid` (recommended), `claude-heavy`, `codex-heavy`, or `custom`. For custom policy, record allowed Claude model aliases/full IDs, allowed Codex model IDs, and any role constraints. The preferred Codex registry is intentionally small: GPT-6 Luna for cheap bounded work, GPT-6.1 Sol for normal/deep engineering with effort scaling, and GPT-6 Astra only for exceptional escalation. Verify or adjust the exact CLI model IDs if the local Codex installation exposes different identifiers. Do not silently fall back to Codex's default model. The main Claude session remains the control-plane orchestrator; task routes are chosen later from risk/complexity. During orchestrated runs it does not author product code. Read `references/control-plane.md`.

## Config

Write/update `.gearbox/config.md` with known fields only:

```yaml
---
specs_dir: docs/engineering/specs
plans_dir: docs/engineering/plans
solutions_dir: docs/solutions
tracker: github
base_branch: main
max_parallel_workers: 3
max_cycles: 3
learning_policy: conditional
token_profile: efficient
execution_mode: delegated-control-plane
orchestrator_product_writes: forbidden
implementation_policy: workers-only
task_review_policy: cross-provider-in-hybrid
post_pr_policy: manual
model_selection: ask-once
model_policy: hybrid
claude_models:
  fast: haiku
  standard: sonnet
  deep: opus
codex_models:
  economy: gpt-6-luna
  standard: gpt-6.1-sol
  frontier: gpt-6-astra
allow_codex_default_model: false
codex_frontier_policy: escalation-or-exceptional
hybrid_review_policy: opposite-provider
budget:
  max_worker_dispatches: 10
  max_codex_dispatches: 12
  max_review_dispatches: 14
  max_model_escalations: 3
  max_pr_repair_cycles: 3
risk_policy:
  auth: high
  permissions: high
  billing: high
  destructive_migration: critical
  persistence: high
  concurrency: high
  public_api: medium
human_gate:
  - destructive_migration
  - privilege_change
  - breaking_external_contract
  - production_config
codex_bin: codex
ponytail: preferred
test_commands: []
check_commands: []
ui_commands: []
---
```

When `model_policy: hybrid`, `task_review_policy: cross-provider-in-hybrid` means every implementation task is reviewed once by the opposite provider before integration. The reviewer model is selected from the task tier with `scripts/review_router.py`; do not use a frontier reviewer for trivial work.

`ask-once` means a run prompts only when model policy is missing/unresolved, then offers to persist it. `--models ask` always prompts. If migrating an older Gearbox config, remove legacy intermediate Codex tiers and normalize to `economy=Luna`, `standard=Sol`, `frontier=Astra`.

Ensure `.gearbox/.gitignore` ignores `runs/`. Create/regenerate `docs/solutions/index.md` when solution notes already exist. Do not modify `CLAUDE.md` merely to advertise Gearbox.

## Control-plane enforcement

Gearbox ships `hooks/hooks.json` plus `scripts/orchestrator_guard.py`. Do not copy this hook into project settings. When the plugin is enabled, the plugin hook activates automatically for orchestrated front doors. Ensure `.gearbox/.gitignore` ignores transient `runs/`; the guard itself stores its per-session marker in the system temp directory, not in the repository.
