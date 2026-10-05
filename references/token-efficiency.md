# Token-efficient orchestration

Gearbox spends context in proportion to risk. The goal is not the fewest tokens at any cost; it is to avoid paying repeatedly for information that is already known or irrelevant to the current decision.

## Default profile: efficient

Use these defaults unless `.gearbox/config.md` explicitly chooses a stricter profile.

### Brainstorm by decisions, not transcript

For `/brainstorm`, keep a rewritten decision ledger rather than appending the entire dialogue to downstream context. Normally keep it under about 800 words and carry forward only accepted outcomes, material constraints, acceptance examples, meaningful rejected alternatives, and open decisions.

Ask high-leverage product/domain questions only. Let the repository answer repository facts. Once the spec is accepted, downstream work reads the spec and does not need the brainstorm transcript.

If the brainstorm creates a GitHub issue from the spec and immediately enters the loop, use the accepted spec directly as requirements input and the issue as tracker context. Never pay for an immediate spec → issue → spec reconstruction.

### Context pointers before copied context

Prefer a short pointer to authoritative material over copying it into prompts. A pointer should say what the material contains and when this task needs it.

Examples:

- `GLOSSARY.md#Payments` instead of pasting the whole domain vocabulary;
- `.gearbox/runs/<id>/research/oauth.md` instead of pasting source notes;
- a symbol/file path instead of a copied implementation;
- an ADR path instead of restating the decision history.

Shared behavior between Gearbox skills belongs in `references/` or agents/scripts. Do not assume merely naming another slash command loads its behavior.

### Read once, distill once

The orchestrator reads the issue, repository instructions, relevant architecture, and plan. It then writes compact run artifacts under the self-ignored `.gearbox/runs/` workspace. Workers receive a task packet, not the parent conversation and not the whole issue history.

Do not make every worker reread the full spec, plan, issue comments, or repository documentation.

### Soft context budgets

These are targets, not correctness limits. Exceed them only when omitting information would create material risk.

- brainstorm decision ledger: about 800 words or less for ordinary ideas;
- minimal issue/spec working artifact: about 1,000 words or less for ordinary work;
- repository facts used by the run: about 40 concise bullets or less;
- implementation task packet: about 1,200 words or less;
- task reviewer input: task acceptance slice + task diff/paths, not the full branch history;
- reviewer report: findings only, with at most 6 material findings by default.

Prefer paths, symbols, commit/base refs, and commands over pasted file bodies. State the intended model for each dispatch; use a capable but cheaper bounded model for task review/ordinary simplification, and reserve the session's strongest model for orchestration or final review when the risk warrants it. Let a worker inspect its local worktree when it needs source detail.

### Dispatch only when delegation pays

Apply `references/delegation-gate.md` to auxiliary agents. A dispatch needs one concrete payoff: flood protection, independent judgment, true parallel work, or a genuinely selectable model. Product mutation workers and configured role gates remain mandatory; this rule removes decorative analysis agents, not execution ownership.

### Isolate research legwork

When a decision depends on external/current facts, give one question to `researcher`. Store the note in the run directory and return a pointer. The parent should not spend its main context browsing documentation for facts a subagent can isolate.

### Ready-frontier concurrency

Use `references/frontier-scheduling.md`. Batch qualifying low-risk same-shape micro-work into one worker/review unit, and dispatch ready tasks as soon as dependencies integrate instead of waiting for artificial waves. Frontier state is metadata; computing it should not require reopening task bodies.

### Pre-flight the plan once

Before the first worker dispatch, sanity-check the whole DAG once for contradictory requirements, missing interfaces, overlapping write ownership, and tasks that would violate global constraints. Fix the plan up front instead of rediscovering the same defect in multiple workers.

### One task reviewer, two verdicts

Do not run separate spec and code-quality reviewer agents for the same task. When a fresh per-task review is warranted, use one `task-reviewer` agent and require two independent verdicts in one pass:

