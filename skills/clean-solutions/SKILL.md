---
name: clean-solutions
description: "Audit Gearbox durable memory in docs/solutions against the current repository and newer knowledge; refresh, merge, or delete notes that are stale, contradicted, duplicate, or no longer applicable. Use periodically and after removals, migrations, or architecture changes."
argument-hint: "[scope/path/domain] [--dry-run]"
disable-model-invocation: true
---

# Keep `docs/solutions/` true, small, and useful

Treat `docs/solutions/` as active engineering memory, not an append-only archive. Git history is the archive.

The goal is to make future humans and agents **less likely to retrieve false or redundant guidance** while preserving the reusable insight that still matters.

## Modes

- `/clean-solutions` audits the canonical `docs/solutions/` corpus.
- `/clean-solutions <scope>` limits the audit to a domain, path, subsystem, tag, or matching solution set.
- Add `--dry-run` to produce the proposed actions without modifying files.

Prefer scoped cleanup when the corpus is large or when a migration/removal gives a natural boundary.

## Evidence rule

Never retire a solution merely because it is old.

A note becomes a cleanup candidate only when current evidence suggests one or more of these:

- referenced code, config, commands, tests, or paths were removed or materially changed;
- a statement in the note conflicts with current executable behavior or repository instructions;
- a newer solution, accepted spec, ADR, migration, or implementation explicitly replaces it;
- the feature/subsystem no longer exists;
- two or more notes now teach the same durable lesson;
- the note contains a mixture of still-valid insight and stale implementation detail.

Use the repository source-of-truth order from `references/artifact-contract.md`, but do **not** blindly canonize accidental implementation drift. If current code conflicts with an accepted contract/spec/ADR and it is unclear which side is intended, classify the note as `BLOCKED` rather than rewriting knowledge around a possible bug.

## Token-efficient audit

Do not deep-read the whole corpus by default.

1. Run `scripts/solutions_audit.py` when available, then inventory `docs/solutions/` cheaply: filenames, titles, tags, index entries, `retire_when` triggers, pointers, and git last-change metadata when useful.
2. Search for obvious invalidation signals: satisfied `retire_when` conditions, missing referenced paths/symbols, duplicate domain terms, newer related notes, removed subsystems, changed config keys, and broken links. Retirement triggers are priority candidates because they name exactly what changed; verify the condition before acting.
3. Group candidates by domain.
4. Deep-read only the suspect notes plus the minimum current code/tests/specs/ADRs needed to establish truth.
5. For very large corpora, work in bounded batches and leave a compact summary of what was and was not audited.

Do not spawn a reviewer swarm for documentation hygiene. One orchestrator pass is normally enough. Before any auxiliary agent, apply `references/delegation-gate.md`; use another agent only when independent judgment or flood protection genuinely pays for the dispatch.

## Classification

Give every audited candidate one action:

### `KEEP`

The durable lesson is still true and useful. Do not churn wording for style alone.

### `REFRESH`

The lesson is still valuable but some details are stale. Rewrite the smallest amount needed so the note describes current truth. Preserve useful root-cause reasoning, traps, failed approaches, and prevention guidance that remain valid.

### `MERGE`

Multiple notes overlap enough that retrieval is noisy. Pick the best canonical note, move only unique still-valid insight into it, update pointers/index entries, then delete the redundant notes.

### `DELETE`

Delete a note when all of these are true:

- its guidance is no longer applicable or is now false;
- no unique reusable lesson remains after checking related current notes;
- keeping it would make future retrieval worse.

Do not leave a `SUPERSEDED` tombstone in `docs/solutions/` by default. Git history already preserves the old file. If a historical fact is still operationally relevant, fold that fact into the current canonical note instead.

### `BLOCKED`

Use this when truth cannot be established safely, for example when code, tests, specs, and ADRs materially disagree. Explain the conflict and leave the note untouched.

## Cleanup procedure

1. Establish the audit scope.
2. Build the cheap inventory and suspect list.
3. Validate suspects against current repository evidence and, for `retire_when`, the named external/version source. A trigger is evidence to investigate, not automatic deletion.
4. Produce an action plan with evidence for each `REFRESH`, `MERGE`, `DELETE`, or `BLOCKED` candidate.
5. Unless `--dry-run` is present, apply safe documentation-only changes.
6. Regenerate/repair `docs/solutions/index.md` (prefer `scripts/solutions_index.py`) and update `README.md` only if the repository uses it.
7. Repair links between solution notes when a merge/delete changes targets.
8. Re-scan the affected subset for dangling references and duplicate current guidance.
9. Run `scripts/solutions_audit.py --strict --check-index` after mutations so malformed metadata/index drift cannot ship.

Do not modify product code to make it agree with a solution note. The notes follow established current truth, never the reverse.

## Interaction with `/learn`

`/learn` must not create a new note beside an older contradictory one and walk away.

When a new lesson invalidates or replaces existing `docs/solutions/` knowledge, reconcile the affected notes using the same `REFRESH` / `MERGE` / `DELETE` rules before adding new durable memory. Prefer one current canonical truth over a stack of chronological corrections.

A full-corpus cleanup remains manual; the engineering loop should only reconcile solution notes it actually touched or proved stale during the current work.

## Final report

Finish with a compact summary containing:

- scope audited;
- `KEEP` count;
- files refreshed;
- merges performed and surviving canonical note;
- files deleted;
- blocked contradictions that need human/product resolution;
- whether `docs/solutions/README.md` changed.

For destructive-looking changes, include the evidence that made deletion safe. Remember that deletion from the working tree is reversible through git history.
