---
name: spec-to-issues
description: "Split a large accepted spec into a GitHub epic plus a small dependency-aware set of implementation issues when one issue would be too broad, while keeping the spec as the requirements source of truth."
argument-hint: "[spec path] [--create] [--max-issues N] [--labels a,b]"
disable-model-invocation: true
---
# Split a large spec into coordinated issues

Use this only when the accepted spec contains independently deliverable slices that benefit from separate review/ownership. Do not split small work for ceremony.

Read the spec, repository boundaries and public contracts. Derive 2-8 outcome-oriented child issues by default. Each child must own a coherent acceptance slice and should be independently verifiable. Avoid splitting by arbitrary layers when that creates tightly coupled half-features.

Create a transient manifest containing epic title/body, child issue drafts, dependency edges and source spec path. The epic explains outcome, scope and links to children. Child issues include their slice, constraints, acceptance criteria, verification, dependencies, and `Source spec` pointer. Do not embed implementation DAG internals.

Without `--create`, stop at drafts. With `--create`, search for duplicates first, create the epic and children idempotently with `gh`, then edit/link bodies so dependencies use real issue numbers. Record created IDs in run state immediately.

Each child can enter `/issue`; the accepted spec remains source of truth. If children must land in a strict order, state the dependency explicitly.
