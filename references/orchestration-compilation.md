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

Every dedicated quality gate persists a version-2 envelope matching `schemas/gate-result.schema.json`.

Before collecting integrated-time evidence, compile a bound quality plan with `--run-id`, `--scope`, and `--input-fingerprint`. The fingerprint must describe the current reviewed inputs, not merely the gate name. These fields and the required artifact kinds participate in `quality_plan_id`. An unbound plan remains useful for approval-safe precomputation, but cannot aggregate to PASS.

```json
{
  "schema_version": 2,
  "gate": "A11Y_GATE",
  "status": "PASS",
  "run_id": "checkout-123",
  "quality_plan_id": "<copy from the current compiled plan>",
  "scope": "checkout",
  "input_fingerprint": "<copy from the current compiled plan>",
  "findings": [],
  "evidence": [
    {"kind": "accessibility", "path": "experience/accessibility.json", "sha256": "<actual 64-character file digest>"},
    {"kind": "interaction", "path": "experience/interaction.json", "sha256": "<actual 64-character file digest>"}
  ],
  "details": {}
}
```

The placeholders above are not valid evidence. The reviewer records real artifact paths and digests after inspecting the files. `required_evidence_kinds` is compiled from the registry's `probe_needs`; gates without runtime artifact requirements still attach a concrete report as `kind: other`.

Aggregate with `scripts/gate_result.py aggregate --plan <quality-plan.json> --result <gate.json> --artifact-root <run-directory>`. The artifact root defaults to the plan's directory. Evidence must exist inside that root, including after symlink resolution, and its SHA-256 must match. A fused review still produces one separately bound result per gate.

Missing results, duplicate verdicts, wrong run/plan/scope/fingerprint, missing artifact kinds and stale or inaccessible files are BLOCKED. No last-write-wins behavior is permitted. PASS exits 0; REPAIR and BLOCKED exit 6. `validate` checks envelope structure only; it is not a substitute for aggregation and artifact verification.

### Upgrading from version-1 results

Keep old records for diagnostics, but do not relabel them as version 2 or synthesize missing provenance. Recompile the plan with its current binding, revalidate or recollect the required proof files, and obtain fresh bound verdicts. Verified reusable artifacts can be copied into the current run; their old verdict does not automatically become a current PASS. Approve materially changed plans as usual.

## Evidence invalidation

Exact-SHA reuse remains the conservative default. A process exit code of 0 cannot override a failed domain verdict; a successful verdict cannot override a failed process. Neither missing identity nor an empty dependency scope can qualify for reuse.

For automatically discovered dependencies, prefer:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/evidence.py" fingerprint \
  --repo-root . --entry src/Page.tsx --extra design/tokens.json
```

This performs dependency discovery and fingerprinting together. Unresolved aliases/packages, dynamic imports, unsupported source types, missing extras or a reached depth limit produce `scope_fingerprint: null` and `reuse_basis: exact_sha`. Do not pass a null or stale scope fingerprint into reuse. Verify the full input revision before exact-SHA reuse, including worktree changes and relevant environment differences.

`--path` is still available for an explicitly complete dependency list maintained by a trusted repository contract. It does not discover imports. Do not feed an incomplete discovered list into that manual mode to bypass its fallback. Include non-imported tokens, schemas, configuration, fixtures and environment metadata as appropriate.

Cross-SHA reuse requires an explicitly matching complete scope fingerprint plus passing freshness, command and path rules.

## Context compilation

Compile task/reviewer packets through `context_compiler.py` and persist their hash/size. A repair packet points back to the original packet plus the canonical finding and delta instead of resending broad context.

## Incremental runtime

Read `references/incremental-runtime.md`.

Before approval, `precompute.py` may compile deterministic artifacts with zero model/worker dispatches. After quality compilation:

- `repo_facts_cache.py` reuses content-hashed repository structural facts;
- `probe_plan.py` derives the minimal artifact union per shared probe group;
- `verification_plan.py` derives the targeted repository-native check set; `test_impact.py` ranks that set from measured history without dropping required checks;
- `evidence_deps.py` may derive bounded local import dependencies for scoped evidence fingerprints;
- `quality_depth.py` may escalate evidence depth from runtime signals without changing gate requiredness;
- `review_plan.py` fuses only compatible gate reviews while preserving separate envelopes;
- `readonly_pack.py` packs compatible non-independent read-only work;
- `coverage_matrix.py` makes proof gaps explicit before final review;
- `result_cache.py` may reuse exact-fingerprint immutable read-only results across runs;
- `routing_advisor.py` may provide an economic tie-breaker only inside normal safety/model policy;
- `frontier_scheduler.py` decides ready dispatch units from DAG state.

Persist these plans under `state.runtime_plans` so resume does not recompute already-known topology without cause.