1. **SPEC**: does the task diff satisfy exactly its assigned acceptance slice without material overbuild?
2. **QUALITY**: is the implementation correct, maintainable, adequately tested, and safe within that slice?

The reviewer checks SPEC first. If SPEC fails, stop and fix before spending review effort on polish.

### Hybrid cross-provider task review

In `model_policy: hybrid`, every implementation task receives exactly one fresh opposite-provider review before integration:

- Claude implementation → Codex review;
- Codex implementation → Claude review.

This replaces the old hybrid behavior where low-risk tasks could skip a fresh reviewer. Keep it token-efficient by scaling the reviewer, not by removing provider diversity: bounded work uses Luna/low or Haiku/low, normal work uses Sol/medium or Sonnet/medium, and stronger reviewers are reserved for deep/exceptional tasks.

Every worker still performs a compact self-review, and the orchestrator still inspects the real diff. The opposite-provider reviewer returns both SPEC and QUALITY verdicts in one pass. Do not add another task reviewer unless there is a concrete unresolved disagreement.

For non-hybrid policies, retain adaptive per-task review: require a fresh reviewer for medium/high risk, contracts/shared seams, weak evidence, surprising diffs, trust/data boundaries, concurrency, persistence, migrations, or orchestrator disagreement; low-risk bounded work may skip it.

### Review only the task at task time

A task reviewer begins with the task packet and task diff. It should inspect changed files and directly dependent code only. Repo-wide searches or broad tests require a concrete suspicion, not curiosity.

The final branch review is where broad integration concerns belong.

### Tests in layers

- RED/GREEN: narrow test for the task.
- After each integration wave: affected focused checks only.
- After Ponytail edits: affected checks only.
- Before shipping: full-enough repository-native tests/lint/typecheck/build once.

Do not run the expensive full suite after every worker unless the repository makes that necessary for credible isolation.

### Compact evidence

Store verbose command logs under the transient run directory. Pass around:

- command;
- exit status;
- short relevant failure/pass summary;
- log path when deeper inspection is needed.

Do not paste hundreds of successful test lines into worker prompts or PR comments.

### Escalate, do not prepay

Start with the smallest context and reviewer topology that can safely decide the task. Expand only on evidence: failing tests, ambiguous requirements, hidden coupling, reviewer disagreement, or high-risk boundaries.

### Repair loops consume deltas, not history

When `/loop` or `/issue` enters a repair cycle, reuse the existing spec, repo facts, DAG and accepted task evidence. Track stable finding ids with `scripts/repair_findings.py`; do not spend a third dispatch on the same failed strategy. Create only the repair packet required by the failed gate. Review prior validated findings plus the repair diff rather than repasting the entire issue history.

Do not rerun broad architecture reconnaissance, full Ponytail, or both final reviewers after a tiny local correction unless the repair changed the corresponding risk surface. Always run full-enough verification again before PASS.

The default cycle limit is 3. Reaching the limit is a stop condition, not an excuse to keep spending context.

### Conditional learning

Collect learning candidates as short ledger entries during the run, then evaluate them once after PASS. Search `docs/solutions/` for duplicates before invoking `/learn`. Routine work should cost nearly zero learning tokens and create no durable note.

### Final cross-model review

Spend the larger review budget once, on the post-Ponytail integrated diff. For substantial `/issue` runs, use one independent Claude final reviewer and one stateless read-only Codex reviewer when available. Their prompts should share requirements but not each other's conclusions.

Do not recursively ask reviewers to review other reviewers.

### Solution-memory cleanup

Do not scan the entire `docs/solutions/` corpus during normal issue loops. `/clean-solutions` is explicit maintenance work. It inventories titles/tags/pointers first, identifies suspects cheaply, and deep-reads only notes with concrete invalidation signals. Current issue loops reconcile only the solution notes they actually retrieved and proved stale.

## Route model spend per task

Use `references/model-routing.md`. Record model/effort in the DAG and escalate only on evidence. Reusing a stronger model for every task is not the efficient profile.
