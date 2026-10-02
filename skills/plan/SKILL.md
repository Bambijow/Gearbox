---
name: plan
description: "Convert a shaped request or specification into an implementation-ready dependency graph of small vertical slices, with verification and rollout steps. Use before non-trivial implementation."
argument-hint: "[spec path, issue, or request]"
disable-model-invocation: true
---

# Plan executable engineering work

Create a plan that another capable engineer or agent can execute without rediscovering the architecture.

## Ground the plan

Read `.gearbox/config.md` when present, repository instructions, the target spec or issue, and the relevant code/tests. Verify important symbols and paths instead of fabricating likely filenames.

For a broad codebase, use independent subagents only when discovery can be split cleanly, for example API surface, persistence, and test architecture. Reconcile their findings yourself.

## Build a dependency graph, not a shopping list

Break the work into the smallest coherent **vertical slices** that deliver or verify behavior end to end. Before listing units, extract a compact **Global Constraints** block containing only rules every unit must respect, such as compatibility floors, dependency limits, exact public copy/values, schema invariants, or repository-wide safety constraints. Do not repeat generic repository guidance.

Each unit should have:

- outcome;
- acceptance criteria/spec slice covered;
- dependencies / blockers;
- interfaces consumed and produced;
- exact or well-supported likely touch points;
- implementation notes limited to decisions already justified by the codebase;
- tests or verification proving completion;
- migration / rollout / rollback concerns when relevant.

Prefer slices that cross layers and prove integration over horizontal tasks like "create all models", then "create all services", then "write all tests".

Mark units that can run in parallel. Keep shared-file contention in mind before claiming parallelism.

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

Start with a short architecture summary, key decisions, and compact Global Constraints. Then provide ordered work units with dependency edges and explicit interfaces. End with a verification matrix mapping requirements to checks.

For substantial work, persist the plan in the configured plans directory. Link the originating spec by relative path when both are persisted.

Do not implement while running `/plan` unless the user explicitly asks to combine planning and execution. `/flow` exists for that purpose.
