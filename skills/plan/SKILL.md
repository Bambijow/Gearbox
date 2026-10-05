---
name: plan
description: "Convert a shaped request or specification into an implementation-ready dependency graph of small vertical slices, with verification and rollout steps. Use before non-trivial implementation."
argument-hint: "[spec path, issue, or request]"
disable-model-invocation: true
---

# Plan executable engineering work

Create a plan that another capable engineer or agent can execute without rediscovering the architecture.

## Ground the plan

Read `.gearbox/config.md` when present, repository instructions, the target spec or issue, and the relevant code/tests. Apply `references/planning-contract.md`, `references/domain-modeling.md` when domain language matters, and `references/frontier-scheduling.md` for executable DAG metadata. Verify important symbols and paths instead of fabricating likely filenames.

Before any auxiliary discovery/design dispatch, apply `references/delegation-gate.md` and record the dispatch reason. Broad discovery may be split only when flood protection or true independent parallel work pays for it. If a shared interface/seam is hard to reverse and reasonable designs differ, the fresh independent judgment of `design-proposer` satisfies that gate; apply the `references/codebase-design.md` design-it-twice contract before committing the plan.

## Build a dependency graph, not a shopping list

Break the work into the smallest coherent **vertical slices** that deliver or verify behavior end to end. Before listing units, extract a compact **Global Constraints** block containing only rules every unit must respect, such as compatibility floors, dependency limits, exact public copy/values, schema invariants, or repository-wide safety constraints. Do not repeat generic repository guidance.

Each unit should have:

- outcome;
- acceptance criteria/spec slice covered;
- dependencies / blockers;
- `ready_when`: the exact dependency/decision condition that places the task on the ready frontier;
- interfaces consumed and produced;
- owned write surface plus known shared seams;
- context pointers (glossary/ADR/research/solution/source) needed by this task, without copied bulk context;
- exact or well-supported likely touch points;
- implementation notes limited to decisions the capable implementer cannot safely choose alone; prefer exact signatures/values/assertions over function bodies;
- tests or verification proving completion, including the `references/test-credibility.md` seam when behavior-bearing tests are planned;
- optional `batch_key` + `batch_members` only for low-risk same-shape micro-work that qualifies under `references/frontier-scheduling.md`;
- migration / rollout / rollback concerns when relevant.

Prefer slices that cross layers and prove integration over horizontal tasks like "create all models", then "create all services", then "write all tests".

Model parallelism as a ready frontier rather than a static wave. Keep shared-file contention in mind before declaring tasks simultaneously ready. A task whose dependencies are integrated may start immediately even while unrelated tasks continue. Collapse qualifying low-risk same-shape micro-tasks into one batch dispatch/review unit rather than paying one fresh worker and reviewer per trivial edit.

## Plan quality checks

Before finalizing, challenge the plan:

- Is there a smaller first slice that proves the risky assumption?
- Are any tasks merely cleanup disguised as requirements?
- Are data migrations reversible or at least recoverable?
- Are compatibility boundaries explicit?
- Does every requirement map to at least one implementation unit or verification step?
- Is every implementation unit justified by a requirement, risk reduction, or necessary enabling work?
- Are observability and operational validation included where production behavior could fail silently?
- Do adjacent tasks agree on their interfaces?
- Would any reviewer immediately reject something the plan itself requires?
- Are tasks right-sized to earn one meaningful test cycle and one useful review unit, with trivial same-shape work batched instead of fragmented?
- Does `## Review Focus` contain at most five plausible failure modes implied by the requested behavior, each owned by a task/check when testable?
- Is the plan proportionate to the spec, or has it started writing implementation bodies the worker can derive?

## Output format

Start with a short architecture summary, key decisions, canonical domain pointers, and compact Global Constraints. Add a `## Review Focus` section with 0-5 items. Then provide dependency-graph work units with explicit interfaces/ownership/`ready_when` and batch metadata when applicable. Add `## Initial ready frontier` with task ids. End with a verification matrix mapping requirements to checks.

For substantial work, persist the plan in the configured plans directory. Link the originating spec by relative path when both are persisted. After writing, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plan_guard.py" --plan <plan> --require-dag` and add `--spec <spec>` when the spec is persisted. Fix guard failures before handoff.

Do not implement while running `/plan` unless the user explicitly asks to combine planning and execution. `/flow` exists for that purpose.
