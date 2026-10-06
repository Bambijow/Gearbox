# Model and effort routing

Gearbox treats model choice as part of the execution plan, not an invisible runtime accident. The hybrid policy deliberately uses a **small Codex registry** and varies effort before reaching for a more expensive frontier model.

## Preflight

Before the first implementation worker is dispatched, resolve a model policy. If `.gearbox/config.md` already contains a policy, use it. If it does not, ask once and offer to persist the answer.

Recommended choices:

- `auto`: Gearbox chooses engine, model family and effort per task.
- `claude-heavy`: prefer Claude workers; Codex is mainly a stateless second opinion.
- `hybrid`: choose Claude or Codex per task. Recommended default.
- `codex-heavy`: prefer stateless Codex for bounded implementation, keep Claude for orchestration/integration/review.
- `custom`: user supplies allowed models and optional role constraints.

`--models ask` forces the preflight for this run. `--models auto|claude-heavy|hybrid|codex-heavy` overrides the stored policy for this run. `--no-codex` removes Codex from the candidate set.

Do not ask repeatedly once a repository policy is stored unless the user requests it or configured models are unavailable.

## Capability gate before model choice

Read `references/capability-routing.md`. Every task records `required_capabilities`, including an explicit empty list. Capability eligibility is a hard gate before risk/cost/model scoring: a provider that cannot supply a required external capability is not a candidate, however cheap or capable its model is.

Use `scripts/capabilities.py route` when the candidate capability sets are known. Codex MCP availability comes from a sanitized setup snapshot for planning and a live `codex mcp list --json` preflight immediately before dispatch. If exactly one provider satisfies the requirements, route there; if both do, continue with the normal risk/cost policy; if neither does, stop with `CAPABILITY_BLOCKED` instead of spending a worker to discover the missing tool.

For Codex dispatches, pass every required MCP as `--required-capability <name>` and use `--prune-mcp` under the default `required-only` policy. The wrapper disables other configured MCP servers only for that invocation, while retaining the user's Codex config and credentials. A task with `required_capabilities: []` therefore gets no MCP tool schemas unless the run explicitly overrides the policy.

## Forced game-asset specialist routes

Game-asset task kinds bypass the ordinary economy/risk router. Resolve them with `scripts/game_asset_router.py` before normal model routing:

| task kind | forced route | capability rule |
|---|---|---|
| `asset-image` | Codex `gpt-6.1-sol` / medium | direct model generation |
| `pixel-art` | Codex `gpt-6.1-sol` / medium | prefer live Aseprite MCP; direct Sol fallback |
| `model-3d` | Claude `claude-opus-5-5` / high | requires live Blender or Godot |
| `review-3d` | Codex `gpt-6-astra` / high, read-only | requires live Blender or Godot |

These are hard specialist contracts. `auto`, `claude-heavy`, `codex-heavy`, `--no-codex`, normal capability economics and Astra escalation policy do not substitute another provider/model. If the forced route is unavailable, return `GAME_ASSET_ROUTE_BLOCKED`.

A completed `model-3d` task always receives the dedicated `review-3d` Astra gate before asset readiness. When the same task also changes product code, the normal code/task review policy still applies to that code; the 3D gate is additional.

## Preferred Codex registry

Use only three configured Codex model slots by default:

```yaml
codex_models:
  economy: gpt-6-luna
  standard: gpt-6.1-sol
  frontier: gpt-6-astra
allow_codex_default_model: false
codex_frontier_policy: escalation-or-exceptional
```

Treat the exact strings as repository configuration. If the local Codex installation exposes different IDs for Luna, Sol, or Astra, persist those exact IDs during `/setup`.

The intentional mapping is:

- **GPT-6 Luna**: documentation, changelog, formatting, metadata, fixtures, generated mappings, renames, obvious wiring, isolated deterministic test work.
- **GPT-6.1 Sol**: the normal Codex engineering model. Use `medium` effort for ordinary features/bugs and `high` for deep debugging, migrations, persistence invariants, concurrency, auth/security or broad changes.
- **GPT-6 Astra**: frontier escalation only. It is not a normal `high risk` model and must not be selected merely because a task touches a database or security-sensitive area.


## Per-task route

Every executable DAG node must record:

