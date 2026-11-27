# Model and effort routing

Gearbox treats model choice as part of the execution plan, not an invisible runtime accident. The hybrid policy deliberately uses a **small Gemini registry** and varies effort before reaching for a more expensive frontier model.

## Preflight

Before the first implementation worker is dispatched, resolve a model policy. If `.gearbox/config.md` already contains a policy, use it. If it does not, ask once and offer to persist the answer.

Recommended choices:

- `auto`: Gearbox chooses engine, model family and effort per task.
- `claude-heavy`: prefer Claude workers; Gemini is mainly a stateless second opinion.
- `hybrid`: choose Claude or Gemini per task. Recommended default.
- `gemini-heavy`: prefer stateless Gemini for bounded implementation, keep Claude for orchestration/integration/review.
- `custom`: user supplies allowed models and optional role constraints.

`--models ask` forces the preflight for this run. `--models auto|claude-heavy|hybrid|gemini-heavy` overrides the stored policy for this run. `--no-gemini` removes Gemini from the candidate set.

Do not ask repeatedly once a repository policy is stored unless the user requests it or configured models are unavailable.

## Unified specialist routing facade

Planner/control-plane code uses `scripts/route_task.py` for registered specialist task kinds. `orchestration-registry.json` is the canonical static model/effort registry; backend routers add dynamic capability/mode behavior.

Direct calls to the three backend routers remain supported for specialist skills and diagnostics, but new orchestration logic should not duplicate their model tables.

## Capability gate before model choice

Read `references/capability-routing.md`. Every task records `required_capabilities`, including an explicit empty list. Capability eligibility is a hard gate before risk/cost/model scoring: a provider that cannot supply a required external capability is not a candidate, however cheap or capable its model is.

Use `scripts/capabilities.py route` when the candidate capability sets are known. Gemini MCP availability comes from a sanitized setup snapshot for planning and a live `gemini mcp list --json` preflight immediately before dispatch. If exactly one provider satisfies the requirements, route there; if both do, continue with the normal risk/cost policy; if neither does, stop with `CAPABILITY_BLOCKED` instead of spending a worker to discover the missing tool.

For Gemini dispatches, pass every required MCP as `--required-capability <name>` and use `--prune-mcp` under the default `required-only` policy. The wrapper disables other configured MCP servers only for that invocation, while retaining the user's Gemini config and credentials. A task with `required_capabilities: []` therefore gets no MCP tool schemas unless the run explicitly overrides the policy.

## Forced game-asset specialist routes

Game-asset task kinds bypass the ordinary economy/risk router. Resolve them with `scripts/game_asset_router.py` before normal model routing:

| task kind | forced route | capability rule |
|---|---|---|
| `asset-image` | Gemini `gemini-4-neon-medium` / medium | direct model generation |
| `pixel-art` | Gemini `gemini-4-neon-medium` / medium | prefer live Aseprite MCP; direct Neon fallback |
| `model-3d` | Claude `claude-opus-5-5` / high directs; Gemini `gemini-4-carbon-high` / high executes | Blender/Godot required on Gemini; independent Carbon review |
| `motion-design` | Claude `claude-opus-5-5` / high directs; Gemini `gemini-4-carbon-high` / high for `--three-d`, otherwise Neon | 3D requires Blender/Godot on Gemini; non-3D may use other capabilities |
| `review-3d` | Gemini `gemini-4-carbon-high` / high, read-only | Blender or Godot must be available to Gemini |

These specialist identities bypass ordinary economy routing. For `model-3d` and `motion-design --three-d`, Opus remains the director/acceptance owner but Gemini Carbon/high is the mandatory substantive execution worker, with a live Gemini Blender/Godot capability. For non-3D motion, Neon remains eligible. This is a forced specialist route, not ordinary frontier escalation. Missing 3D capability on Gemini returns `GAME_ASSET_ROUTE_BLOCKED`, even when Claude has a tool. Run independent Carbon review for 3D assets.

A completed `model-3d` task always receives the dedicated `review-3d` Carbon gate before asset readiness. When the same task also changes product code, the normal code/task review policy still applies to that code; the 3D gate is additional.

## Web-design directed route

Material web-design tasks use `scripts/web_design_router.py` before ordinary implementation routing.

