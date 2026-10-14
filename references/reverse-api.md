# Reconstructing server/API behavior without server source

Use with `/gearbox:reverse <HAR-or-traces> --mode api [--target project]`. This lane reconstructs a **candidate observable contract** from historical HTTP exchanges, not routes, SQL, source code or hidden server-side semantics. If the old backend is gone, recorded requests/responses remain valid partial evidence. Do not infer authentication, permissions, required fields, transactional guarantees, idempotency, business formulas or complete routes from a few successes.

## Passive collection before experiments

1. Inventory the artifacts and their provenance: HAR 1.2, SAZ, compatible mitmproxy capture, saved logs, OpenAPI if available, screenshots, replay fixtures. Record authority version/time/environment and capture SHA-256; provenance may remain uncertain.
2. Use `scripts/api_reconstruct.py --har <existing-capture.har>` for an offline JSON report. This Python script opens a local file only; it makes **zero HTTP requests** and does not execute embedded scripts. It caps its input size and sample count; no hostnames, query values, header values or payload values are emitted. Literal path segments and JSON keys may still be sensitive and must be reviewed before sharing. It produces observed methods, conservatively templated paths, statuses, structural JSON shapes, source record ordinals and an `openapi_candidate`. Draft operations intentionally lack `required` and authentication declarations. An `OBSERVED_ONLY` result is not an API readiness gate.
3. For other formats, use REA's actual exposed `inspect_web_network_capture` MCP/CLI operation when present. Confirm the installed version and tool schema. REA's `api-surface` projection is available for supported HAR Evidence with query-name opt-in; grouped templates are inferred and cannot prove handler identity. Redact before sharing any raw capture and distinguish redacted hashes from raw Evidence identities.
4. Group stateful examples by recorded chronology only when timestamps, correlation IDs and data support it. Identify observable precondition, request, response, state afterward, delay and material side effects. Never invent missing setup or hidden backend state.
5. Separate `observed` from `inferred` and `unknown` claims. For each uncertain claim, record its falsifier and the experiment most likely to distinguish surviving explanations. Use `scripts/decision_trace.py` to bind critical assumptions to verified evidence, and `scripts/investigation_plan.py` to choose **one** bounded discriminating probe, if authorized.

## Active probes are a separate permission boundary

An offline capture does **not** authorize traffic generation. Only probe a service the user controls or is authorized to test, in a preapproved test environment with stated endpoint allowlist, rate/request budget, credential policy, effects/reset/rollback and stop conditions. Never auto-enumerate admin or sensitive endpoints, bypass authentication, or replay mutating requests against production. A 200 response does not prove the handler is safe or correct. On denied access or incomplete environment, deliver a partial contract and a recommended manual experiment instead.

Build a *test matrix* covering boundary/invalid inputs, missing vs null values, duplicates/retries, ordering, state read-after-write, auth role differences and concurrency only where those dimensions materially matter. A candidate probe is a **proposal**, never an implicit test. Record actual observations as separate reference Evidence. A recorded 401/403 demonstrates a response under those conditions; it doesn't reconstruct authorization policy. Network silence or client cancellation doesn't prove server cancellation.

## Transfer to a new backend

For every material behavior, propose `preserve`, `adapt`, `discard` or `defer`, with independent user agreement on the target semantics. Validate source scenarios independently from target acceptance. For a preserved contract compare normalized, declared results and observable side effects; for an adapted contract test intentional divergence. Keep seeds, fixtures, time and environment under control rather than scrubbing mismatches until they disappear.

Reviewers must seek a failing counterexample with a fresh candidate fixture/test. Use `scripts/contract_challenge.py --contract <contract.json> --report <challenge.json>` and `final_review_router.py --behavior-transfer --contract-challenge-status reviewed|gaps|counterexample` as part of the ordinary verification flow. `REVIEWED_NOT_PROVEN` says a bounded challenge was performed, not that runtime equivalence has been proved. Unresolved material claims keep the spec or final quality gate blocked. Avoid adding a new schema-generating framework or server runtime to do simple passive inspection.

## Example

```bash
python3 scripts/api_reconstruct.py --har .gearbox/runs/legacy/reconstruction/orders/old-orders.har > .gearbox/runs/legacy/reconstruction/orders/api-observed.json
```

The produced JSON contains no original examples/credential material. `openapi_candidate` is a **human-reviewed draft**, not a publishable contract. The orchestrator creates `contract.json` and evidence files using `schemas/reconstruction.schema.json`, then runs `scripts/reconstruction.py`; moving from partial observation to new implementation still requires accepted destination decisions, normal plan approval and new proof.
