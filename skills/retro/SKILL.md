---
name: retro
description: "Retrospect on a Gearbox coding run or session and suggest concrete improvements to the agent environment: navigation, deterministic checks, coding standards, steering files, tooling, model routing, task packets, evidence and review placement. Does not re-review the feature code."
disable-model-invocation: true
---

# Retrospect on the engineering environment

The user wants to improve the **next** engineering run, not reopen the feature that just shipped.

A retro studies the primary evidence of a session/run and asks:

> What made the agent slower, less reliable, more expensive, or more confused than it needed to be, and what durable change to the environment would prevent that next time?

Do not turn this into another code review. Do not invent findings from vibes. Every recommendation needs evidence from the run.

## Input

Accept any of:

- no argument: retrospect on the current Gearbox run/session if one is identifiable;
- a Gearbox run id or issue number;
- a PR number/URL;
- a path to a session log or run directory.

Prefer Gearbox artifacts over replaying conversation history when both exist.

For a Gearbox run, read only the smallest useful primary-source set first:

1. `.gearbox/runs/<run>/state.json`
2. `dag.yaml`
3. `evidence.json`
4. task `worker-result.json`, review results and repair packages only for tasks that failed, retried, escalated or produced material findings;
5. `learning-candidates.md` when it helps distinguish repository knowledge from agent-environment problems;
6. the final PR technical report when available.

Expand to session logs or repository files only when a candidate finding requires proof.

## What to look for

### 1. Navigation

Look for time/context lost finding the correct files, hidden dependencies, duplicated reconnaissance, or workers reading large areas because the packet lacked a pointer.

Prefer a **navigation pointer** over copying knowledge into steering files.

Good destinations:

- a short pointer in `CLAUDE.md` / `AGENTS.md`;
- a focused existing doc;
- a new focused doc only when no suitable reference exists;
- `docs/solutions/` only when the information is a durable repository fact/root cause. If so, recommend `/gearbox:learn` rather than duplicating it in retro.

Keep steering files sparse. They are loaded into many agent contexts.

### 2. Deterministic guardrails

Classify every recurring coding-standard problem as **mechanical** or **judgement** before recommending prose.

Mechanical examples:

- banned API/import shape;
- naming/file-location rule;
- generated-file rule;
- formatting/type/lint constraint;
- test command that must always run;
- dependency boundary that tooling can detect.

Mechanical findings should become a deterministic check where practical:

- linter/compiler rule;
- dependency check;
- unit/integration test;
- pre-commit hook;
- CI job;
- Gearbox hook/validator.

Do **not** spend recurring model tokens reminding agents about something a machine can reject.

A repository with no meaningful CI/pre-commit/lint/typecheck/test guardrail is itself a possible finding when the run exposed preventable mistakes.

### 3. Judgement standards

For genuine judgement calls that cannot be mechanically enforced, recommend a review-time standard, preferably in an existing `CODING_STANDARDS.md` or equivalent.

Examples:

- what counts as an acceptable abstraction;
- repository-specific error-handling expectations;
- when a compatibility layer is justified;
- domain-specific API design judgement.

Do not burden implementation packets with broad review standards unless the task needs that rule to satisfy the spec. Reviewers have lower context pressure and are the better place to enforce broad standards.

### 4. Steering files

Inspect `CLAUDE.md` / `AGENTS.md` only when evidence suggests the agent was missing a global pointer or instruction.

Recommend additions sparingly. Prefer:

- short navigation pointers;
- one repo-wide invariant that truly applies almost everywhere;
- links to focused docs.

Avoid turning steering files into a handbook.

### 5. Tooling and information access

Look for repetitive manual work that a stable tool could replace:

- discovering test commands repeatedly;
- awkward browser/UI evidence capture;
- inaccessible schemas/docs;
- missing local scripts;
- missing fixtures;
- weak observability;
- repeated shell pipelines.

Recommend the smallest durable tool or command wrapper.

### 6. Gearbox routing and delegation

Use Gearbox telemetry when available.

Look for:

- Luna tasks that repeatedly needed Sol;
- Sol/high tasks that should have been split rather than escalated;
- Astra use that did not buy anything;
- wrong provider choice for the task shape;
- repair tasks caused by insufficient ownership boundaries;
- workers modifying overlapping seams;
- packets missing an interface/constraint that forced broad exploration;
- task reviewers discovering information that should have been in the packet;
- final review finding issues that should have been caught by task review;
- parent/control-plane behavior trying to compensate for weak worker contracts.

Prefer changing classification/routing rules only when there is repeated or high-cost evidence. Do not overfit the router to one weird task.

### 7. Verification and evidence

Look for:

- checks discovered too late;
- duplicated expensive suites;
- missing targeted feedback loops;
- flaky checks;
- UI evidence that required manual archaeology;
- claims that were difficult to tie to `evidence.json`;
- CI failures that local verification could have caught.

Recommend better feedback loops, not more blanket checks.

### 8. DAG and repair-loop quality

Look for:

- tasks too large to review cheaply;
- unnecessary serial dependencies;
- parallel tasks touching the same seam;
- repair cycles caused by a bad initial split;
- repeated re-planning of facts already known;
- blockers that should have been caught by spec clarification or DAG preflight.

## Severity

Rank candidates by expected future cost:

- **HIGH**: likely to cause correctness/safety failures, repeated failed runs, expensive escalations, or major context waste;
- **MEDIUM**: recurring friction or review churn with a clear durable fix;
- **LOW**: small but repeatable efficiency improvement.

Do not list speculative or one-off trivia just to fill the report.

## Output

Present the findings in severity order. For each finding include:

- **Evidence**: exact run artifact, event, retry, review finding, path or measured symptom;
- **Why it matters**: the recurring failure/cost it creates;
- **Class**: navigation | deterministic-check | judgement-standard | steering | tooling | routing | verification | DAG;
- **Change**: the smallest durable improvement;
- **Destination**: exact file/tool/check/config location that should own the improvement;
- **Expected effect**: what should disappear or become cheaper on the next run.

Then finish with:

### Keep as-is

Call out 1-3 parts of the environment that worked well enough that changing them would add ceremony without value.

### Recommended next actions

Give at most 5 actions, ordered by leverage. Prefer deterministic/environment fixes before prompt prose.

## Mutation policy

By default, **do not edit anything**. A retro is a diagnosis and proposal.

If the user asks to apply selected recommendations, do that as a separate explicit step. Do not silently change routing, CI, hooks, `CLAUDE.md`, `AGENTS.md`, or coding standards during the retro itself.

## Relationship to /learn

- `/gearbox:learn` captures reusable truths about the repository/system.
- `/gearbox:retro` improves the environment in which agents work.

If a finding is really a hidden domain invariant or root cause, route it to `/learn`.
If a finding is "agents keep missing X because the repo/tooling does not expose it well", it belongs in `/retro`.
