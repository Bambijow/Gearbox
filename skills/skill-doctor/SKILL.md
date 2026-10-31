---
name: skill-doctor
description: "Audit and reduce an agent skill/prompt ecosystem: trigger quality, overlap, progressive disclosure, prompt budgets, dead references, duplicated policy, deterministic-rule opportunities, and missing behavioral evals. Use when CLAUDE.md/AGENTS.md/plugins/skills have grown, collide, or become hard to maintain."
argument-hint: "[scope] [--fix]"
---

# Keep the agent environment small and legible

The default remedy is not another skill.

Read `references/skill-authoring.md`, `references/agent-writing.md`, `prompt-budgets.json` when present, and the relevant skills/steering files/evals.

## Audit

Inventory the selected agent-facing surfaces and report:

- trigger collisions: two skills likely to fire for the same intent;
- trigger holes: useful capability exists but descriptions make discovery unlikely;
- duplicate policy copied into several skills instead of a shared reference;
- skill bodies carrying conditional detail that should move behind a pointer;
- mechanical rules that should be lint/test/script/hook rather than prose;
- stale/dead references, examples or commands;
- prompt-budget hotspots and unnecessary always-loaded steering text;
- behavior-bearing changes with no discriminating eval;
- skills that should be merged, split, renamed or retired.

For each finding, name the retrieval/behavior failure it causes. Avoid style-only edits unless they reduce ambiguity or context cost.

## Fix mode

Without `--fix`, produce a ranked remediation plan.

With `--fix`, prefer deletions, merges and reference extraction before adding new skills. Preserve public command names unless there is a migration path. Update manifests, prompt budgets, docs and behavior evals together so the environment cannot drift half-migrated.

For changes that alter trigger or agent behavior, require a fresh read-only semantic reviewer following `references/skill-semantic-review.md`. Review only modified instructions and caller-shaped examples; do not authorize the original editor to certify its own rewrite.

Finish by running the repository's deterministic plugin validation, prompt-budget check and eval-schema validation when available.
