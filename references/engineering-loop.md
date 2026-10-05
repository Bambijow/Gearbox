# Gearbox engineering loop

This is the shared convergence protocol for `/loop`, `/issue`, and substantial `/flow` runs.

The loop exists to converge on a trustworthy change, not to repeat the same expensive pipeline. Cycle 0 does the broad work. Later cycles are narrow repair loops driven by concrete failed gates.

## Hard control-plane boundary

Read `references/control-plane.md` before dispatch. During this shared loop the main Claude conversation is a scheduler/architect/judge, **not a coding agent**. It may write transient run artifacts and configured specs/plans, but it does not modify product code, tests, migrations, application config, public docs, generated committed artifacts, or `docs/solutions/`. There is no small-edit exception.

Every product mutation is delegated:

- implementation and repair → routed Claude/Codex worker;
- accepted integration → `integrator`;
- structural simplification → `ponytail-simplifier`;
- durable solution memory → `knowledge-curator`;
- verification → `verifier`;
- commit/push/PR publication → `shipper`.

The plugin `PreToolUse` guard enforces the main-thread boundary while orchestrated commands are active. If a worker is incomplete or a cherry-pick conflicts, dispatch a repair worker. The parent must never complete the code itself.

## Inputs

Normalize one of these sources:

- GitHub issue URL or number;
- accepted spec file;
- accepted spec file plus an optional GitHub tracker issue created from it;
- grounded free-form request.

`/brainstorm` is an upstream conversational entry: it converges on an accepted spec, optionally creates the tracker issue, then hands both into this loop. When a tracker issue was generated from the accepted spec, keep the spec as the requirements source instead of round-tripping through issue → spec again.

Create a transient run directory under `.gearbox/runs/<run-id>/` containing only compact orchestration state:

- `intake.md`: source requirements artifact, optional tracker issue, outcome, constraints, links;
- `spec.md`: minimal decision-complete SDD spec;
- `repo-facts.md`: distilled repository facts read once by the orchestrator;
- `dag.yaml`: dependency-aware work units;
- `state.json`: current cycle, gate states, refs, unresolved findings and clarification blocker state;
- `spec-clarification.json`: compact deductions, reversible assumptions, blocking questions and answers when shaping is ambiguous;
- `learning-candidates.md`: compact candidate ledger for `/learn`;
- `tasks/<id>/...`: task packets, diffs, worker results and focused evidence;
- `evidence/`: transient UI evidence and verification outputs.

Do not persist the run directory in the product diff. Initialize/acquire `state.json` and the run lock immediately after creating/reusing this directory so clarification blockers are durable even before planning.

## Spec clarification gate before planning

Apply `references/spec-clarification.md` before building the implementation DAG. Use narrow repository/issue investigation to resolve missing facts and seed `repo-facts.md`; do not ask the user for information the repository already proves.

Every gap becomes DEDUCED, ASSUMED, or QUESTION. Only low-impact reversible engineering choices may be assumed. If any QUESTION would materially change product/domain semantics, permissions, data lifecycle, public compatibility, billing, safety, migration behavior, or user-visible workflow, persist the independent questions as one compact batch and stop with `state.status=BLOCKED`, `state.phase=SPEC`, and `state.blocker.code=SPEC_BLOCKED`.

`--auto` never bypasses this gate. While `SPEC_BLOCKED`, do not perform model preflight, dispatch workers/reviewers, create task worktrees, or consume implementation budgets. `/resume` continues from the stored questions after the user answers.

Repository facts gathered to settle clarifications are reused later; do not pay for the same reconnaissance twice.

## Domain language before architecture

Before shaping architecture or naming new concepts, apply `references/domain-modeling.md`.

- If `GLOSSARY-MAP.md` exists, load only the relevant context glossary.
- Otherwise read root `GLOSSARY.md` when present.
- Carry canonical terms into the spec, DAG packets, tests, reviews and PR copy.
- If a term or qualifying architecture decision is actually resolved during the run, delegate the smallest durable glossary/ADR edit to `domain-curator`.

When an implementation decision depends on a current external fact, dispatch `researcher` using `references/research.md` and store the answer under the run directory. Downstream packets receive the research note path plus the decision-relevant conclusion, not the research transcript.