- direction: Claude Opus 5.5 / high;
- optional comp generation: Gemini Gemini 4 Neon orchestrating a configured GPT Image renderer; auto for surface/redesign when available;
- implementation: Gemini Gemini 4 Neon, medium by default and high for full redesign;
- rendered review: fresh Claude, Sonnet/high for refine/surface and Opus 5.5/high for full redesign.

Inspo is a preferred Claude-side evidence capability, not a requirement and never visual authority. Browser/Playwright-style tooling is preferred for implementation/review evidence. A material web-design task cannot reach visual PASS from source inspection alone; missing credible rendered evidence yields `BLOCKED` at the design-review gate.

The lane preserves provider separation: the director decides, Gemini may first generate design-system-grounded desktop/mobile comps, Gemini builds from the approved contract/comp, and a fresh Claude reviewer judges the rendered result including the anti-slop gate. Normal model economics do not downgrade the director or builder within this specialist lane.

## Creative-web route

`creative-web` composes the web-design lane with a harder interaction/creative-tech contract:

- direction: `creative-web-director`, Claude Opus 5.5 / high;
- optional comp generation: Gemini Gemini 4 Neon / high + configured GPT Image renderer;
- implementation: Gemini Gemini 4 Neon / high;
- review: fresh `creative-web-reviewer`, Claude Opus 5.5 / high.

The reviewer requires `SLOP_GATE`, `INTERACTION_GATE`, and `CREATIVE_GATE`. Creative mode does not grant permission to add WebGL, smooth-scroll libraries, custom cursors, shaders or animation dependencies without a product-grounded interaction thesis and fallback/performance plan.

Use `scripts/web_design_router.py --creative` for the deterministic route.

## Product/design quality specialist routes

Use `scripts/product_quality_router.py` for these task kinds before normal model economics:

| task kind | owner | bounded execution / review |
|---|---|---|
| `design-system` | Opus 5.5/high | Gemini Neon/medium apply; fresh Sonnet/high review |
| `a11y-audit` | Sonnet/high | Gemini Neon/medium repairs only after validated findings |
| `visual-regression` | Sonnet/high | read-only semantic adjudication |
| `content-design` | Sonnet/high | Gemini Neon/medium bounded copy/resource edits |
| `experience-perf` | Gemini Neon/high profiler | fresh Sonnet/high evidence review |
| `art-direction` | Opus 5.5/high | fresh Sonnet/high cross-asset review |
| `audio-design` | Opus 5.5/high | Gemini Neon/high tool wiring when capability exists |
| `level-design` | Opus 5.5/high | Gemini Neon/high blockout; fresh Opus/high playtest review |

These routes are role contracts, not excuses to bypass capability preflight or normal mutation ownership.

## Preferred Gemini registry

Use only three configured Gemini model slots by default (verified Gemini CLI identifiers: `gemini-4-hydrogen-low`, `gemini-4-neon-medium`, `gemini-4-carbon-high`):

```yaml
gemini_models:
  economy: gemini-4-hydrogen-low
  standard: gemini-4-neon-medium
  frontier: gemini-4-carbon-high
allow_gemini_default_model: false
gemini_frontier_policy: escalation-or-exceptional
```

Treat the exact strings as repository configuration. If the local Gemini installation exposes different IDs for Hydrogen, Neon, or Carbon, persist those exact IDs during `/setup`.

The intentional mapping is:

- **Gemini 4 Hydrogen**: documentation, changelog, formatting, metadata, fixtures, generated mappings, renames, obvious wiring, isolated deterministic test work.
- **Gemini 4 Neon**: the normal Gemini engineering model. Use `medium` effort for ordinary features/bugs and `high` for deep debugging, migrations, persistence invariants, concurrency, auth/security or broad changes.
- **Gemini 4 Carbon**: frontier escalation only. It is not a normal `high risk` model and must not be selected merely because a task touches a database or security-sensitive area.


## Per-task route

Every executable DAG node must record:

```yaml
execution:
  engine: claude | gemini | orchestrator
  role: implementation | research | review | simplify | verify
  model_class: economy | standard | frontier
  model: sonnet | opus | haiku | <configured full model id>
  effort: low | medium | high | xhigh | max | auto
  rationale: one short sentence
```

Choose the cheapest route that can safely satisfy the task.

### Gemini deterministic router

For Gemini candidates, use `scripts/model_router.py` rather than selecting a model ad hoc. Feed it the task kind, risk, ambiguity, breadth, verification strength and prior failed attempts.

