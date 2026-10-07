# Test credibility gate

A green test is evidence only when it can realistically detect the behavior it claims to protect.

Apply this gate whenever Gearbox adds, strengthens, reviews, or relies on a test as acceptance/regression evidence.

## Credibility questions

A behavior-bearing test should satisfy all applicable items:

1. **Observed red** — for new/regression behavior, the test was seen fail before the fix when a safe red-capable seam exists.
2. **Right reason** — the red failure represented the intended broken invariant, not setup noise.
3. **Real seam** — the test exercises the production behavior/contract at a seam real callers use.
4. **Independent expectation** — expected values come from the spec/domain rule/example, not by reusing the production computation under test.
5. **Mutation story** — name at least one plausible production mutation that would make the test fail.
6. **No test-only production seam** — production API/branching was not invented solely so the test could assert something callers never rely on.

## Hard stops

Do not count these as behavior proof:

- grep/string-presence assertions against source when observable behavior is the requirement;
- constant assertions or change-detectors that can fail without detecting a product defect;
- a mock-only seam that bypasses the failure chain that occurred in production;
- an expected value computed by calling the same helper/algorithm under test;
- a shallow test added because no stable seam exists.

If no credible seam exists, record that as a verification/architecture finding. Keep the original red-capable reproduction as evidence when possible rather than manufacturing false confidence.

## Cleanup / deletion gate

Before deleting or merging a behavior-bearing test, apply `references/test-suite-cleanup.md`. A test is removable only when the protected behavior is intentionally gone or credible surviving tests preserve the relevant failure signal. Age, slowness, flakiness or the existence of broader E2E coverage are not sufficient evidence.

## Hardening escalation

For high-cost invariants, parsers/state machines, money/auth/data-integrity logic, or a user-requested confidence pass, apply `references/test-hardening.md`. A real targeted mutation that survives is stronger evidence of a test gap than merely naming a mutation story. Do not run repository-wide mutation/fuzz campaigns by default; constrain the target, time budget and invariant first.

## Trivial work

Generated mappings, metadata, formatting and static wiring do not need ritual red-green tests when repository-native mechanical checks are stronger. Use the narrowest credible evidence.
