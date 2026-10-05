# Ready-frontier scheduling

Gearbox executes a dependency DAG as a changing **ready frontier**, not a static list.

A task is on the ready frontier when:

- every declared dependency has passed task review and is integrated;
- required spec/domain decisions are resolved;
- its owned write surface does not conflict with another active task unless the interface is explicitly coordinated;
- the task packet has enough pointers to start without broad rediscovery.

## Same-shape micro-batching

Before dispatch, look for multiple ready nodes that are all:

- low risk;
- independent with no dependency between them;
- the same mechanical change shape;
- small enough that none deserves its own design judgment or test seam;
- non-overlapping except for an intentionally safe shared generated/registry surface.

Examples: several equivalent field additions, constant updates, fixture mappings, simple renames, or repeated compatibility shims with identical rules.

Collapse them into one **batch task** with explicit `batch_members`, each member's files/change/acceptance evidence, and one shared `batch_key`. One worker implements the batch and one opposite-provider reviewer verifies **every member** appears correctly in the diff.

Never batch auth/security behavior, destructive/data migrations, public contract changes with distinct semantics, different root causes, or tasks whose tests/review could reasonably pass one member and reject another for different reasons.

Batching changes the dispatch/review unit, not traceability: every original member remains named and mapped to evidence.

## Dispatch

Dispatch as many frontier tasks in parallel as the configured worker budget safely allows. Apply `references/delegation-gate.md` only to optional auxiliary analysis agents; implementation workers remain mandatory under the control-plane contract.

Every worker starts from the current integration-branch tip (or exact integration SHA recorded in its packet).

Before reporting done, the worker synchronizes the latest integration tip into its branch/worktree and reruns its focused verification. Its result records:

- `integration_base_sha`;
- `head_sha`;
- changed paths;
- focused evidence.

This surfaces integration conflicts while the implementer still owns the context rather than dumping them onto the parent.

## Integration wave

As each task passes opposite-provider review:

1. integrate it mechanically;
2. run affected focused checks;
3. update task status;
4. recompute the frontier;
5. immediately dispatch newly-ready tasks while unrelated workers continue.

Do not wait for a whole “wave” to finish if a newly-ready task can start safely.

## Conflict policy

If another integration landed after a worker’s final sync and the mechanical integration now conflicts, create a bounded repair/resync task. The parent still does not patch code.

## Token policy

The frontier calculation uses task statuses/dependency ids/ownership metadata. It must not reread every task packet to decide readiness.