Example:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/model_router.py" \
  --task-kind feature \
  --risk medium \
  --ambiguity low \
  --breadth moderate \
  --verification strong \
  --luna-model "<configured Hydrogen id>" \
  --sol-model "<configured Neon id>" \
  --astra-model "<configured Carbon id>" \
  --json
```

The router uses four reasoning tiers but only three models:

- **bounded** → Hydrogen/low (occasionally Hydrogen/medium when the deliverable itself is cheap but risk metadata is noisy);
- **normal** → Neon/medium;
- **deep** → Neon/high;
- **exceptional** → Carbon/medium first, Carbon/high only when further escalation is justified.

### Hard ceilings

These task kinds are hard-capped to Hydrogen-class execution even if a noisy classifier marks them critical: docs, changelog, formatting, metadata, fixtures, generated mappings, simple renames/wiring and isolated simple tests.

If the work contains a hard architecture decision plus documentation, split it into two tasks:

1. architecture/domain decision → Claude or Neon/high as appropriate;
2. writing the already-decided documentation → Hydrogen/low.

This prevents frontier compute from being spent on prose generation.

### Carbon gate

Carbon is allowed only when one of these is true:

1. an explicit frontier override was requested for this task;
2. a frontier-eligible deep task has already failed at least twice for reasoning/context reasons and remains difficult after replanning/escalation;
3. the task is simultaneously critical, highly ambiguous, broad, weakly verifiable, and belongs to a frontier-eligible class such as deep debugging, migration, auth/security, concurrency, persistence, architecture, or high-risk adjudication.

Ordinary high-risk work stays on Neon/high first. A failed environment/tool invocation is not a reasoning failure and does not justify Carbon.

## Hybrid cross-provider review routing

When `model_policy: hybrid`, every executable implementation task gets a fresh **opposite-provider task review before integration**. Provider diversity is the invariant:

- implementation by **Claude/Anthropic** → review by **Gemini/OpenAI**;
- implementation by **Gemini/OpenAI** → review by **Claude/Anthropic**.

The reviewer never receives the implementation conversation or another reviewer's conclusions. It receives only the task packet, task acceptance slice, base/head refs or diff path, changed paths, and focused verification evidence.

Resolve the reviewer route with `scripts/review_router.py`, using the implementation task's already-selected tier and risk. Persist the result beside the implementation route in `dag.yaml`:

```yaml
execution:
  engine: gemini
  model: gemini-4-neon-medium
  effort: medium
review:
  engine: claude
  model: sonnet
  effort: medium
  agent: task-reviewer
  rationale: opposite-provider review for normal Gemini work
```

Example router calls:

```bash
# Claude implementation -> Gemini reviewer
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_router.py" \
  --implementation-engine claude \
  --task-tier normal \
  --risk medium \
  --json

# Gemini implementation -> Claude reviewer
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/review_router.py" \
  --implementation-engine gemini \
  --task-tier deep \
  --risk high \
  --json
