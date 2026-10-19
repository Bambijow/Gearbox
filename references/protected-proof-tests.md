# Protected acceptance tests in simplification

Before dispatch, the orchestrator supplies a protected proof manifest: test paths and identifiers (including parameterized cases), baseline content identities, and verification commands. Include newly added and pre-existing accepted tests. If the manifest cannot be established, do not authorize test-file edits.

The simplifier must not delete, skip, weaken, rewrite, rename, or alter fixtures/assertions of protected tests. Non-proof test helpers may only be simplified with preserved proof and successful focused checks.

Protected test cleanup requires a separate `/gearbox:clean-tests --apply` decision with evidence of equivalence. After simplification, independently compare protected test identifiers and baseline files, reject/revert alterations, and rerun focused verification. A green suite alone does not authorize changing a protected test.
