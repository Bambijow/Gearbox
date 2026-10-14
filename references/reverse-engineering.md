# Behavioral reconstruction and transfer

Shared protocol for `/reverse`, Wayfinder research, shaping, planning and focused debugging. Goal: recover a useful behavior from what survives, then implement the intended version in another codebase. This is original Gearbox workflow design, inspired by `morluto/rea` (Reverse Engineer Anything), not a bundled REA installation.

## Inputs and honest limits

A source checkout is helpful, not required. Start from a runnable installed app, executable, served website, packaged JS/Electron assets, native/managed binary, logs, saved network captures, exports or recordings. Inventory the actual authority, version, artifact/configuration fingerprints and available runtime. Version labels without a pinned artifact or capture are insufficient for repeatable comparisons.

Modes: `source` maps code/contracts; `behavior` probes observable inputs and effects; `interface` reconstructs UI states and interactions; `binary` uses static/native tooling when useful. These are investigation strategies, not guarantees that every platform/tool is installed. If only recordings remain, reconstruct the demonstrated behavior and mark unobservable branches unknown. If nothing executable or observable survives, work from user examples as new requirements, not as recovered facts.

State one question and a bounded completion criterion. Investigate only facts that would change an implementation or transfer decision. Treat knowledge uncertainty separately from consequence risk: a cheap read/probe can resolve an unknown without buying a full architecture exercise. It cannot remove an applicable safety gate or authorize product edits.

## REA as an optional provider

Upstream references checked on 2026-10-14:

- https://github.com/morluto/rea
- https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md
- https://github.com/morluto/rea/blob/main/docs/process-capture.md

Before real use, record the installed REA version, live MCP tool schemas, host, selected provider and capabilities. Upstream `main` may describe tools not yet present in a released package. Consult installed help/schema and the pinned release; do not copy remembered argument shapes. Do not auto-install REA, native providers or upstream skill instructions. Installation and configuration changes require separate permission.

Borrow feature-scoped investigation, following calls/references only as needed, canonical evidence identities, declared coverage/limitations and separate reference/candidate observations. Through live-discovered tools, use REA to inspect native or JS/managed artifacts, browser/network evidence, or process captures when supported. Preserve the returned canonical evidence ID, normalized result, analysis profile, provider/target identity and limitations in a redacted evidence file. An MCP error or truncated/partial result is not a complete observation. An empty unavailable facet does not prove absence.

REA process capture runs a selected command with the host user's permissions and inherited environment. It does not sandbox the target and observation paths do not constrain writes. Establish isolation separately, avoid secrets in inherited environment, restrict network and effects, snapshot/dispose the test workspace, and require bounded runtime authorization. Never execute a target merely because static parsing failed.

REA capture comparison has its own comparison-contract and host constraints. Use it only when the actual captures satisfy those constraints; for cross-project adaptation use an explicit semantic adapter and destination-native tests instead of weakening REA's comparator. Normalization must be declared before comparing, narrow, justified and visible. Never delete mismatches until the samples look equal.

Without REA, use existing eligible source/browser/debugger/CLI tools and the same evidence contract. A missing tool yields a specific capability gap, not an invented decompilation. REA is a tool provider; Gearbox retains orchestration, approval and product ownership.

## The portable reconstruction bundle

Store a feature-sized bundle under `.gearbox/runs/<run-id>/reconstruction/<feature>/`. Use relative paths so the redacted evidence and contract can move together. Retain original authority metadata; do not relabel old evidence as a current destination result. Do not bundle an executable or unrelated source/assets by default.

`contract.json` follows `schemas/reconstruction.schema.json`:

- `source`: id, kind, version, fingerprint, availability (`runnable`, `artifact-only`, `recordings-only`). The fingerprint identifies the exact artifact or retained capture plus relevant configuration, not a model's certainty.
- `question`, `scope`, `limitations`: bounded purpose and limits.
- optional `target`: destination project and inspected revision. A later revision requires destination revalidation.
- `evidence`: stable id, kind, relative path, complete file SHA-256, source fingerprint, coverage (`bounded`, `partial`, `unknown`) and limitations. `bounded` describes the explicitly inspected scope, not whole-program completeness.
- `claims`: id, statement, explicit `material` boolean, status (`observed`, `inferred`, `unknown`), evidence ids and limitations. Inferred claims remain hypotheses even when their evidence files are valid.
- `scenarios`: id, claim ids, setup, actions, expected reference behavior, oracle description, reference evidence ids, explicit normalizations and comparison semantics.
- `decisions`: id, claim id, disposition, reason, proposed target behavior and scenario ids. Material destination behavior must be preserved/adapted/discarded explicitly; `defer` remains a gap.
- `unknowns`: id, question, explicit `blocking` boolean and affected claim ids.