```yaml
execution:
  engine: claude | codex | orchestrator
  role: implementation | research | review | simplify | verify
  model_class: economy | standard | frontier
  model: sonnet | opus | haiku | <configured full model id>
  effort: low | medium | high | xhigh | max | auto
  rationale: one short sentence
```

Choose the cheapest route that can safely satisfy the task.

### Codex deterministic router

For Codex candidates, use `scripts/model_router.py` rather than selecting a model ad hoc. Feed it the task kind, risk, ambiguity, breadth, verification strength and prior failed attempts.

Example:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/model_router.py" \
  --task-kind feature \
  --risk medium \
  --ambiguity low \
  --breadth moderate \
  --verification strong \
  --luna-model "<configured Luna id>" \
  --sol-model "<configured Sol id>" \
  --astra-model "<configured Astra id>" \
  --json
```

The router uses four reasoning tiers but only three models:

- **bounded** → Luna/low (occasionally Luna/medium when the deliverable itself is cheap but risk metadata is noisy);
- **normal** → Sol/medium;
- **deep** → Sol/high;
- **exceptional** → Astra/medium first, Astra/high only when further escalation is justified.

### Hard ceilings

These task kinds are hard-capped to Luna-class execution even if a noisy classifier marks them critical: docs, changelog, formatting, metadata, fixtures, generated mappings, simple renames/wiring and isolated simple tests.

If the work contains a hard architecture decision plus documentation, split it into two tasks:

1. architecture/domain decision → Claude or Sol/high as appropriate;
2. writing the already-decided documentation → Luna/low.

This prevents frontier compute from being spent on prose generation.

### Astra gate

Astra is allowed only when one of these is true:

1. an explicit frontier override was requested for this task;
2. a frontier-eligible deep task has already failed at least twice for reasoning/context reasons and remains difficult after replanning/escalation;
3. the task is simultaneously critical, highly ambiguous, broad, weakly verifiable, and belongs to a frontier-eligible class such as deep debugging, migration, auth/security, concurrency, persistence, architecture, or high-risk adjudication.

Ordinary high-risk work stays on Sol/high first. A failed environment/tool invocation is not a reasoning failure and does not justify Astra.

## Hybrid cross-provider review routing

When `model_policy: hybrid`, every executable implementation task gets a fresh **opposite-provider task review before integration**. Provider diversity is the invariant:

- implementation by **Claude/Anthropic** → review by **Codex/OpenAI**;
- implementation by **Codex/OpenAI** → review by **Claude/Anthropic**.

The reviewer never receives the implementation conversation or another reviewer's conclusions. It receives only the task packet, task acceptance slice, base/head refs or diff path, changed paths, and focused verification evidence.

Resolve the reviewer route with `scripts/review_router.py`, using the implementation task's already-selected tier and risk. Persist the result beside the implementation route in `dag.yaml`:

```yaml
execution:
  engine: codex
  model: gpt-6.1-sol
  effort: medium
review:
  engine: claude
  model: sonnet
  effort: medium
  agent: task-reviewer
  rationale: opposite-provider review for normal Codex work
```

Example router calls:

```bash
# Claude implementation -> Codex reviewer
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_router.py" \
  --implementation-engine claude \
  --task-tier normal \
  --risk medium \
  --json

# Codex implementation -> Claude reviewer
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_router.py" \
  --implementation-engine codex \
  --task-tier deep \
  --risk high \
  --json
