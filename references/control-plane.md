# Control-plane invariant

During orchestrated Gearbox runs (`/issue`, `/loop`, `/flow`, `/brainstorm` when it continues into implementation, `/resume`, and `/continue-pr`), the main Claude conversation is a **control plane**, not an implementation worker.

## Main orchestrator responsibilities

The main thread may:

- read repository code, tests, docs, Git history, issue/PR state and run artifacts;
- shape requirements and ask clarification questions;
- write/update Gearbox transient artifacts under `.gearbox/runs/`;
- write/update specs and plans in the configured `specs_dir` / `plans_dir`;
- build/pre-flight the DAG;
- choose engine/model/effort and dispatch workers/reviewers;
- inspect real worker diffs and evidence;
- adjudicate review findings;
- decide whether to integrate, repair, simplify, learn, verify, ship or stop.

The main thread **must not author product changes** during an orchestrated run. Product changes include source code, tests, migrations, application configuration, public documentation, generated artifacts intended for commit, and `docs/solutions/` knowledge notes.

There is no "small enough for the orchestrator" exception. A one-line product fix still goes to the cheapest suitable worker.

## Delegated mutation roles

Product mutation is delegated by role:

- implementation / repair → `worker-*` Claude agent or stateless Codex worker;
- integration mechanics → `integrator` agent;
- post-integration simplification → `ponytail-simplifier` agent;
- durable solution memory → `knowledge-curator` agent;
- final verification → `verifier` agent;
- commit/push/PR publication → `shipper` agent.

Review agents remain read-only.

If a worker result is incomplete, wrong or conflicts with another task, the orchestrator dispatches a repair worker. It does not "finish the last 10 lines" itself.

## Mechanical enforcement

Gearbox ships a plugin `PreToolUse` guard. While an orchestrated command is active:

- main-thread `Write`, `Edit` and `NotebookEdit` are denied outside transient run artifacts plus configured specs/plans;
- main-thread Bash is restricted to read-only discovery and approved Gearbox orchestration scripts;
- subagents are identifiable through hook `agent_id` / `agent_type` and are not subject to the main-thread product-write ban;
- the guard is deactivated when the command turn ends and reactivated by `/resume` on a later turn.

The hook is the enforcement boundary. Prompt instructions are defense in depth, not the only control.

## Provenance invariant

Every committed product path in an orchestrated run must be attributable to a delegated mutation role. The PR technical report should be able to say which task/agent produced each material change group.
