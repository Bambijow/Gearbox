# Required context and verified coverage

These contracts close three fail-open cases: an empty compiled packet, declared rather than verified coverage, and missing evidence selecting lite review. They do not claim an integrity hash proves semantic correctness.

## Context descriptors

`context_compiler.py` validates before rendering. `packet_kind` defaults to `implementation`; `review` has the same requirements, while `investigation` does not require an invented `spec_slice`. Every kind requires a non-empty role, outcome, task, ownership, verification method and output contract, plus an explicit string-list `required_capabilities` (including `[]`). Implementation/review additionally require the spec slice. Use ownership to state a read-only scope for investigators/reviewers.

`critical_pointers` and `critical_dependencies` are optional string lists that never compress. Put source contracts, indispensable invariants and authority/scenario identities there; ordinary `pointers` and `dependencies` remain compressible. A budget overflow fails instead of dropping critical information. `precompute.py` validates all descriptors before writing any context packet.

Migrate old descriptors by supplying the genuinely missing contract; do not fill mandatory fields with arbitrary boilerplate simply to pass validation.

## Coverage schema 2

`coverage_matrix.py` requires `schema_version: 2`, non-empty `run_id`, `scope`, `input_fingerprint`, an explicit requirements list and proof records. Bind the input fingerprint to the actual reviewed revision (including relevant worktree/config/environment), not just a gate name. Do not relabel a source reconstruction's evidence as destination proof.

Example input shape (replace placeholders with actual identities/digests):

```json
{
  "schema_version": 2,
  "run_id": "port-jump",
  "scope": "jump-input-buffer",
  "input_fingerprint": "<actual current input fingerprint>",
  "requirements": [
    {"id": "R1", "required_kinds": ["test"], "proof_ids": ["T1"]}
  ],
  "proofs": [
    {
      "id": "T1", "kind": "test", "status": "PASS", "exit_code": 0,
      "run_id": "port-jump", "scope": "jump-input-buffer",
      "input_fingerprint": "<same current input fingerprint>",
      "pointer": "evidence/jump-test.txt", "sha256": "<actual file SHA-256>"
    }
  ],
  "failure_modes": []
}
```

A PASS proof must have the same run/scope/input identity, a real file inside the selected artifact root, a matching full-file SHA-256 and no conflicting process exit. The helper reuses the gate layer's file-confinement/hash verification. It does not accept a model's success label as sufficient evidence.

Run with `--input <input.json> --artifact-root <run-directory>`; artifact root otherwise defaults to the input's directory. Output may be persisted with `--output` under the approved run location by an authorized role. Exit 0 means COMPLETE; 6 means GAPS/BLOCKED; CLI/input errors use 2.

Required kinds must be explicit and non-empty, unless a requirement has `not_applicable_reason`, empty `required_kinds` and no proof references. An empty requirement set similarly needs a top-level `not_applicable_reason`. Applicability is a reviewed plan decision, never a way to bypass a missing proof. Duplicate IDs block, dangling references remain gaps, pending/unknown proofs never cover a requirement, and uncovered failure modes prevent COMPLETE. A matching `covers_failure_mode` on a verified referenced proof can cover a named failure mode.

For old runs, keep the old matrix for diagnostics, re-establish current input identity and revalidate actual proof files before constructing schema-2 input. Do not synthesize successful evidence or copy old PASS strings. A current valid artifact may be reused under the existing freshness rules; the historical verdict alone is not portable proof.

## Final-review inputs

Provide actual coverage and quality status to `final_review_router.py`. `not-provided` is rejected by default. Explicit `not-applicable` needs `--evidence-not-applicable-reason` and must match the approved requirement/gate topology.

The migration-only `--legacy-incomplete-evidence` switch permits classification with missing inputs, but forces at least focused review. It never waives verification, fills coverage, drops a required gate or authorizes shipping. A reviewer may identify the missing proof; a review opinion does not replace it.