```

Default opposite-provider mapping:

| implementation | task tier | independent reviewer |
|---|---|---|
| Claude | bounded | Gemini Hydrogen / low |
| Claude | normal | Gemini Neon / medium |
| Claude | deep | Gemini Neon / high |
| Claude | exceptional | Gemini Carbon / medium, high only when justified |
| Gemini | bounded | Claude Haiku / low |
| Gemini | normal | Claude Sonnet / medium |
| Gemini | deep | Claude Opus / high |
| Gemini | exceptional | Claude Opus / xhigh |

This routing is deliberately asymmetric with cost: a trivial Claude-authored README task is reviewed by Hydrogen/low, not Carbon; a bounded Gemini task is reviewed by Haiku/low, not Opus. Provider diversity does not mean paying frontier prices for every diff.

A task is not integration-ready until its opposite-provider review has a passing SPEC verdict and no validated blocking QUALITY finding. The orchestrator adjudicates findings against code/tests/spec; reviewers do not command fixes blindly.

If the opposite provider is unavailable, do **not** silently substitute a same-provider reviewer in hybrid mode. Mark the task review `BLOCKED` or request an explicit policy override. `--no-gemini` is such an explicit override and disables this cross-provider invariant for that run.

For non-hybrid policies (`claude-heavy`, `gemini-heavy`, `auto` when it resolves to a single provider), use the configured adaptive review behavior unless an explicit cross-provider lens is available.

## Claude routing

Use these dimensions: requirement ambiguity, architectural breadth, trust/data risk, debugging novelty, number of seams touched, and strength of deterministic verification.

- **Tier 1 / bounded**: mechanical edits, obvious wiring, generated mappings, isolated tests. Prefer Haiku/low.
- **Tier 2 / normal**: ordinary feature work, bugs, tests, moderate multi-file changes with clear contracts. Prefer Sonnet/medium.
- **Tier 3 / deep**: architecture, subtle debugging, migrations, auth/security, concurrency, persistence invariants, broad refactors, ambiguous cross-cutting behavior. Prefer Opus/high when Claude owns the task.
- **Tier 4 / exceptional**: use xhigh/max sparingly only when evidence shows it is justified.

Gemini is preferred for a bounded packet with explicit ownership and strong tests. Claude is preferred when the task needs domain interpretation, cross-task context, architectural judgment, or interactive tool use that depends on the parent plan.

## Claude subagents

Gearbox ships worker agents with fixed effort tiers (`worker-low`, `worker-medium`, `worker-high`, `worker-xhigh`). Their `model` is `inherit`; when Claude Code supports a per-dispatch model override, dispatch the chosen model while selecting the agent whose frontmatter effort matches the route. If a requested model is unavailable, fall back to the closest allowed family and record the fallback in run state.

Claude task reviewers have effort-specific profiles (`task-reviewer-low`, `task-reviewer`, `task-reviewer-high`, `task-reviewer-xhigh`) so Gemini-authored work can be reviewed at the matching risk tier. Ponytail simplification stays medium and final cross-review stays high unless risk justifies more.

Record the requested route and, when runtime tooling exposes it, the observed route. Never claim an effort was actually used if it cannot be observed.

## Dispatch fingerprint and deduplication

Before any long-lived/background worker dispatch, compute a stable fingerprint from the exact base SHA, task packet/prompt, provider, model, effort, kind and required capability set with `scripts/invocation_fingerprint.py`. Register it in `children.json`. If `scripts/child_jobs.py register --fingerprint ...` reports `DUPLICATE_INVOCATION`, do not launch another worker: reconcile the existing child/worktree/artifact first. This is not blind result caching; implementation reuse is valid only when the recorded worktree/branch/artifact still proves the prior worker's output.

## Gemini workers

Pass the concrete router-selected model and effort to `scripts/gemini_worker.py`. The wrapper maps effort to Gemini `model_reasoning_effort`, performs live capability preflight, optionally prunes unrelated MCPs, and writes metadata with route settings plus base/prompt/schema hashes, Gemini version, active capabilities, dispatch/invocation/environment fingerprints, and memory policy. It keeps the normal Gemini user/project configuration loaded by default so configured MCP servers and other capabilities remain available, while forcing Gemini memory off for the worker with `features.memories=false`, `memories.use_memories=false`, `memories.generate_memories=false`, and `memories.dedicated_tools=false`. Together with `--ephemeral`, this makes each Gemini worker cognitively stateless without amputating its configured tool layer. `--ignore-user-config` remains an explicit hard-isolation escape hatch, not the default. Some managed Gemini configurations can override one-off config values; therefore requested effort is evidence of intent, not proof of effective runtime effort unless Gemini exposes/records it.

If a configured Gemini slot is unavailable, do not silently invoke Gemini with its default model when `allow_gemini_default_model: false`. In `hybrid`, fall back to the corresponding Claude route and record the fallback. In `gemini-heavy`, block and request a valid model mapping.

## Telemetry economic tie-breaker

For **unregistered generic tasks only**, after capability/risk/model-policy eligibility is known, Gearbox may query `scripts/routing_advisor.py` for repeated measured history of the same task kind.

The advisor is never an authority over safety:

- specialist routes remain pinned;
- security/persistence/public-contract/production-config surfaces stay observe-only;
- insufficient samples yield no recommendation;
- telemetry cannot promote work to Carbon/frontier;
- the user/model policy remains the candidate ceiling.

Use advice only as an economic tie-breaker among already-safe candidates.

## Token policy

Routing optimizes successful-work cost, not raw cheapness. A cheap model that fails twice is expensive, but an expensive model used for trivial work is also waste.

1. start at the predicted tier;
2. escalate **effort on Neon before model class** whenever reasonable;
3. if a worker fails because of reasoning/context rather than environment, replan or escalate one step;
4. never retry the same unchanged packet on the same model/effort more than once;
5. Carbon requires the explicit gate above;
6. count every dispatch and model escalation against the run budget.
