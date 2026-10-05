# Ready-frontier scheduling

Gearbox executes a dependency DAG as a changing **ready frontier**, not a static list.

A task is on the ready frontier when:

- every declared dependency has passed task review and is integrated;
- required spec/domain decisions are resolved;
- its owned write surface does not conflict with another active task unless the interface is explicitly coordinated;
- the task packet has enough pointers to start without broad rediscovery.

## Dispatch

Dispatch as many frontier tasks in parallel as the configured worker budget safely allows.

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