For hard-to-reverse shared interface/seam decisions, apply the `references/codebase-design.md` design-it-twice gate before freezing the DAG. Ordinary features do not pay for parallel architecture proposals.

## Read reusable knowledge early

Before inventing a solution, search `docs/solutions/` for relevant prior incidents, invariants, traps, migrations, and architecture lessons. Pull only directly relevant notes into `repo-facts.md` as short pointers. Follow their source links only when needed.

Historical notes are evidence, not authority. Current code, tests, and accepted requirements can supersede them. If this run conclusively proves a retrieved solution stale, record that fact in the learning candidate ledger so the final learning gate can refresh, merge, or delete that specific note. Do not run a full `/clean-solutions` corpus audit inside every issue loop.


## Persistent state, model preflight, evidence and budgets

Persistent run state is already initialized before clarification. After the spec clarification gate is RESOLVED, initialize/refresh `evidence.json`, classify task risk, and resolve the model policy from `references/model-routing.md`. The pre-flighted DAG records engine/model/effort/risk for every executable node. Consume dispatch/review/escalation budgets from `references/risk-budget-policy.md`.

When model selection is unresolved, ask before the first worker dispatch. This is deliberately after DAG preflight so the user can see the proposed routing, but before implementation work begins. If a stored policy is valid, do not interrupt each run.

All gate claims map to `evidence.json`. State and evidence, not chat history, make the loop resumable and make PR reporting auditable.

## Cycle 0: build the change

1. Normalize intake and create or reuse the minimal spec.
2. Run the spec clarification gate; stop at `SPEC_BLOCKED` when required.
3. Reconcile architecture facts once, reusing facts already gathered during clarification.
4. Build and pre-flight the DAG once.
5. Dispatch bounded implementation workers in dependency waves. Every product edit, including tiny edits and test/doc changes, belongs to a worker.
6. Workers use RED -> GREEN -> REFACTOR where the failing check provides real signal. Before returning they synchronize the latest integration tip into their task branch/worktree, rerun focused verification, and report `integration_base_sha`, `head_sha`, actual diff/evidence and preferably one local unpushed task commit.
7. Inspect every worker diff centrally without editing it. In `hybrid`, resolve and run exactly one opposite-provider task review before integration: Claude implementation → Codex review; Codex implementation → Claude review. The review is task-scoped and returns SPEC then QUALITY verdicts.
8. Validate review findings centrally. When repair is required, dispatch the same or a fresh implementation worker; the parent never patches the finding itself.
9. After the task review gate passes, delegate mechanical integration to `integrator`. Integration conflicts become repair tasks.
10. After each accepted integration, delegate affected focused checks to `verifier`, update task status, recompute the ready frontier, and immediately dispatch any newly-ready non-conflicting tasks.
11. Run the post-integration `ponytail-simplifier` gate.
12. Run final independent cross-model review on the simplified integrated diff. This is integration-level review and does not replace the per-task opposite-provider gate.
13. Delegate full-enough repository-native verification and required UI/UX evidence to `verifier`.

Record reusable surprises as compact learning candidates while they are fresh. Do not invoke `/learn` yet just because something was interesting.

## Gate result

Classify the integrated state as one of:

### PASS

All of these are true:

- every acceptance scenario maps to credible evidence;
- required tests/checks pass;
- no validated Blocker or Important review finding remains;
- no required migration/security/compatibility concern is unresolved;
- required UI/UX evidence exists and was inspected;
- the simplification gate has no unresolved material simplification;
- no worker or integration conflict is being hand-waved.

### REPAIR

There is a concrete, bounded defect that can be corrected without inventing new product semantics. Examples: failing test, validated review finding, integration bug, missed acceptance case, unsafe edge case, or material over-engineering.

### BLOCKED

Stop instead of looping when any of these apply:

- a material product/domain decision is missing;
- required authorization/tooling is unavailable;
- external state makes verification impossible;
- requirements are contradictory;
- the requested behavior would require a destructive or irreversible action not authorized by the user;
- the loop has reached its configured cycle limit without convergence.

## Repair cycles

Default `max_cycles` is 3 total convergence cycles after the initial implementation pass unless repository config overrides it. A cycle exists only when a failed gate created actionable repair work.

For each repair cycle:

1. Convert only validated failed gates into repair tasks.
2. Reuse the existing spec, repo facts and DAG knowledge. Do not redo broad reconnaissance.
3. Dispatch the smallest worker topology that can fix the defects.
4. Run focused RED/GREEN checks for the repaired behavior when applicable.
5. Inspect the repair diff centrally without editing it. In `hybrid`, run the opposite-provider task review for each implementation repair before integration, using only the delta review package.
6. Validate findings; if repair is still needed dispatch another bounded worker. Delegate accepted integration to `integrator`, then delegate affected checks to `verifier`.
7. Re-run Ponytail only when the repair introduced or materially changed structure, duplication, abstractions, or control flow. For tiny local fixes, perform a targeted simplification check instead of paying for a full pass.
8. Re-review the repaired findings and changed scope. Run another broad final review only when the repair changed architecture, public contracts, security/data boundaries, or a substantial part of the integrated diff.
9. Run full-enough verification before declaring PASS.

Never loop because a reviewer has a subjective style preference. Never ask a reviewer to review another reviewer.

## Learning candidate ledger

During shaping, implementation, debugging, integration, simplification and review, append a candidate only when there is plausible reusable value. Keep each entry short:

```markdown
- trigger: hidden cache invalidation coupling
  evidence: tests/cache/foo_test.ts + src/cache/foo.ts
  insight: invalidation must happen after transaction commit
  reuse: likely for future write paths
  duplicate_checked: false
```

Good candidate triggers include:

- non-obvious root cause;
- undocumented invariant or coupling;
- misleading architecture or stale documentation;
- failed approaches whose reason matters later;
- recurring migration, security, operational, performance or debugging trap;
- review finding that exposed a repository-specific rule worth remembering.

Do not add routine implementation facts, generic best practices, or facts already clearly documented.

## Learning gate

Run this only after the engineering loop has converged to PASS and before shipping, so any durable note can be included in the PR.

1. Read `learning-candidates.md` once.
2. Search `docs/solutions/` for duplicates, existing notes to update, and any retrieved note the run proved stale or contradicted.
3. Reconcile proven-stale affected notes using `/clean-solutions` rules, then apply the `/learn` qualification gate to genuinely new durable knowledge.
4. If nothing qualifies, record `learn: skipped` with a short reason in `state.json` and continue.
5. If one or more candidates qualify, dispatch `knowledge-curator` using `/learn` semantics for the smallest set of distinct durable lessons. Normally create or update at most one solution note per issue; allow more only for genuinely unrelated reusable lessons.
6. Record created/updated `docs/solutions/...` paths in run state and include them in PR technical evidence.

The learning gate must not reopen settled implementation scope. `/learn` writes durable knowledge, not another feature.

## Shipping gate

Shipping is allowed only on PASS. `--ship` authorizes the orchestrator to dispatch `shipper` for commit, push, PR creation/update and PR comments, never merge or deployment. The parent does not perform publication Bash mutations itself during the guarded run.

The PR description remains non-technical. The technical PR comment must include the loop outcome, material repair cycles, verification, Ponytail reductions, cross-review resolution, durable solution notes created/updated, and UI evidence when applicable.

## Token policy

Cycle 0 pays for broad understanding once. Repair cycles consume deltas:

- reuse file-based artifacts instead of repasting history;
- scope worker packets to the repair task;
- scope reviewer input to prior findings plus changed paths/diff;
- keep successful logs on disk and propagate status plus log paths;
- do not rerun broad discovery or duplicate final reviewers unless the repair changed the risk surface;
- stop at the cycle limit instead of burning context indefinitely.


## Retrospective recommendation

Do not run a retrospective automatically. At the end of PASS, BLOCKED, or MAX_CYCLES, recommend `/gearbox:retro <run-id>` only when the run contains evidence that the **agent environment** should improve, such as:

- two or more repair cycles caused by the same class of mistake;
- a model/provider escalation that exposed a bad initial routing rule;
- repeated worker or reviewer failure caused by missing context/tool access;
- task packets that forced broad repository exploration to rediscover stable information;
- overlapping task ownership or a DAG split that repeatedly caused integration repair;
- final review discovering a rule that task review or a deterministic check should have caught;
- missing/flaky verification that caused avoidable CI repair;
- meaningful token/dispatch waste caused by repeated navigation or duplicated checks.

A clean routine run should normally end with `retro: not needed`. This keeps retrospectives high-signal and token-efficient.
