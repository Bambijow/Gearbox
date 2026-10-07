# Test suite cleanup

Use this protocol to remove test-suite entropy without converting "less code" into "less confidence".

## What counts as a cleanup candidate

A test may be worth reviewing when current evidence suggests one or more of these:

- it exercises the same production seam, invariant and materially identical failure mode as another stronger test;
- its assertions are a strict subset of a surviving test and it adds no useful boundary/example;
- many parameterized-looking copies differ only in data that does not create a distinct behavior class;
- it is coupled to private implementation details that callers no longer depend on while a credible public-seam test protects the real contract;
- it protects behavior that an accepted spec/API/product contract has explicitly removed or replaced;
- a stronger property/invariant test now subsumes a large collection of example tests;
- a snapshot/golden test duplicates another canonical artifact without adding a distinct failure signal;
- its fixtures/helpers exist only for tests that are themselves proven removable.

Similarity is a signal to investigate, never proof.

## Things that do not justify deletion

Do not delete merely because a test is:

- old;
- slow;
- flaky;
- inconvenient to update;
- low-level while an integration/E2E test exists;
- duplicated in wording or setup;
- covering a branch that currently looks "obvious".

A unit test can still provide cheaper fault localization, boundary coverage, or a failure mode hidden by a broad integration test.

## Classification

### KEEP

The test uniquely protects a relevant behavior/failure mode or provides materially better localization/coverage than supposed replacements.

### MERGE

Several tests protect the same seam/failure class and can become one clearer parameterized/table/property test without losing meaningful examples.

### DELETE

Deletion is justified only when either:

1. current accepted behavior no longer includes what the test protects; or
2. surviving credible tests protect the same relevant failure modes with no material loss of detection/localization.

### REWRITE

The behavior remains important, but the current test uses a weak/private/mock-only seam. Replace it with a credible test rather than preserving or blindly deleting it.

### BLOCKED

Use when current code, tests, specs, ADRs or product contracts disagree enough that cleanup would implicitly decide product semantics.

## Deletion proof

For every `MERGE` or `DELETE` candidate, record:

- candidate test/file;
- protected behavior or invariant;
- current contract evidence;
- surviving test(s), if any;
- why their seam/assertions are at least as credible;
- one plausible production fault relevant to the candidate;
- whether the surviving suite would detect that fault;
- focused command used before/after.

For low-risk exact duplicates, a reasoned mutation story can be enough. For auth, money, persistence, state machines, parsers, data integrity or other high-cost invariants, prefer a real targeted mutation/property check when repository tooling makes it practical.

## Apply protocol

1. Scope narrowly by package/domain/test directory.
2. Run the targeted baseline first. If it is already red for unexplained reasons, do not delete around the failure.
3. Group candidates by invariant, not filename.
4. Produce the classification report before mutation.
5. Under `--apply`, edit tests/test-only fixtures/helpers only.
6. Apply small independent batches.
7. After each batch, rerun the focused suite and any credibility probe used for the deletion proof.
8. Run affected lint/type/build checks where test code participates.
9. Compare the final suite against the baseline.
10. Stop on any unexplained coverage/failure-signal regression.

Do not edit production code merely to make tests easier to remove. If cleanup exposes a bad production seam requiring architecture work, report it separately.

## Interaction with test hardening

`clean-tests` asks "which tests no longer buy us useful confidence?"

`test-harden` asks "would the surviving important tests catch plausible wrong implementations?"

They are complementary. After a substantial cleanup around an expensive invariant, a bounded hardening pass is often the best proof that pruning removed noise rather than safety.
