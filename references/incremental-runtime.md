# Incremental orchestration runtime

Gearbox should invalidate and recompute only what a change actually affects.

## Runtime chain

```text
DAG state
  -> frontier_scheduler.py
  -> next dispatch units / safe micro-batches

changed paths + consequence surfaces
  -> verification_plan.py
  -> smallest repository-native check set

quality-plan.json
  -> probe_plan.py
  -> exact artifact kinds required per shared probe group

entry files + explicit contract/token extras
  -> evidence_deps.py
  -> local dependency closure
  -> evidence.py fingerprint

requirements + tests/gates/runtime proofs
  -> coverage_matrix.py
  -> COMPLETE | GAPS | BLOCKED
  -> gap-driven final_review_router.py
```

## Scheduler

The scheduler consumes task statuses/dependencies/ownership metadata only. It prioritizes ready work by critical-path length and descendant unlock count, respects active ownership conflicts, and batches compatible low/medium-risk same-shape work.

It does not reread task prompts to compute readiness.

Persist the latest scheduler decision under `state.runtime_plans.scheduler`.

## Minimal probes

Compile probe artifacts from required gates rather than asking a browser worker to capture everything.

Examples:

- SLOP -> screenshot;
- A11Y -> accessibility + interaction;
- PERF -> performance + network + console;
- visual regression -> screenshot + DOM;
- creative -> screenshot + interaction + playback.

The union for a shared probe group is the exact collection contract.

## Verification compiler

Repository setup may maintain a `verification_catalog` describing known checks with path/surface triggers, cost, coverage group and profile requirements.

Use `verification_plan.py` to choose the narrowest credible checks first. Release/critical profiles may require broader checks explicitly.

A broad check is not automatically better evidence than a targeted check.

## Evidence dependency closure

For supported local source imports, `evidence_deps.py` derives a bounded transitive closure from gate entry files. Add non-imported dependencies such as tokens, design contracts, schemas or scenario fixtures explicitly.

Feed that list to `evidence.py fingerprint`. If dependency discovery is incomplete or dynamic, keep exact-SHA reuse.

## Context compression

`context_compiler.py` never drops hard sections: outcome/spec slice/task/capabilities/ownership/verification/output contract.

Only explicitly compressible sections such as excess pointers/dependency notes may be omitted, and the manifest records omitted counts. The structured descriptor remains available to the worker when deeper reading is actually necessary.

## Cross-run cache

`result_cache.py` stores only immutable read-only outputs keyed by exact input fingerprint.

Allowed examples: research, independent review, gate output, runtime probe, static analysis, route result.

Implementation/mutation artifacts are deliberately not cacheable.

The default cache lives under the user/XDG cache directory, namespaced by Git common-dir identity, so it never pollutes the repository. An explicit cache dir may still be configured.

## Coverage matrix

Assign stable requirement ids in the accepted spec/plan. Map each to required proof kinds and concrete proof ids.

Completion requires every requirement to be covered by passing evidence. Missing/partial/blocked requirements become explicit proof gaps rather than something a final reviewer is expected to notice accidentally.

## Gap-driven final review

Final review receives:

- task-review state;
- quality aggregate;
- coverage status;
- uncovered failure modes.

A failed quality gate or blocked proof prevents final review from substituting judgment for missing evidence.

Coverage gaps force at least focused review. A lite route has no unresolved proof gap.

## Adaptive economics

Usage records may include task kind, model, effort and outcome. `routing_advisor.py` aggregates repeated measured history.

Telemetry is a tie-breaker, never a safety override:

- registered specialist routes stay pinned;
- trust/persistence/public-contract/production-config surfaces remain observe-only;
- telemetry never promotes a task to frontier compute;
- insufficient samples produce no recommendation;
- user/model policy still bounds candidates.

## Read-only cache before dispatch

For cacheable read-only work:

1. compute the exact invocation/input fingerprint;
2. query `result_cache.py get`;
3. on hit, verify the cached artifact hash and reuse it;
4. on miss, dispatch normally and cache only the immutable validated result.

Record hit/miss state in the run so retrospectives can quantify avoided dispatches.


## Controlled gate-review fusion

After shared probe collection and quality-depth resolution, compile the reviewer topology with `scripts/review_plan.py`.

For compatible low/medium-risk UI gates in dev/standard profiles, one fresh Sonnet reviewer may evaluate multiple gates over the same immutable bundle. It still emits **one normalized envelope per gate**. A failing A11Y gate cannot be hidden by a passing SLOP gate.

Do not fuse when fresh independent judgment is itself valuable: high/critical risk, creative-web, performance adjudication, security/trust boundaries, or any task explicitly marked independent.

Persist dispatches saved and fused gate membership under `state.runtime_plans.review`.

## Historical test impact

Repository checks may be ranked by `scripts/test_impact.py`, using prior changed-path/check outcomes stored outside the repository in the user/XDG cache.

History is rank-only:

- historically sensitive checks run earlier;
- insufficient samples have low confidence;
- required checks remain required;
- a history of green runs is never permission to delete or skip proof.

Record each completed check outcome/duration back to the ledger when available.

## Incremental repository facts

Use `scripts/repo_facts_cache.py` for deterministic structural facts from package manifests, tsconfig, pyproject/Cargo/go.mod, requirements and workflow files.

Facts are cached by content hash. An unchanged file is not reparsed on every run. The cache stores extracted configuration facts, not model-written architecture summaries.

Feed the compact returned facts into `repo-facts.md`; keep product/domain reconnaissance separate.

## Deterministic precompute before approval

Once the exact plan exists, Gearbox may run `scripts/precompute.py` **before human approval** because it performs deterministic artifact work only:

- quality/probe/verification plans;
- historical test-impact ranking;
- scheduler snapshot;
- specialist route snapshot from known capabilities;
- compiled context packet hashes;
- repo-facts cache lookup.

The result explicitly reports `model_calls: 0`, `worker_dispatches: 0`, and `approval_safe: true`.

This does not authorize implementation. Live capability preflight and every worker/reviewer dispatch still wait for plan approval.

## Adaptive quality depth

After integration and during repair cycles, run `scripts/quality_depth.py`.

Depth is **escalate-only** relative to the approved base profile. Silent findings, repeated repairs, integration repairs, and high/critical risk may expand state/probe/review depth. Required gates never disappear and the system never silently drops below the user-approved profile.

Persist base/effective profile and reasons under `state.runtime_plans.quality_depth`.

## Read-only dispatch packing

Before launching several small read-only tasks, run `scripts/readonly_pack.py`.

Packing is allowed only when tasks:

- use an allowed read-only kind;
- use the same provider/model/effort/context fingerprint;
- do not require independent judgment;
- preserve separate member output contracts.

Implementation/mutation work is never packed by this mechanism. Independent reviewers remain separate.

Controlled gate fusion and generic read-only packing are complementary: gate fusion understands gate semantics; generic packing handles other same-context read-only work.
