# Post-PR continuation loop

This loop inherits `references/control-plane.md`: the parent validates CI/review claims and schedules work, but it never edits the repair itself.

Opening a PR is not proof the change is done. `/continue-pr` consumes CI and human review feedback as another bounded repair loop.

## Intake

Fetch the PR metadata/diff/head SHA, required/visible checks, review decisions, review comments and unresolved review threads with `gh`. Read only new feedback since the last recorded PR continuation when possible.

Classify feedback into:

- environment/transient failure;
- deterministic failing check;
- valid code-review finding;
- ambiguous product request;
- stale comment already resolved by newer code;
- suggestion/opinion with no correctness requirement.

Review comments are hypotheses, not commands. Verify them against current code/spec before editing.

## Repair DAG

Convert validated failures into the smallest repair DAG. Reuse the original spec, repo facts, state, model policy and evidence. Do not replay the whole issue pipeline.

Implementation fixes are delegated to routed workers and reviewed with the configured opposite-provider gate. Delegate accepted integration to `integrator`, focused/full-enough checks to `verifier`, and targeted Ponytail only when structure changed. After PASS, delegate push/update of the existing PR and technical evidence comment to `shipper`.

## CI freshness

A successful check only proves the SHA it ran against. After any new push, wait for/check the new head's required checks before calling the PR healthy.

## Stop states

`PR_PASS`, `PR_BLOCKED`, `PR_BUDGET_EXHAUSTED`, or `PR_MAX_CYCLES`. Never auto-merge unless separately requested.
