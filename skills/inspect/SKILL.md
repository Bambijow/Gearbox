---
name: inspect
description: "Explain a Gearbox run's blockers, plan approval, verified quality evidence, recorded worker states, scheduling conflicts and usage without resuming or mutating the run."
argument-hint: "[run-id | run-directory]"
disable-model-invocation: true
---

# Inspect a run without changing it

Resolve the requested `.gearbox/runs/<run-id>` from the repository. If no unique match exists, show the matching run IDs rather than picking one silently.

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/inspect_run.py" --run-dir <run-directory> --json`.

Use the returned diagnostics as the source of truth. Explain the concrete blocker, pending approval, invalid or missing proofs, ownership waits, recorded usage and smallest next action. Distinguish recorded child statuses from verified process liveness. Unknown cost is unknown, not zero.

Do not initialize or migrate state, acquire or break locks, approve a plan, reconcile children, dispatch a worker, or contact remote services. Do not infer that the product is shippable from a stored run status. When quality artifacts are available the helper independently verifies their binding and file hashes; missing artifacts remain blocked.

Inspection never grants approval. Refer to `/gearbox:resume` for an explicitly requested continuation.

If the existing control-plane guard denies this helper, report that limitation and stop. Do not disable the guard or route the helper through another executable to bypass it.
