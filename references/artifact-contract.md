# Gearbox artifact contract

Gearbox stores durable engineering context in the repository only when it earns its keep.

Defaults, unless `.gearbox/config.md` overrides them. The `/learn` solution location is intentionally canonical and should not be redirected:

- Specifications: `docs/engineering/specs/`
- Implementation plans: `docs/engineering/plans/`
- Reusable solutions / learnings from `/learn`: `docs/solutions/`. Treat this as current active memory, not an append-only archive; `/clean-solutions` may refresh, merge, or delete stale entries. Git history preserves retired knowledge.
- Handoffs: `docs/engineering/handoffs/`
- Brainstorm decision ledgers, issue drafts, `state.json`, `spec-clarification.json`, `evidence.json`, task packets, logs, and engineering-loop state: transient under `.gearbox/runs/`; do not persist unless the repository already has an explicit convention. The accepted spec, not the brainstorm transcript, is the durable artifact.
- Architecture decisions: use an existing ADR location if the repository already has one; otherwise do not invent an ADR directory unless the decision is genuinely architectural.

## Naming

Use `YYYY-MM-DD-short-kebab-title.md` for durable artifacts. Reuse an existing artifact when continuing the same piece of work instead of creating near-duplicates.

## What deserves persistence

Persist information that another engineer or a future agent would benefit from without replaying the original investigation. Do not persist transient scratch notes, obvious facts, or verbose session logs.

## Source of truth order

When sources conflict, prefer in this order:

1. Executable behavior and tests
2. Current repository instructions (`CLAUDE.md`, `AGENTS.md`, contributing docs)
3. Current code and configuration
4. Accepted specs / ADRs
5. Historical learnings
6. Comments and stale prose

Never silently rewrite history to hide a contradiction. Surface it and resolve it. When an old solution is conclusively superseded and no unique current lesson remains, deleting the stale working-tree note is preferred to leaving contradictory searchable guidance; git history remains the historical record.
