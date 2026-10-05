---
name: shape
description: "Turn a feature, change, or fuzzy engineering request into a decision-complete specification grounded in the current codebase. Use before planning when requirements or domain boundaries are still unclear."
argument-hint: "[feature, problem, GitHub issue, spec, or change request]"
disable-model-invocation: true
---

# Shape the work before planning it

Produce a specification that is precise enough to plan without pretending implementation decisions are already settled. If the destination itself is clear but the route is hidden behind multiple unresolved decision clusters that cannot reasonably converge in one shaping session, stop and recommend `/gearbox:wayfinder` instead of manufacturing a giant speculative spec. For a genuinely conversational exploration where the user wants to talk through alternatives before a spec exists, `/brainstorm` is the preferred front door and uses this shaping discipline only after the product/domain decisions converge.

## First, ground yourself

If the input is a GitHub issue URL or number, resolve it with `gh issue view` and treat the issue body/comments as the requested outcome and constraints. Verify claims against the current repository before turning them into the spec. This is the explicit issue-to-spec path when the user wants shaping without running the full `/issue` loop.

Read `.gearbox/config.md` when present. Read relevant repository instructions. Inspect the existing code paths, tests, schemas, APIs, and configuration touched by the request. Apply `references/domain-modeling.md`: read the relevant glossary context when present and use its canonical terms before inventing new names.

Separate three buckets:

- **Observed**: behavior or constraints verified in the repository.
- **Requested**: outcomes the user explicitly wants.
- **Open**: decisions that materially change scope, UX, compatibility, data shape, safety, or rollout.

Do not interrogate the user about things the repository can answer. When a material decision depends on current external facts rather than product preference, dispatch `researcher` using `references/research.md`; carry the conclusion and note path into shaping instead of browsing broadly in the parent context. Apply `references/spec-clarification.md`: classify gaps as DEDUCED, low-risk/reversible ASSUMED, or blocking QUESTION. Ask only for genuinely consequential unknowns. For issue/non-conversational shaping, prefer one coherent batch of independent blocking questions over a long drip of trivial confirmations. `--auto` never authorizes inventing product semantics.

## Shape the domain

Make terms explicit. If two words appear to mean the same thing, resolve the vocabulary. If one word hides two concepts, split it. Reuse the repository's existing language unless it is demonstrably causing confusion.

When a canonical term becomes materially clearer, delegate the smallest glossary edit to `domain-curator` after the decision is settled. If a hard-to-reverse, surprising architecture choice with real alternatives is resolved, the same curator may record a compact ADR. Do not turn every implementation choice into an ADR.

## Specification content

A useful spec contains:

1. **Problem / outcome**: what changes for the user, operator, or system.
2. **Current behavior**: only the relevant verified baseline.
3. **In scope / out of scope**: sharp boundaries.
4. **Behavioral requirements**: observable outcomes, including important failure behavior.
5. **Domain and data rules**: invariants, state transitions, ownership, compatibility constraints.
6. **Interfaces**: API, CLI, UI, events, configuration, or operational touch points when relevant.
7. **Acceptance scenarios**: concrete examples that can later become tests.
8. **Operational concerns**: migration, rollout, observability, security, performance, rollback, or backwards compatibility when material.
9. **Open decisions**: only unresolved items that truly block planning.

Avoid implementation task lists in the spec. A spec describes the destination and constraints; `/plan` decides the route. Keep ordinary specs compact: include only facts and decisions downstream workers/reviewers will actually need, rather than preserving the whole discovery narrative.

## Persisting

If the request is substantial enough to survive beyond the current session, save the spec in the configured specs directory using the artifact naming convention. If it is tiny, keep the result in the conversation instead of creating documentation debris.

Before finishing, run a contradiction pass: compare the spec against the code and any existing docs you relied on. Call out stale docs rather than quietly choosing whichever story is convenient. A spec is not planning-ready while `references/spec-clarification.md` has unresolved blocking QUESTION entries; persist them and return `SPEC_BLOCKED` rather than guessing.
