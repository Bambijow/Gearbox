# Concurrent state transition review

When a diff changes persisted status, leases, counters, child lifecycle or scheduling state, review **all writers**, including call sites outside the changed files. Record a compact table with state field, writer, locking/transaction boundary, precondition, transition, and side effects.

Challenge each shared transition against:
1. Repeated event or duplicate callback: idempotency and no double accounting.
2. Stale writer or delayed worker result: verify generation/lease/expected version before mutation.
3. Concurrent writers: transaction / compare-and-swap / lock ensures no lost update or invalid state transition.

Review read-modify-write sequences, optimistic version checks, retry and failure recovery, including work outside the diff. A green unit test does not substitute for inspecting the actual writer topology. A potential race requires a reachable interleaving and consequence; do not manufacture speculative findings. For high-risk state, require a deterministic interleaving regression test or explicitly record a verification gap. This supplements existing review calibration and does not add another reviewer by default.
