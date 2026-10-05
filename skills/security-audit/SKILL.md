---
name: security-audit
description: "Perform a focused defensive security audit around explicit trust boundaries by building a small threat model, tracing entry points and data flows, reviewing the diff plus adjacent code, and using available static analyzers selectively. Use for auth, permissions, secrets, crypto, untrusted parsing/uploads/deserialization, sensitive data, or security-critical changes."
argument-hint: "[diff/PR/path/scope]"
disable-model-invocation: true
---

# Audit concrete attack paths

This is a defensive engineering review, not a generic list of secure-coding advice.

Read `references/security-audit.md`, `references/review-calibration.md`, `references/secret-redaction.md`, and repository security instructions. For a PR/diff, begin with the changed trust boundary and expand only along plausible attack/data paths.

## Audit spine

Build a compact threat model: assets, attacker/control assumptions, entry points, trust boundaries, privileged actions and sensitive sinks.

Then inspect:

- authorization and identity transitions, not merely authentication;
- validation/canonicalization at untrusted boundaries;
- secrets, tokens and sensitive logging;
- injection/interpreter/query/template boundaries;
- upload/path/archive/parser/deserialization behavior;
- cryptographic misuse or unsafe fallback/defaults;
- SSRF/egress or confused-deputy paths where relevant;
- data exposure, tenancy and persistence invariants;
- dependency/config changes only when they materially change the attack surface.

Use Semgrep, CodeQL or repository-native scanners when available and scoped enough to add signal. Treat scanner output as claims requiring validation.

## Findings

A valid finding needs a concrete failure/abuse path, affected asset, attacker precondition, evidence location and consequence. Calibrate severity by exploitability plus impact. Separate confirmed issues from hypotheses that need reproduction.

Do not create findings for generic best practices with no plausible path. Do not claim the absence of vulnerabilities because a scanner or review found none.

In an orchestrated run, repairs are delegated and return through normal verification/review. The audit itself remains independent judgment.
