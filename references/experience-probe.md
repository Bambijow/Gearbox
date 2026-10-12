# Shared experience probe

User-facing gates should observe the same runtime whenever possible instead of reopening the product independently.

## One probe, many judgments

For a material UI/creative journey, compile the quality plan first. If multiple required gates share `probe_group: experience`, run one instrumented journey and store a reusable bundle under:

```text
.gearbox/runs/<run-id>/experience/<probe-id>/
├── experience-bundle.json
├── screenshots/
├── accessibility/
├── console/
├── network/
├── performance/
├── interaction/
└── playback/
```

Use `scripts/experience_bundle.py` to register artifacts and hashes.

The probe should collect only what required gates need at the selected quality profile. Typical artifacts:

- desktop + mobile/narrow screenshots;
- interaction/state event log;
- accessibility tree or audit output;
- console/runtime errors;
- failed/suspicious network evidence;
- performance trace/vitals when PERF is required;
- playback/video for motion/creative behavior when still images are insufficient;
- DOM/state metadata needed to compare a baseline.

## Independence without duplicate observation

Reviewers remain cognitively independent: each gate reads the approved contracts plus the shared bundle and reaches its own verdict.

Independence does **not** require each reviewer to launch a second browser session.

Do not rerun the same journey merely because A11Y, visual regression, interaction, dogfood and performance have separate reviewer roles.

## Probe invalidation

A bundle is evidence for its exact scenario/environment/artifact fingerprint. Re-run when:

- target state or scenario changes;
- changed dependencies invalidate the affected observation;
- capture environment/profile materially changes;
- a repair changes the runtime surface inspected;
- artifacts are missing/hash-mismatched;
- external-state TTL expires.

A source-only repair outside the experience dependency set should not automatically force a new browser journey.

## Quality profiles

Use the quality plan's depth:

- `dev`: changed states only;
- `standard`: representative material states;
- `release`: representative journey plus edge states;
- `critical`: risk-expanded matrix.

Required safety/correctness gates remain required; profiles change evidence depth, not truth.
