---
name: learn
description: "Capture a non-obvious engineering lesson from completed work into durable repo memory so future humans and agents do not repeat the same investigation. Use after notable bugs, decisions, migrations, or tricky changes."
argument-hint: "[incident, change, decision, or lesson]"
disable-model-invocation: true
---

# Compound the lesson, not the paperwork

## Orchestrated-run ownership

When `/learn` semantics are triggered inside `/issue`, `/loop`, `/flow`, `/resume`, or `/continue-pr`, the main orchestrator must delegate durable `docs/solutions/` mutation to the `knowledge-curator` agent. Direct `/learn` invocation by the user remains usable as a standalone maintenance command.

Create durable repo memory only when the information will materially shorten a future investigation or prevent recurrence.

## Qualification gate

Do **not** write a learning note for routine implementation details, obvious fixes, generic best practices, or facts already documented clearly elsewhere.

A note is warranted when at least one is true:

- the root cause was non-obvious;
- multiple plausible approaches failed and knowing why matters;
- an undocumented invariant or coupling was discovered;
- the repository's apparent architecture differed from its real behavior;
- an operational, migration, security, performance, or debugging trap could recur;
- a decision has consequences future work must respect.

## Canonical home: `docs/solutions/`

Before creating a new note, search `docs/solutions/` and relevant repository docs.

Every durable lesson created by `/learn` belongs in `docs/solutions/`. Do not redirect it to another learnings directory. Use one solution note per reusable problem/decision and update an existing matching note instead of creating a near-duplicate.

If current evidence shows an existing solution is stale, contradicted, duplicated, or replaced, do not create a second note that leaves both truths searchable. Reconcile the affected knowledge first using the same principles as `/clean-solutions`: refresh a partially valid note, merge overlapping notes, or delete a fully obsolete note after preserving any unique still-valid lesson. Git history is the archive.

Other documentation may be updated **in addition** when appropriate:

- Architecture decision with durable tradeoffs → also update/create the repository's ADR.
- Runbook or operational procedure → also update the runbook.
- Repository-wide agent rule → propose a small update to `CLAUDE.md` or `AGENTS.md` when appropriate.

The `docs/solutions/` note remains the compact, searchable record of what was learned, why it mattered, and how to recognize or avoid the problem next time.

## Learning note structure

Start each note with compact metadata for cheap retrieval:

```yaml
---
title: <current durable lesson>
tags: [domain, subsystem]
areas: [relevant/path/**]
verified_against: <current git sha>
last_verified: <YYYY-MM-DD>
---
```

Then write a compact note containing:

1. **Context / symptom**: enough to recognize the situation later.
2. **Root cause or key decision**: the durable insight, stated plainly.
3. **Why it was easy to get wrong**: misleading signals, hidden coupling, stale docs, surprising behavior.
4. **Failed or rejected approaches**: only those that teach something reusable.
5. **Resolution**: what worked and why.
6. **Prevention / detection**: test, invariant, monitoring, documentation, migration rule, or review heuristic.
7. **Pointers**: relevant code, tests, issue/PR, spec, ADR, or commands.
8. **Tags**: a few searchable domain terms.

Avoid a chronological diary. Future readers need the compressed model, not the full session transcript.

## Discoverability

Store the note under `docs/solutions/` using `YYYY-MM-DD-short-kebab-title.md`.

Regenerate or update `docs/solutions/index.md` using `scripts/solutions_index.py` when available. The index is the canonical cheap retrieval surface; a repository-specific `README.md` may coexist.

Prefer links to source files, tests, issues, PRs, ADRs, and commands over copied context. Keep the note compact enough to be cheap for future agents to retrieve.

Finish by stating which `docs/solutions/...` file was created or updated.
