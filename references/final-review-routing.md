# Consequence-based final review routing

Task-level review and integration-level review solve different problems, but the final integrated diff should not always pay the same review spine.

After Ponytail simplification and before final verification, classify the **integrated failure consequence** with `scripts/final_review_router.py`.

The router has three modes.

## lite

Use when all required task review gates passed (or were legitimately not required), failure is **loud and local**, risk is low/medium, and no full-review boundary is touched.

Examples:

- local UI rendering bug caught by targeted tests;
- internal formatting/serialization helper whose failure is immediate and bounded;
- small wiring change with strong task reviews and no silent state mutation.

Final-review behavior:

- **no new model reviewer**;
- keep the accepted task reviews as the independent implementation judgments;
- parent inspects the integrated diff;
- `verifier` supplies current repository-native evidence.

Lite is not “no review”. It avoids buying a second independent review spine when the task reviews already covered the code and an integration failure would be loud/local.

## focused

Use when a plausible failure can be **silent/mixed**, or risk is high without crossing a full-review boundary, or integration creates a shared seam whose failure is not obviously local.

Final-review behavior:

- exactly **one fresh adversarial integration reviewer**;
- give it the spec/acceptance slice, final diff, changed paths, Review Focus and current evidence pointers;
- ask it to attack the silent/shared failure surface, not replay every task review;
- no finish-review swarm and no reviewer-of-reviewer.

In hybrid mode this reviewer may use the provider/model that adds the most independent signal, but task-level opposite-provider reviews remain the provider-diversity guarantee.

## full

Use when consequence is intrinsically high or hard to reverse, including:

- auth/permissions/trust boundaries;
- money/billing;
- secrets/cryptography;
- destructive migration;
- persistence/data-integrity invariants;
- public/external contracts;
- production configuration/rollout controls;
- concurrency/coordination invariants;
- material architecture/shared-interface redesign;
- critical risk;
- a large executable change that crosses the configured full-review floor.

Final-review behavior:

- one fresh comprehensive integration reviewer;
- in `hybrid`, add one independent cross-provider adversarial peer when available;
- reconcile findings centrally through `references/review-calibration.md`;
- verifier remains separate. A reviewer is not a substitute for executable evidence.

For auth/permissions, secrets/crypto, untrusted parsers/uploads/deserialization, sensitive data flows, or other explicit trust boundaries, apply `references/security-audit.md` inside the full-review spine. Prefer enriching the existing comprehensive reviewer packet over automatically buying another reviewer; add a dedicated security reviewer only when `references/delegation-gate.md` justifies fresh independent judgment.

## Size can only escalate

Changed-line count never awards `lite`.

The optional executable non-test line floor may only force `full`. It is a backstop for an unusually broad change, not a proxy for consequence on ordinary diffs.

## Preconditions

A final review route is invalid when a required task review gate is still failed. Fix/adjudicate that gate first rather than hoping a bigger final reviewer catches it.

## Persist the decision

Record the router JSON in run state, for example:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/run_state.py" set \
  --run-dir ".gearbox/runs/<run-id>" \
  --key final_review \
  --json '<router-json>'
```

PR technical evidence should state the selected mode and why, especially when `lite` intentionally avoided another model dispatch.
