---
name: wayfinder
description: "Map a large or foggy initiative as a decision graph before implementation. Creates/resolves decision issues, uses focused research and domain modeling, and hands off only when the route to a spec or implementation plan is clear."
argument-hint: "[idea | map issue URL/number] [--create] [--auto-research]"
disable-model-invocation: true
---

# Wayfind before you build

Use this when the initiative is too large, too uncertain, or too cross-cutting to fit safely into one brainstorm/spec session.

Wayfinder discovers the **route**. It does not implement the destination.

A Wayfinder unit is a **decision ticket**: a question whose resolution changes what should be built, not an implementation slice.

Read:

- `references/domain-modeling.md` for canonical vocabulary and ADR rules;
- `references/research.md` for external/primary-source investigation;
- `references/agent-writing.md` when the route may change agent-facing docs;
- `references/codebase-design.md` only for hard-to-reverse module/interface/seam decisions;
- `references/token-efficiency.md` for context-pointer discipline.

## Two modes

### Chart a new map

Input is a loose initiative.

1. **Name the destination.** State in 1-2 sentences what “the fog is cleared” means. Usually this is an accepted spec, a hard architectural decision, or a migration strategy. Do not define implementation tasks yet.
2. **Ground the vocabulary.** Read the relevant `GLOSSARY.md` or `GLOSSARY-MAP.md` if present. If a domain term is genuinely being resolved, use `domain-curator` only after the user decision is clear.
3. **Breadth-first uncertainty scan.** Identify the few questions whose answers materially change scope, domain semantics, data shape, compatibility, security, rollout, or architecture.
4. Classify each visible question:
   - `research`: a fact from primary external/local sources is missing;
   - `prototype`: a cheap concrete artifact is needed to decide;
   - `grilling`: a human/product decision is needed;
   - `task`: a prerequisite action must happen before a decision can be made.
5. Put fuzzy-but-not-yet-askable areas under **Not yet specified**. Do not create fake precision just to fill the map.
6. Put ruled-out work under **Out of scope**.
7. If `--create` is absent, persist a draft under `.gearbox/runs/wayfinder-<slug>/map.md` plus issue drafts and stop.
8. If `--create` is present, create one GitHub map issue plus decision issues. Prefer GitHub native sub-issues/blocking when available; otherwise include `Parent map: #<n>` and explicit `Blocked by: #...` pointers in bodies. Use labels such as:
   - `gearbox:wayfinder-map`
   - `gearbox:wayfinder-research`
   - `gearbox:wayfinder-prototype`
   - `gearbox:wayfinder-grilling`
   - `gearbox:wayfinder-task`
   Create labels best-effort; failure to create a label must not destroy the map.
9. For independent research tickets, dispatch `researcher` agents in parallel when `--auto-research` is set. Store findings by pointer rather than pasting them into the map.
10. Stop after charting. Do not silently start implementation.

### Work an existing map

Input is a map issue.

1. Load only the map body and the **ready frontier**: open, unblocked, unclaimed decision tickets.
2. If the user named a ticket, take it. Otherwise choose the first highest-leverage frontier ticket.
3. Claim it before doing work when the tracker supports assignment/claiming.
4. Resolve exactly one non-research decision ticket in this session. Independent research tickets may run in parallel.
5. Record the answer in the ticket, close it, and append only a one-line gist + link to **Decisions so far** on the map.
6. Recompute the frontier. Promote newly-sharp fog into decision tickets; delete or close invalidated tickets instead of leaving zombies.
7. If the decision is hard to reverse, surprising without context, and the result of a real trade-off, ask `domain-curator` to record a compact ADR.
8. When no unresolved decision or fog remains before the destination, hand off:
   - destination = spec → materialize via the normal Gearbox shaping/spec contract;
   - destination = architecture decision → point the next `/gearbox:plan` or `/gearbox:loop` at the resolved map;
   - destination = migration strategy → produce the decision-complete migration spec/plan input.

## Map format

```markdown
## Destination
<what being done with wayfinding means>

## Notes
<standing constraints, domain pointers, research pointers>

## Decisions so far
- [Decision title](link): <one-line answer>

## Not yet specified
- <fog that is in scope but not yet sharp enough to ticket>

## Out of scope
- <explicit boundary and why>
```

## Decision ticket format

```markdown
## Question
<one decision-sized question>

## Context pointers
- <spec/glossary/research/code pointers only when needed>

## Parent map
<link or issue number>

## Blocked by
<issue links when applicable>
```

Do not paste the whole map/spec into each ticket.

## Completion criterion

Wayfinding is complete only when a capable planner could proceed without inventing a material product/domain/architecture decision.

If the remaining work is merely “build it”, stop wayfinding and hand off. That is success, not unfinished planning.