```

Default opposite-provider mapping:

| implementation | task tier | independent reviewer |
|---|---|---|
| Claude | bounded | Codex Luna / low |
| Claude | normal | Codex Sol / medium |
| Claude | deep | Codex Sol / high |
| Claude | exceptional | Codex Astra / medium, high only when justified |
| Codex | bounded | Claude Haiku / low |
| Codex | normal | Claude Sonnet / medium |
| Codex | deep | Claude Opus / high |
| Codex | exceptional | Claude Opus / xhigh |

This routing is deliberately asymmetric with cost: a trivial Claude-authored README task is reviewed by Luna/low, not Astra; a bounded Codex task is reviewed by Haiku/low, not Opus. Provider diversity does not mean paying frontier prices for every diff.

A task is not integration-ready until its opposite-provider review has a passing SPEC verdict and no validated blocking QUALITY finding. The orchestrator adjudicates findings against code/tests/spec; reviewers do not command fixes blindly.

If the opposite provider is unavailable, do **not** silently substitute a same-provider reviewer in hybrid mode. Mark the task review `BLOCKED` or request an explicit policy override. `--no-codex` is such an explicit override and disables this cross-provider invariant for that run.

For non-hybrid policies (`claude-heavy`, `codex-heavy`, `auto` when it resolves to a single provider), use the configured adaptive review behavior unless an explicit cross-provider lens is available.

## Claude routing

Use these dimensions: requirement ambiguity, architectural breadth, trust/data risk, debugging novelty, number of seams touched, and strength of deterministic verification.

- **Tier 1 / bounded**: mechanical edits, obvious wiring, generated mappings, isolated tests. Prefer Haiku/low.
- **Tier 2 / normal**: ordinary feature work, bugs, tests, moderate multi-file changes with clear contracts. Prefer Sonnet/medium.
- **Tier 3 / deep**: architecture, subtle debugging, migrations, auth/security, concurrency, persistence invariants, broad refactors, ambiguous cross-cutting behavior. Prefer Opus/high when Claude owns the task.
- **Tier 4 / exceptional**: use xhigh/max sparingly only when evidence shows it is justified.

Codex is preferred for a bounded packet with explicit ownership and strong tests. Claude is preferred when the task needs domain interpretation, cross-task context, architectural judgment, or interactive tool use that depends on the parent plan.

## Claude subagents

Gearbox ships worker agents with fixed effort tiers (`worker-low`, `worker-medium`, `worker-high`, `worker-xhigh`). Their `model` is `inherit`; when Claude Code supports a per-dispatch model override, dispatch the chosen model while selecting the agent whose frontmatter effort matches the route. If a requested model is unavailable, fall back to the closest allowed family and record the fallback in run state.

Claude task reviewers have effort-specific profiles (`task-reviewer-low`, `task-reviewer`, `task-reviewer-high`, `task-reviewer-xhigh`) so Codex-authored work can be reviewed at the matching risk tier. Ponytail simplification stays medium and final cross-review stays high unless risk justifies more.

Record the requested route and, when runtime tooling exposes it, the observed route. Never claim an effort was actually used if it cannot be observed.

## Dispatch fingerprint and deduplication

Before any long-lived/background worker dispatch, compute a stable fingerprint from the exact base SHA, task packet/prompt, provider, model, effort, kind and required capability set with `scripts/invocation_fingerprint.py`. Register it in `children.json`. If `scripts/child_jobs.py register --fingerprint ...` reports `DUPLICATE_INVOCATION`, do not launch another worker: reconcile the existing child/worktree/artifact first. This is not blind result caching; implementation reuse is valid only when the recorded worktree/branch/artifact still proves the prior worker's output.

## Codex workers

Pass the concrete router-selected model and effort to `scripts/codex_worker.py`. The wrapper maps effort to Codex `model_reasoning_effort`, performs live capability preflight, optionally prunes unrelated MCPs, and writes metadata with route settings plus base/prompt/schema hashes, Codex version, active capabilities, dispatch/invocation/environment fingerprints, and memory policy. It keeps the normal Codex user/project configuration loaded by default so configured MCP servers and other capabilities remain available, while forcing Codex memory off for the worker with `features.memories=false`, `memories.use_memories=false`, `memories.generate_memories=false`, and `memories.dedicated_tools=false`. Together with `--ephemeral`, this makes each Codex worker cognitively stateless without amputating its configured tool layer. `--ignore-user-config` remains an explicit hard-isolation escape hatch, not the default. Some managed Codex configurations can override one-off config values; therefore requested effort is evidence of intent, not proof of effective runtime effort unless Codex exposes/records it.

If a configured Codex slot is unavailable, do not silently invoke Codex with its default model when `allow_codex_default_model: false`. In `hybrid`, fall back to the corresponding Claude route and record the fallback. In `codex-heavy`, block and request a valid model mapping.

## Token policy

Routing optimizes successful-work cost, not raw cheapness. A cheap model that fails twice is expensive, but an expensive model used for trivial work is also waste.

1. start at the predicted tier;
2. escalate **effort on Sol before model class** whenever reasonable;
3. if a worker fails because of reasoning/context rather than environment, replan or escalate one step;
4. never retry the same unchanged packet on the same model/effort more than once;
5. Astra requires the explicit gate above;
6. count every dispatch and model escalation against the run budget.
