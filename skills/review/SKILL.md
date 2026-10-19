---
name: review
description: "Review a diff, branch, PR, or completed plan for requirement coverage, correctness, security, regressions, tests, operational risk, and post-simplification architecture."
argument-hint: "[diff, branch, PR, plan, or scope]"
disable-model-invocation: true
---

# Review the actual change

Review code and requirements, not the implementation conversation.

Read `references/review-calibration.md`, `references/test-credibility.md`, and `references/evidence-reuse.md`. For an orchestrated post-integration gate also read `references/final-review-routing.md` and obey the persisted `final_review` route. When the diff crosses an explicit trust boundary (auth/permissions, secrets/crypto, untrusted parsing/uploads/deserialization, sensitive data), also apply `references/security-audit.md` rather than relying on a generic security checklist.

## Scope

Read repository instructions, relevant spec/issue/plan, final diff, changed files, direct dependencies, Review Focus, and current evidence pointers. Discover applicable review/standards files such as `CODING_STANDARDS.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and nearest scoped equivalents rather than assuming one global rules file. Expand only on a concrete suspicion.

For a **standalone user-invoked** `/review`, perform the review in the current context; optional extra reviewers still pass `references/delegation-gate.md`.

For an **orchestrated final review**:

- `lite`: do not dispatch another model reviewer. Inspect the integrated diff centrally and rely on accepted task reviews + verifier evidence.
- `focused`: dispatch exactly one fresh adversarial integration reviewer against the silent/shared failure surface.
- `full`: dispatch one fresh comprehensive reviewer; in hybrid add one independent cross-provider adversarial peer when available.

No reviewer may edit the integration tree. Never ask a reviewer to review another reviewer.

## Finding standard

A material finding needs a concrete reachable failure path, requirement mismatch, credible verification gap, or maintainability hazard with real future cost.

Classify:

- **Blocker**: likely security/data-loss/severe correctness/compatibility/production-safety failure.
- **Important**: concrete meaningful regression or material acceptance gap.
- **Minor**: relevant localized cleanup with modest impact.
- **Advisory**: hardening/rollout observation that does not make the change incorrect.

For each finding include location, evidence/failure path, consequence/failure cost, smallest useful remedy, and ownership (`repair|human|release|advisory`).

Reconcile multiple reviewers centrally against code/spec/evidence. Agreement is corroboration, not proof.

## Cross-provider receipt

When an independent cross-provider review was requested, emit a machine-readable receipt alongside the human summary. Record `peer_outcome` as exactly one of `folded` (an identifiable independent result was received and its findings reconciled), `fallback` (independent result unavailable; another route was explicitly used), `failed` (the requested peer failed or returned an unusable result), or `not_required` (no peer was requested by the route). Also record `requested_provider`, `verified_provider` (null if unverifiable), `peer_evidence_ref` (null if none), and `fallback_reason` (null unless applicable). A launched job is not a received review; an unverifiable provider is never `folded`.

For `full` + `hybrid`, do not report independent cross-provider review as complete unless `peer_outcome=folded`. Any `fallback` or `failed` outcome must be surfaced for explicit adjudication against the persisted route; never silently downgrade to a local-only PASS. The receipt is a review provenance record, not a substitute for the quality-gate evidence envelope.

## Maintainability scope checks

In addition to ordinary correctness, flag these when the diff provides concrete evidence:

- **Unrequested surface**: a new public endpoint, flag, config key, parameter or export contradicts the accepted scope or is clearly outside a narrower requested contract. Mere omission from a brief is not proof; name the scope evidence and the surface to remove.
- **Needless dependency**: a new package/dependency was added for behavior the standard library, platform, or an existing repository helper already provides. Name the concrete replacement, not just "avoid dependencies".

These are review findings only when tied to real scope/maintenance cost, not aesthetic minimalism.

## Verification audit

Map each acceptance criterion to executable/manual evidence. Valid exact-SHA evidence is proof to inspect, not a reason to rerun the same suite. Rerun only for a freshness/scope/legibility gap or when a finding challenges that evidence seam.

If no material findings remain, say so and state what was inspected and what could not be verified.
