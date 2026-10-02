# Persistent run state and idempotence

Every substantial Gearbox run is a resumable state machine under `.gearbox/runs/<run-id>/`.

The canonical machine state is `state.json`, not conversation memory. Use `scripts/run_state.py` for initialization, locking, transitions and budget accounting when practical.

## Minimum state

```json
{
  "schema_version": 3,
  "run_id": "issue-123",
  "status": "ACTIVE",
  "phase": "IMPLEMENT",
  "cycle": 0,
  "source": {},
  "git": {"base_sha": null, "head_sha": null, "branch": null},
  "github": {"issue": null, "pr": null, "technical_comment_id": null},
  "completed": {},
  "pending": [],
  "worktrees": [],
  "budgets": {},
  "usage": {},
  "model_policy": {},
  "model_assignments": {},
  "orchestration": {"mode": "delegated-control-plane", "product_writes": "workers-only"},
  "clarification": {"status": "UNSET", "round": 0, "questions": [], "answers": {}},
  "blocker": null,
  "learning": {},
  "last_error": null
}
```

Phases normally progress through `INTAKE`, `SPEC`, `PLAN`, `MODEL_PREFLIGHT`, `IMPLEMENT`, `INTEGRATE`, `SIMPLIFY`, `REVIEW`, `VERIFY`, `LEARN`, `SHIP`, `POST_PR`, and `DONE`. `BLOCKED` and `MAX_CYCLES` are terminal-until-resumed states. A requirements ambiguity uses `status=BLOCKED`, `phase=SPEC`, and `blocker.code=SPEC_BLOCKED`; keep the actual questions in both the compact clarification state and `spec-clarification.json`.


## Control-plane state

Orchestrated runs persist `orchestration.mode=delegated-control-plane` and `product_writes=workers-only`. Runtime tool enforcement is turn-scoped through the plugin hook and is reactivated by `/resume`; persistent state exists for audit/resume semantics, not as the only enforcement mechanism.

## Spec clarification persistence

Before planning, apply `references/spec-clarification.md`. When material product/domain questions remain unresolved, persist them before returning control to the user. A blocked example:

```json
{
  "status": "BLOCKED",
  "phase": "SPEC",
  "clarification": {
    "status": "NEEDS_INPUT",
    "round": 1,
    "questions": ["archive-visibility", "restore-behavior"],
    "answers": {}
  },
  "blocker": {
    "code": "SPEC_BLOCKED",
    "message": "Material product decisions are required before planning"
  }
}
```

No worker/reviewer/model-selection budget is consumed while this blocker is active. `/resume` surfaces those questions, records answers, updates the spec and acceptance criteria, then transitions back to `ACTIVE` only after the clarification gate is resolved.

## Locks

Acquire the run lock before changing run state or dispatching workers. If a lock exists, do not start a second orchestrator blindly. Inspect lock metadata and only break a stale lock after confirming the owning process/session is gone.

## Resume

`/resume` reads state first, validates repository/branch/base assumptions, reconciles current HEAD, and continues from the first incomplete gate. Completed workers with valid evidence at the same commit are not relaunched.

If source files changed outside Gearbox since the stored head, classify the drift. Small compatible user changes may be reconciled; material drift invalidates affected evidence and tasks only. Never throw away unrelated user work.

## Idempotent remote actions

- If `github.pr` is already recorded and still exists, update it instead of creating a duplicate.
- Technical comments use a stable marker such as `<!-- gearbox-report:v1 -->`; update the existing marked comment when possible.
- Spec-to-issue and spec-to-issues search for existing tracker artifacts before creating duplicates.
- Store remote IDs/URLs immediately after successful creation.

## Worktree cleanup

Track every temporary worktree path and branch in state. Prefer `scripts/run_state.py cleanup-worktrees --run-dir <run> --repo <repo>` for deterministic cleanup. On PASS/BLOCKED/failure, remove only Gearbox-owned worktrees that are clean or whose work has already been integrated. Never force-delete a worktree containing unintegrated changes without recording/recovering them.
