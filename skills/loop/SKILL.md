---
name: loop
description: "Run Gearbox as a convergent engineering loop from a GitHub issue, accepted spec, or grounded request until quality gates pass, the work is blocked, or the cycle limit is reached. Includes adaptive repairs, conditional learn, and optional shipping."
argument-hint: "[GitHub issue | spec path | request] [--auto] [--ship] [--max-cycles N] [--workers N] [--no-codex] [--token-profile efficient|strict] [--models ask|auto|hybrid|claude-heavy|codex-heavy] [--follow-pr]"
disable-model-invocation: true
---

# Run the engineering loop

Read `references/control-plane.md` and `references/engineering-loop.md`, `references/engineering-rules.md`, `references/spec-clarification.md`, `references/token-efficiency.md`, `references/model-routing.md`, `references/state-machine.md`, `references/evidence-ledger.md`, and `references/risk-budget-policy.md`. Use them as the canonical loop semantics rather than inventing another pipeline.

## Normalize the input

- GitHub issue: resolve it with `gh issue view`, then create the minimal issue-derived spec before planning.
- Spec path: read and validate the spec against the current repository. Do not rewrite it unless code evidence reveals a contradiction or a decision is missing.
- Free-form request: normalize it into the minimal decision-complete spec required by `references/spec-clarification.md`; do not assume another slash command is loaded.

Use `.gearbox/config.md` when present. Default to `token_profile: efficient` and the configured cycle limit, otherwise 3.

Before planning, run the spec clarification gate. Resolve facts from the repo first; make only low-risk reversible engineering assumptions. If material product/domain semantics remain unresolved, persist the compact question batch, set `BLOCKED` with `SPEC_BLOCKED`, and stop before model selection or worker dispatch.

`--auto` authorizes ordinary engineering decisions inside the normalized scope and allows repair cycles to proceed without routine checkpoints. It never authorizes destructive production actions, secret access, merge, deploy, or invented product semantics.

`--ship` authorizes commit, push, PR creation/update and PR comments only after the loop reaches PASS.

Initialize persistent run state before spec clarification so any blocker is resumable. After clarification resolves and DAG preflight completes, initialize/refresh evidence and resolve model policy. If no policy is stored, ask which allowed model strategy to use and offer to persist it. Then assign every task an engine, model, effort and risk class. In `hybrid`, also precompute its opposite-provider review route with `scripts/review_router.py` so a Claude task is reviewed by Codex and a Codex task is reviewed by Claude before integration. For every Codex candidate, call `scripts/model_router.py` with the task classification and persist its concrete model/effort result in `dag.yaml`; do not choose a Codex model ad hoc or fall back silently to the Codex CLI default. `--models ask` forces this prompt; other `--models` values override for the run.

## Execute to convergence

Follow the shared loop protocol:

1. minimal SDD spec and acceptance mapping;
2. spec clarification gate with repository deductions, explicit assumptions, or `SPEC_BLOCKED`;
3. relevant glossary/domain pointers, `docs/solutions/` lookup, isolated research when needed, and architecture reconnaissance;
4. pre-flighted dependency DAG with ready-frontier metadata;
5. bounded Claude/Codex workers with isolated write worktrees, dispatched continuously from the ready frontier;
6. TDD where useful;
7. central diff inspection + opposite-provider task review;
8. delegated mechanical integration via `integrator`;
9. Ponytail post-integration simplification;
10. independent review;
11. delegated repository-native verification/UI evidence via `verifier`;
12. targeted worker repair cycles for validated failed gates;
13. conditional learning through `knowledge-curator`;
14. optional publication through `shipper`.

Do not restart the entire workflow after a failed gate. Later cycles operate on the delta and prior evidence.

## Finish states

Report exactly one final loop state:

- `PASS`: convergence achieved. State cycle count, acceptance evidence, checks, simplification, review, learning result, shipping state, and whether `/gearbox:retro` is recommended.
- `BLOCKED`: state the concrete blocker, completed evidence, current branch/worktree state and the smallest decision/action needed to resume.
- `MAX_CYCLES`: state unresolved validated findings and evidence. Do not claim success and do not ship.

For GitHub issue inputs, `/issue` is the shorter convenience entry point to this same loop.

## Post-PR continuation

When `--follow-pr` is present with `--ship`, continue through `references/post-pr-loop.md` after the PR is opened, bounded by `max_pr_repair_cycles`. Without it, create/update the PR and leave later CI/review repair to `/continue-pr`.