Use `scripts/reconstruction.py --input <bundle>/contract.json` to inspect referential integrity and proof files. It writes nothing and never launches tools, installs packages, imports upstream instructions or runs commands embedded in JSON. It reports `READY_FOR_SHAPING`, `PARTIAL` or `BLOCKED`, always with `implementation_authorized: false` and `runtime_equivalence_proven: false`. Its exit codes are 0 for ready, 6 for gaps/invalid evidence and 2 for CLI/input errors. Hash validity proves file integrity, not that an agent interpreted it correctly. Inspect the semantics independently before acceptance.

Partial evidence can support a narrow observation; it cannot justify universal behavior or absence claims. Record these limits on both evidence and claims. If a material fact remains inferred/unknown, preserve the gap. Recordings-only inputs never establish unobserved interaction or runtime equivalence.

## Recover a contract, not the original implementation

Capture caller-visible behavior: input classes and boundary values, outputs, state transitions, ordering, timing tolerances, failure paths, persistence, concurrency and external effects when material. A cancel action must distinguish UI cancellation, network cancellation and server-side termination. A static call edge is not proof it ran; an observed run is not proof all runs follow it.

Form only the hypotheses still plausible and useful for the question. For each material uncertainty, state the next observation that would distinguish alternatives. Keep raw transcripts outside the parent context; return concise claims with evidence pointers. Changes to the authority, configuration or oracle invalidate dependent claims/scenarios and require focused re-investigation. Do not blindly reuse a previous conclusion by matching a filename.

For UI, prioritize state, focus, keyboard/touch, loading/error/cancel/resume and responsiveness before visual imitation. For games, capture mechanical rules, input timing, coordinate systems, units, randomness/seeds, frame/time dependence, collision and animation/audio triggers where observable. Do not transplant engine-specific assumptions or assets into a new project by accident.

## Transfer decisions and normal development handoff

Inspect the destination's conventions, public interfaces, lifecycle, failure behavior, data ownership and available checks. Produce a neutral behavioral specification and an explicit map:

- `preserve`: same promised semantics, implemented idiomatically in the destination;
- `adapt`: an intentional, stated semantic change (units, UX, storage, timing or other contract);
- `discard`: a legacy quirk or dependency not required in the target, with justification;
- `defer`: unresolved intent or missing evidence. Material deferred decisions block implementation readiness.

The original program is the reference for characterization, not the product owner. Its defects do not become requirements. The accepted target spec decides which semantics are authoritative. Present the proposed transfer decisions for normal acceptance; a JSON field is never user authorization.

Shaping consumes the bundle as evidence, using `references/spec-clarification.md`. Distinguish source observations, approved target decisions and unknowns. Planning uses `references/planning-contract.md` and `references/codebase-design.md`, chooses a small vertical integration and retains the authority/scenario pointers as critical context. No new permanent abstraction is justified solely because the legacy system used one. Delegate implementation and harness mutations through existing roles under `references/control-plane.md`.

Keep reference characterization and target acceptance distinct. Freeze the characterization scenarios before implementing the target. For preserved behavior, compare reference and target under equivalent initial state and documented semantic adapters; also test adversarial inputs not used while implementing. For adapted behavior, assert the approved target rule, record intentional divergence and do not report exact parity. Validate effects as well as returned values. Handle nondeterminism with controlled seeds/clocks or justified tolerances, not blanket output scrubbing.

Run target-native tests, integration checks and surface-triggered quality gates. UI and game adaptation inherit their existing experience/interaction/a11y/perf/playtest gates when triggered. A reference trace or successful decompilation does not satisfy a destination test gate. Source and candidate evidence are separate, and fresh candidate proofs bind to the actual destination run, revision and environment. Repair discrepancies by claim/scenario id, rather than restarting the whole investigation.

Example: an old game's jump can preserve apex height and input-buffer semantics, adapt milliseconds to the destination engine's timestep, discard frame-rate-dependent acceleration, and defer an unobserved wall-jump rule. This is a new implementation of an evidenced contract, not a claim to have recovered the author's source.
