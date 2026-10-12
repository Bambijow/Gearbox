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
