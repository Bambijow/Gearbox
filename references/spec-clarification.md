# Spec clarification gate

Gearbox must not turn missing product intent into implementation guesses. Before planning or dispatching workers, requirements must be decision-complete enough that two reasonable implementations would not produce materially different externally observable behavior.

This gate applies to `/issue`, `/loop`, `/shape`, and the final convergence step of `/brainstorm`.

## Resolution order

For every apparent gap, resolve it in this order:

1. **Explicit requirement**: accepted spec, issue body, later authoritative user clarification, or clearly applicable issue comment.
2. **Current repository evidence**: executable behavior, tests, repository instructions, schemas, APIs, UI patterns, configuration, and current accepted docs.
3. **Relevant active solution memory**: use `docs/solutions/` as evidence about repository-specific invariants, never as permission to override newer requirements.
4. **Ask the user** when the remaining choice is materially product/domain-sensitive.

Do not ask for facts the repository can answer. Do not use an old convention to invent new product semantics merely because it is convenient.

## Three dispositions

Classify each gap as exactly one of these.

### DEDUCED

Use this when the answer is directly supported by current repository evidence and does not introduce a new product decision.

Examples:

- the repository already places equivalent destructive actions in the same existing action menu;
- an API error shape is standardized and tested everywhere;
- the project already has one canonical pagination contract.

Record the evidence briefly in the working spec or clarification artifact. Do not interrupt the user.

### ASSUMED

Use this only for a low-impact, reversible engineering choice whose alternatives do **not** materially change user-visible behavior, business/domain semantics, permissions, data retention, public contracts, migration behavior, billing, security, or safety.

Examples:

- reuse the existing notification component rather than adding another wrapper;
- follow the repository's current filename convention;
- use the existing test helper for a new case.

Make the assumption explicit in the working spec. `/plan` may later choose a better implementation if acceptance behavior remains unchanged.

### QUESTION

Ask when two reasonable answers would materially change the delivered behavior or risk surface. Typical blockers include:

- user-visible workflow or UX semantics;
- business/domain rules or state transitions;
- permissions, roles, authentication, or authorization;
- deletion, retention, archival, restoration, or irreversible data behavior;
- public API/CLI/event contracts or compatibility promises;
- billing or entitlement semantics;
- destructive or materially risky migrations;
- rollout/rollback semantics that affect users or stored data;
- contradictory requirements or acceptance scenarios.

`--auto` never converts QUESTION into ASSUMED.

## Issue-mode questioning

For `/issue` and non-conversational `/loop` inputs, investigate first, then ask **one compact batch** of all independent blocking questions discovered in that pass. Avoid a drip of one-question-at-a-time interruptions.

Each question should contain:

- a stable `id`;
- the decision needed;
- why it matters;
- what repository/issue evidence was checked;
- 2-3 concrete options when useful, with short consequences;
- free-form response allowed when the options are incomplete.

Do not recommend an option merely to avoid asking. You may identify an existing repository precedent as evidence, but the user still owns an unresolved product decision.

If one answer logically determines which later question is relevant, ask the independent blockers now and defer only the truly dependent branch. Normally finish clarification in one batch; use another batch only when the user's answer reveals a genuinely new blocker.

## Brainstorm-mode questioning

`/brainstorm` remains conversational. It may ask the highest-leverage question one at a time because exploration is the purpose of that entry point. Before materializing the accepted spec, however, run the same decision-completeness test and ensure no QUESTION remains unresolved.

## Persistent artifacts

Persist clarification state under the transient run directory:

```text
.gearbox/runs/<run-id>/
├── spec.md
└── spec-clarification.json
```

Suggested shape:

```json
{
  "status": "NEEDS_INPUT",
  "round": 1,
  "deductions": [
    {
      "id": "error-shape",
      "decision": "Reuse the existing validation error envelope",
      "evidence": ["tests/api/validation_test.ts", "src/http/errors.ts"]
    }
  ],
  "assumptions": [
    {
      "id": "notification-component",
      "decision": "Reuse the existing toast component",
      "reversible": true
    }
  ],
  "questions": [
    {
      "id": "archive-visibility",
      "decision": "Where should archived records remain visible?",
      "why": "The answer changes navigation and retrieval behavior",
      "evidence_checked": ["issue #123", "src/features/records"],
      "options": [
        {"id": "archives-view", "label": "Dedicated Archives view"},
        {"id": "search-only", "label": "Only through explicit search/filter"},
        {"id": "hidden", "label": "Not accessible from normal product UI"}
      ]
    }
  ],
  "answers": {}
}
```

When unresolved QUESTION entries exist:

- set `state.json.phase` to `SPEC`;
- set `state.json.status` to `BLOCKED`;
- set `state.json.blocker.code` to `SPEC_BLOCKED`;
- set `state.json.clarification.status` to `NEEDS_INPUT`;
- do not perform model preflight;
- do not dispatch implementation/review workers;
- do not create implementation worktrees;
- report the smallest set of decisions needed to resume.

When the user answers, persist answers, update the spec's decisions and acceptance scenarios, rerun only the contradiction/decision-completeness pass, mark clarification `RESOLVED`, clear the blocker, and continue from planning. Do not redo broad reconnaissance unless the answers materially changed the affected domain.

## Resume semantics

`/resume` on a `SPEC_BLOCKED` run must surface the stored unanswered questions directly. If the user answers in that resumed conversation, write those answers to the clarification artifact/state before continuing. Already-resolved deductions and assumptions are reused.

## Spec acceptance invariant

A spec may contain documented low-risk assumptions, but it is not implementation-ready while any material QUESTION remains unresolved. `Open decisions` in a spec are therefore either:

- explicitly non-blocking implementation choices delegated to `/plan`; or
- blockers that force `SPEC_BLOCKED` before planning.

Never hide a product blocker inside an `Open decisions` section and dispatch workers anyway.
