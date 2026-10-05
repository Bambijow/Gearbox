---
name: plan
description: "Convert a shaped request or specification into an implementation-ready dependency graph of small vertical slices, with verification and rollout steps. Use before non-trivial implementation."
argument-hint: "[spec path, issue, or request]"
disable-model-invocation: true
---

# Plan executable engineering work

Create a plan that another capable engineer or agent can execute without rediscovering the architecture.

## Ground the plan

Read `.gearbox/config.md` when present, repository instructions, the target spec or issue, and the relevant code/tests. Apply `references/domain-modeling.md` when domain language matters and `references/frontier-scheduling.md` for executable DAG metadata. Verify important symbols and paths instead of fabricating likely filenames.

For a broad codebase, use independent subagents only when discovery can be split cleanly, for example API surface, persistence, and test architecture. Reconcile their findings yourself. If a shared interface/seam is hard to reverse and reasonable designs differ, apply the `references/codebase-design.md` design-it-twice gate with parallel `design-proposer` agents before committing the plan.

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
- implementation notes limited to decisions already justified by the codebase;
- tests or verification proving completion;
- migration / rollout / rollback concerns when relevant.

Prefer slices that cross layers and prove integration over horizontal tasks like "create all models", then "create all services", then "write all tests".

Model parallelism as a ready frontier rather than a static wave. Keep shared-file contention in mind before declaring tasks simultaneously ready. A task whose dependencies are integrated may start immediately even while unrelated tasks continue.

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
- Are tasks right-sized to earn one meaningful test cycle and, when risk warrants it, one bounded review pass?

## Output format

Start with a short architecture summary, key decisions, canonical domain pointers, and compact Global Constraints. Then provide dependency-graph work units with explicit interfaces/ownership/`ready_when`. State the **Initial ready frontier** by task id. End with a verification matrix mapping requirements to checks.

For substantial work, persist the plan in the configured plans directory. Link the originating spec by relative path when both are persisted.

Do not implement while running `/plan` unless the user explicitly asks to combine planning and execution. `/flow` exists for that purpose.
