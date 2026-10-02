# Pull request reporting contract

Gearbox uses two layers so a PR is understandable to both non-technical stakeholders and engineers.

## Main PR description

Write this for someone who understands the product/problem but not the code.

Recommended shape:

```markdown
## Why this change
<plain-language problem>

## What changes
<observable behavior and who benefits>

## What does not change
<important scope boundary>

## Confidence
<plain-language verification, including UI/manual evidence if relevant>

## Rollout / caveats
<only when needed>

Closes #123
```

Do not dump file names or internal implementation terminology into this section unless a stakeholder truly needs it.

## First technical comment

Start with the hidden marker `<!-- gearbox-report:v1 -->` so later `/continue-pr` runs update the same report instead of spamming comments. Build verification/review claims from `evidence.json` and run state.

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
