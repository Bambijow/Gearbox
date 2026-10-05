# Pull request reporting contract

Gearbox uses two layers so a PR is understandable to both non-technical stakeholders and engineers.

## Main PR description

Write this for someone who understands the product/problem but does not need to know the implementation.

Use this shape:

```markdown
## Summary
<2-5 lines: problem + observable result>

<optional smallest useful visual: pseudocode, call tree, shallow file/component tree, Mermaid, or diff-sketch>

## What changes
<observable behavior and who benefits>

## What does not change
<important scope boundary>

## Evidence
**Before:** <failing scenario/output/screenshot or verified old behavior>
**After:** <passing scenario/output/screenshot or verified new behavior>

## Merge Danger
**Door:** <one-way|two-way>
**Blast Radius:** <short scope label>
<one or two lines explaining rollback/irreversibility and plausible affected surface>

## Rollout / caveats
<only when needed>

Closes #123
```

The visual is optional. Use one only when it makes the shape of the change easier to understand than prose. Pick the smallest representation that makes the key point clear; do not dump implementation detail into the stakeholder description.

**Door**:

- `two-way`: cheap/safe to revert without irreversible state loss;
- `one-way`: destructive migration, irreversible external side effect, contract/state transition, or other decision that cannot be cheaply walked back.

**Blast Radius** describes what could be affected if the change is wrong: one form, one endpoint, all consumers of an API, persisted data, auth flows, etc.

Before creating/updating the PR, write this body to `.gearbox/runs/<run-id>/pr-body.md` and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pr_body_guard.py" \
  --body ".gearbox/runs/<run-id>/pr-body.md"
```

A failed body guard blocks publication. Do not invent “before” evidence that was never observed; say `not captured` with the reason when the old state cannot be reproduced.

## First technical comment

Start with the hidden marker `<!-- gearbox-report:v1 -->` so later `/continue-pr` runs update the same report instead of spamming comments. Build verification/review claims from `evidence.json` and run state. Both PR body and technical report are potentially public: apply `references/secret-redaction.md`; guards reject obvious secret-like material.

This is the engineer's control panel, not a prose recap of filenames.

Recommended shape:

````markdown
<!-- gearbox-report:v1 -->

## Implementation map
- <component/path>: <why it changed>

## Critical logic to inspect
<!-- gearbox-critical-code:start -->
### `src/example.ts:84-101`
```ts
<exact source lines 84 through 101 from the final PR head>
```
**Why this matters:** <behavior/invariant/risk controlled by these lines>
**Review focus:** <specific thing a human reviewer should verify>
<!-- gearbox-critical-code:end -->

## Verification
- `command` ✅
- manual scenario ✅

## Simplification pass
- removed ...
- reused ...

## Engineering loop
- cycles: ...
- repaired gates: ...

## Independent review
- fixed: ...
- residual risk: ...

## Durable learning
- `docs/solutions/...` or `none`

## UI / UX evidence
![state](./local-screenshot.png)

## Dogfood (when run)
- persona/journey: ...
- functional blockers: ...
- UX friction/polish: ...
- console/network/a11y observations: ...
````

### Critical-code rule

For any PR containing substantive product code, configuration, schema, query, migration, or runtime-behavior changes, the technical comment MUST include 1 to 5 actual source-backed excerpts. A filename bullet, a prose summary, a symbol name, or a `path:line` pointer without visible code does **not** satisfy this requirement.

Each excerpt MUST:

- show the exact final source text, not pseudocode or a paraphrase;
- use a heading exactly shaped as ``### `<path>:<start>-<end>` ``;
- be 30 lines or fewer;
- explain `Why this matters` in behavior/invariant/risk terms;
- give a concrete `Review focus`;
- prefer the smallest excerpt that exposes the important decision;
- come from the final PR head after Ponytail and repair cycles, not an intermediate diff.

Keep the total critical-code excerpt budget at 120 lines or less. Usually 2 to 4 excerpts is ideal. Do not dump entire files or large generated blocks.

If the change genuinely contains no critical product code (for example, documentation-only metadata), emit `<!-- gearbox-critical-code:none -->` and explain that there is no runtime logic to inspect. Do not use the `none` marker for a PR that changes runtime behavior.

Before posting/updating the technical comment, write it to the run directory as `pr-technical-report.md` and run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/pr_report_guard.py" \
  --report ".gearbox/runs/<run-id>/pr-technical-report.md" \
  --repo-root . \
  --require-code
```

Use `--require-code` whenever the intended diff contains substantive code/config/schema/migration/runtime changes. A failed guard is `SHIP_REPORT_INCOMPLETE`: do not post the comment; regenerate it with real excerpts and validate again.

When creating the comment with GitHub CLI attachment support, reference local image paths in the Markdown and pass the same paths with `--attach`; GitHub rewrites those references to uploaded assets.
