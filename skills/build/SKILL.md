---
name: build
description: "Implement an approved plan or scoped change with SDD traceability, TDD where useful, isolated workers when warranted, minimal scope, and explicit verification."
argument-hint: "[plan path, issue, or scoped task]"
disable-model-invocation: true
---

# Build with short evidence loops

Implement the requested behavior, not an imagined future platform.

## Orient

Read `.gearbox/config.md` when present, repository instructions, the relevant spec/plan/issue, and the code you are about to change. Check the working tree before editing so unrelated user changes remain untouched.

Maintain traceability from requirement → work unit → verification. Apply `references/test-credibility.md` whenever tests are created or relied on as behavior proof. For a substantial issue workflow, `/issue` owns the DAG and worker scheduling; this skill executes individual units faithfully. Read `references/token-efficiency.md` when the parent workflow provides a task packet. For a multi-task plan, use `references/frontier-scheduling.md`: execute only ready tasks, batch qualifying same-shape micro-work, and carry relevant glossary/ADR/research/solution context pointers instead of copied bulk context.

## Development loop

For each work unit:

1. Identify the observable behavior or invariant being added or changed.
2. Choose the narrowest credible evidence seam.
3. Use RED → GREEN → REFACTOR by default for business logic, regressions, state transitions, parsers, transformations, API contracts, concurrency behavior, and other behavior where a failing check provides signal.
4. Verify the red state fails for the intended reason and that the test has a credible mutation story rather than merely detecting source text/change.
5. Make the smallest coherent implementation.
6. Run the narrow check, then expand verification as confidence grows.
7. Perform a compact self-review against the assigned acceptance slice and re-read the diff for accidental scope growth before moving on.

Do not manufacture brittle tests for static wiring, generated code, or behavior already better covered by an existing integration/e2e check. Never weaken a legitimate test merely to turn the suite green.

## Agent discipline

When `/build` is invoked **manually as the user’s direct coding command**, the active Claude session may implement the scoped change unless the user asked for delegation.

When `/build` is executing inside an orchestrated `/issue`, `/loop`, `/flow`, `/brainstorm --issue/--ship`, `/resume`, or `/continue-pr` run, `references/control-plane.md` overrides that convenience: **every product mutation is worker-owned, even a one-line edit**. Choose the cheapest suitable worker rather than letting the parent edit. The parent inspects actual diffs, validates reviews and dispatches `integrator`; it does not finish incomplete worker code itself.

For parallel write tasks, use separate git worktrees and path ownership. Before a worker reports done, synchronize the latest integration tip into its branch/worktree, rerun focused verification, and report `integration_base_sha` plus `head_sha`.

Codex workers should be stateless `codex exec --ephemeral` jobs with a bounded context packet. They do not own architecture, pushes, or PRs. They may create a local task commit in their isolated worktree when that makes mechanical integration safer; they never publish it. Do not paste the whole spec/plan or large source files into their prompt when paths and symbols let them inspect the worktree directly.

## Design discipline

Match existing architectural seams before introducing new abstractions. Prefer existing codebase primitives, standard library/framework/native platform behavior, and direct code over speculative generic frameworks.

Do not silently change public behavior, configuration defaults, schemas, or compatibility promises outside the spec.

## Verification

Run configured validation commands that are relevant and affordable. Prefer focused checks during a work unit; defer expensive full-suite/lint/build passes to the integration/final verification gate unless broad execution is necessary to establish correctness. Inspect the final diff and test changed behavior directly when possible.

Report what changed, completed work units, exact checks/results, checks not run and why, and residual risks.

In a manual build, do not commit or push unless explicitly authorized. In an orchestrated worker task, a local unpushed task commit is allowed when the packet asks for it; remote publication remains the `shipper` role.
