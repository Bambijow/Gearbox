# Compiled orchestration

Gearbox should derive execution/quality topology mechanically before spending model budget.

## Pipeline

```text
expected/actual paths + task kind
        ↓
change_surface.py
        ↓
consequence surfaces
        ↓
quality_plan.py
        ↓
required gates + shared probe groups + quality profile
        ↓
route_task.py
        ↓
specialist backend + concrete models/efforts/capabilities
        ↓
context_compiler.py
        ↓
bounded worker/reviewer packets
        ↓
workers / shared experience probe
        ↓
normalized gate-result envelopes
        ↓
gate_result.py aggregate
        ↓
PASS | REPAIR | BLOCKED
```

The main conversation arbitrates exceptions; it should not manually recreate this topology when the scripts can derive it.

## Plan-time vs integrated-time compilation

At plan time, classify expected owned/touch paths and task kinds. Persist a **provisional quality plan** under the run directory and include its gate/probe topology in plan approval.

After integration, refresh classification from the actual changed paths. The integrated plan may:

- add a gate when the real diff touched a new consequence surface;
- drop a provisional gate only when the actual diff proves its trigger never occurred;
- preserve an explicit user/repository-required gate even when path heuristics are silent.

Record the reason for any delta from the approved provisional quality plan.

## Quality profiles

Profiles change evidence depth, not whether a required safety/correctness property is true.

- `dev`: changed states / focused probe;
- `standard`: representative material states;
- `release`: representative journey plus edge states;
- `critical`: risk-expanded matrix and stricter fresh adjudication.

Default is `standard`. A repository may persist another default in Gearbox config.

## Unified routing

Use `scripts/route_task.py` as the planner/control-plane facade for specialist task kinds.

The facade reads `orchestration-registry.json` and delegates dynamic behavior to:

- `game_asset_router.py`;
- `web_design_router.py`;
- `product_quality_router.py`.

Static specialist model/effort identities live in the registry, not independently in each router.

## Shared probes

When required gates share a probe group, collect evidence once. In particular, user-facing web gates commonly share the `experience` probe.

Use `experience-prober` + `scripts/experience_bundle.py`; independent reviewers consume the same immutable bundle.

## Gate envelopes

Every dedicated quality gate persists a normalized result matching `schemas/gate-result.schema.json`.

The human-facing domain verdict may remain richer, but the control plane receives:

```json
{
  "schema_version": 1,
  "gate": "A11Y_GATE",
  "status": "PASS",
  "scope": "checkout",
  "input_fingerprint": "...",
  "findings": [],
  "evidence": [],
  "details": {}
}
```

Aggregate required results with `scripts/gate_result.py`. Missing required results are BLOCKED, not silently treated as PASS.

## Evidence invalidation

Exact-SHA reuse remains the conservative default. For expensive scoped gates, compute a dependency fingerprint with `evidence.py fingerprint` and record it on the evidence item.

Cross-SHA reuse is allowed only when the caller explicitly requests the same scope fingerprint and freshness/command/path rules still pass.

## Context compilation

Compile task/reviewer packets through `context_compiler.py` and persist their hash/size. A repair packet points back to the original packet plus the canonical finding and delta instead of resending broad context.

## Incremental runtime

Read `references/incremental-runtime.md`.

After quality compilation:

- `probe_plan.py` derives the minimal artifact union per shared probe group;
- `verification_plan.py` derives the targeted repository-native check set from the repository verification catalog;
- `evidence_deps.py` may derive bounded local import dependencies for scoped evidence fingerprints;
- `coverage_matrix.py` makes proof gaps explicit before final review;
- `result_cache.py` may reuse exact-fingerprint immutable read-only results across runs;
- `routing_advisor.py` may provide an economic tie-breaker only inside normal safety/model policy;
- `frontier_scheduler.py` decides ready dispatch units from DAG state.

Persist these plans under `state.runtime_plans` so resume does not recompute already-known topology without cause.
