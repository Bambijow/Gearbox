# Proof for independent critical guards

For auth, payment, state-transition or data-integrity invariants protected by multiple guards, enumerate **every independent guard**. Run pristine tests green first. Disable exactly one guard per trial, verify the mutation actually changed the intended production seam, and run the relevant test. Capture a red result whose failure reason is the protected invariant (not setup or compilation errors). Restore pristine code before the next guard.

Record a local JSON receipt with `schema_version: 1`, `expected_guards` (full list), and `guards` entries. Each entry has `guard`, `mutated_guards: [guard]`, `mutation_diff` (retained diff path), `baseline_green: true`, `mutation_applied: true`, `mutation_killed: true`, `failure_is_intended: true`, `test_command`, and `failure_evidence` (retained output path). Run `python3 scripts/guard_mutation_proof.py --report <receipt.json>` to validate completeness. This checks declared evidence, not the truth of self-reported booleans: inspect diffs and test logs independently. Do not mutate production files in normal CI.

If one guard survives, report a **test gap** and reject the claim that the full invariant is protected. Exclude equivalent/impossible mutants with explicit reasoning, not by claiming a kill. Prefer bounded high-consequence paths, not blanket mutation testing.
