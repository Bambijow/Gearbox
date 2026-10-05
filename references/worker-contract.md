# Stateless worker contract

Gearbox workers receive a bounded context packet. Every dispatch is preceded by a recorded engine/model/effort/risk assignment from `references/model-routing.md`; and return structured evidence. They do not inherit the orchestrator's conversation and must not guess missing architecture. Read `references/control-plane.md`: workers, not the parent, own all product mutations in orchestrated runs.

## Context packet

A worker prompt should contain only what the task needs:

```text
ROLE
You are an isolated implementation worker. You are not the project orchestrator. All product edits for this task belong to you, not the parent.

ISSUE / OUTCOME
Short plain-language outcome.

SPEC SLICE
Exact acceptance criteria and invariants this task owns.

GLOBAL CONSTRAINTS
Only cross-task rules that genuinely bind this task.

YOUR TASK
One bounded implementation result.

DEPENDENCIES ALREADY TRUE
Facts produced by prerequisite tasks.

INTERFACES
Inputs/contracts this task consumes and outputs/contracts it must provide to dependent tasks.

OWNERSHIP
You may modify:
- path/**

Do not modify:
- other shared paths unless blocked; report the blocker instead.

REPOSITORY CONVENTIONS
Only relevant confirmed rules.

TDD / VERIFY
Commands and expected behavior.

CONSTRAINTS
No pushes, no secrets, no unrelated refactors, no weakening tests. A local task commit is allowed/encouraged when the packet requests it; never publish it.

SELF-REVIEW
Before reporting, compare the diff to the assigned spec slice, check for scope growth, and record RED/GREEN evidence when TDD applies.

OUTPUT
Return JSON matching the provided schema. Keep it compact. The orchestrator will inspect your actual diff and task logs.
```

Include relevant symbol names and paths discovered by reconnaissance. Do not paste the whole chat, full plan, successful command logs, or huge files when the worker can read them in its worktree. Use the task packet as the sole handoff whenever possible.

## Write isolation

Each concurrent write worker gets its own git worktree and branch. The parent control plane should create/remove these through `scripts/worktree_manager.py` and record them in run state rather than performing ad-hoc product-tree shell mutation. Parallel tasks must have non-overlapping ownership or an intentionally conflict-free seam.

Prefer one local task commit after focused verification, scoped strictly to owned paths, so accepted integration can be mechanical. If a local commit is unavailable, leave the worktree intact and report changed/untracked paths exactly. Workers never push, open PRs, merge, or change remote state. The parent never recreates the worker change by hand; the `integrator` agent applies accepted output.

## Stateless Codex invocation

Preferred execution uses `codex exec --ephemeral` with the worktree as cwd, a JSON output schema, and a last-message output file. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/codex_worker.py"` wraps that shape when Gearbox is installed as a plugin.

Do not use Codex's own nested multi-agent orchestration for these workers. Gearbox owns the DAG and wants one disposable context per worker.

## Acceptance

A worker result is accepted only after the orchestrator verifies:

- changed paths fit ownership;
- diff implements the assigned spec slice;
- test changes are legitimate and not weakened;
- focused verification passes;
- no unexpected generated/secret/debug artifacts exist.


## Review package

When a task needs independent review, do not paste its diff into the reviewer dispatch. Write the diff and compact review metadata under the transient task directory, then pass only those file paths to the read-only reviewer. The package should identify the task packet, base/head refs, changed paths, focused verification status, and diff file.

## Incomplete work

If a worker cannot complete the task, report the blocker or partial state. The parent must dispatch a repair/replacement worker. It must not take over implementation itself.


## Integration synchronization

Each implementation worker starts from the integration SHA in its packet. Before reporting done, synchronize the latest integration tip into the task branch/worktree and rerun focused checks.

Return:

- `integration_base_sha`: integration tip successfully synchronized before handoff;
- `head_sha`: final task head;
- changed paths;
- task commit when created;
- focused verification/evidence.

This is part of the completion criterion. If synchronization conflicts, report the conflict while the worker still owns the task context rather than hiding it.

## Context pointers

Packets should point to glossary, ADR, research, solution and source artifacts rather than paste them wholesale. Read only the pointers relevant to the assigned slice.

## Secret safety

Worker results, logs and evidence are potentially publishable. Follow `references/secret-redaction.md`; never return raw credentials, tokens, cookies, private keys or signed URLs.
