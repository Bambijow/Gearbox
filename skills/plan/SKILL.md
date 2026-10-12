---
name: plan
description: "Convert a shaped request/spec into a lean executable DAG with ownership, capabilities, verification, specialist routing, and a compiled quality-gate topology. Use before non-trivial implementation."
argument-hint: "[spec path, issue, or request]"
disable-model-invocation: true
---

# Plan executable engineering work

Create a plan another capable worker can execute without rediscovering architecture.

Read `.gearbox/config.md`, repository instructions, the accepted request/spec, relevant code/tests, and only needed pointers. Apply `references/planning-contract.md`, `references/domain-modeling.md`, `references/frontier-scheduling.md`, `references/delegation-gate.md`, and `references/orchestration-compilation.md`.

Use fresh `design-proposer` judgment only for a hard-to-reverse shared seam with materially different valid designs. Do not buy discovery agents to summarize context already available.

## Build the DAG

Extract one compact **Global Constraints** block, then split work into the smallest coherent vertical slices. Each executable unit records:

- outcome + exact acceptance/spec slice;
- dependencies and `ready_when`;
- consumed/produced interfaces;
- owned paths + known shared seams;
- context pointers, not pasted bulk;
- `required_capabilities`, including explicit `[]`;
- specialist `task_kind` when applicable;
- concrete route from `scripts/route_task.py` for registered specialist kinds;
- implementation decisions a capable worker cannot safely choose alone;
- focused verification, including test credibility for behavior-bearing tests;
- optional same-shape `batch_key`/members;
- migration/rollout/rollback when relevant.

Prefer vertical integration over horizontal "all models / all services / all tests" phases. Continuously schedule the ready frontier; do not encode rigid waves.

## Compile quality topology

Before finalizing the plan:

1. reuse deterministic structural facts through `scripts/repo_facts_cache.py`, then classify expected owned/touch paths with `scripts/change_surface.py`;
2. compile the provisional quality plan with `scripts/quality_plan.py` using the repository/default quality profile;
3. persist the quality-plan path/id with the run;
4. compile the minimal probe artifact plan and targeted repository verification plan; rank checks with historical test impact when samples exist;
5. run deterministic `scripts/precompute.py` for routes/context hashes/scheduler snapshot without model or worker spend;
6. include only **required** gates, shared probe groups and selected checks in the human plan summary.

Quality profiles change evidence depth, not whether required correctness/safety gates are true. Do not manually add every available specialist gate.

## Challenge the plan

Check:

- smallest slice proves the riskiest assumption first;
- every requirement maps to implementation or verification;
- every task is justified by requirement/risk/enabling work;
- compatibility/migration/operational boundaries are explicit;
- adjacent interfaces agree;
- expected capabilities exist before dispatch;
- tasks earn one meaningful test/review unit;
- low-risk same-shape work is batched;
- `Review Focus` has at most five plausible failure modes;
- plan records decisions, not future function bodies.

Material web UI uses `web-design`; use `creative-web` only when interaction/motion/spatial behavior is part of the experience itself. Other specialist kinds route through the unified facade rather than duplicating model tables in the plan.

## Output

Produce:

1. short architecture summary + key decisions/pointers;
2. Global Constraints;
3. `## Review Focus` with 0-5 items;
4. dependency-graph work units;
5. provisional quality topology: profile, required gates, shared probe groups;
6. `## Initial ready frontier`;
7. verification matrix with stable requirement ids mapping requirements to tests/checks/gates/runtime proofs.

For substantial work, persist the plan in the configured plans directory and link the originating spec. Run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/plan_guard.py" --plan <plan> --require-dag
```

Add `--spec <spec>` when persisted. Fix guard failures before handoff.

Do not implement during `/plan` unless explicitly asked to combine planning/execution; `/flow` exists for that.
