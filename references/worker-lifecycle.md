# Delegated child lifecycle and waiting

Gearbox may have multiple workers/researchers/reviewers in flight. Waiting should not become a polling tax or hide lost children.

## Register before dispatch

For background or long-lived delegated work, register the expected child and artifact:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/child_jobs.py" register \
  --run-dir ".gearbox/runs/<run-id>" \
  --id "task-T3-impl" \
  --kind implementation \
  --provider codex \
  --artifact "tasks/T3/worker-result.json" \
  --timeout-seconds 3600
```

Use the provider/harness child handle as the id when stable; otherwise choose a deterministic task/role id.

## Waiting policy

Never spin:

```text
wait 10s → wait 10s → wait 10s → ...
```

Instead:

1. while useful local control-plane work exists, do it;
2. let event-driven child completion surface naturally when the host supports it;
3. when genuinely idle, wait in a **bounded long interval** appropriate to the expected job;
4. after waking, reconcile children once;
5. recover an `ARTIFACT_READY` child from its artifact even if its inline completion message was lost;
6. treat `STALE` / `ORPHANED` as lifecycle failures to diagnose, not permission to launch duplicates blindly.

Capacity/active-agent-limit errors are backpressure. Queue the work and retry after a slot frees; they are not task failures.

## Completion

Mark the child completed/failed/cancelled when the host result is known. Child lifecycle state is orchestration evidence, not product evidence.

## Resume

On `/resume`, reconcile `children.json` before redispatching pending work. A non-empty expected artifact may prove a child finished even if the previous controller died before recording its return.

This registry does not replace provider-native process supervision. It gives Gearbox a durable reconciliation surface across harnesses.
