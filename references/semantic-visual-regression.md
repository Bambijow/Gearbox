# Semantic visual regression

Pixel difference is evidence of change, not evidence of regression.

Compare the current render against an approved baseline, design contract and product state.

## Inputs

Prefer:

- exact baseline viewport/theme/state;
- current render from same conditions;
- design contract / design-system authority;
- intended-change description;
- DOM/state metadata when available;
- pixel-diff output as supporting evidence, never sole judge.

If capture conditions differ materially, return `AMBIGUOUS` rather than inventing certainty.

## Classify changed regions

- `INTENDED`: directly explained by approved change and still satisfies the design contract.
- `REGRESSION`: unintended loss in layout, hierarchy, typography, state, overflow, responsiveness, accessibility or design-system coherence.
- `AMBIGUOUS`: cannot determine intent or capture equivalence safely.
- `NOISE`: antialiasing, font rasterization, sub-pixel/video/time-dependent variation with no meaningful visual consequence.

Do not approve a regression because the new screenshot is aesthetically pleasing.

## Semantic checks

Look for:

- disappearance/obscuring of important content/action;
- unexpected wrapping, clipping or layout shift;
- hierarchy inversion;
- token/component drift;
- broken responsive composition;
- missing interaction/focus/error state;
- changed copy causing visual/meaning regressions;
- theme mismatch;
- motion-state capture taken at the wrong moment;
- baseline that itself conflicts with newer approved design truth.

## Baseline lifecycle

A baseline updates only when:

1. the change is approved/intended;
2. target state/viewport/theme is reproducible;
3. relevant design/a11y gates pass;
4. the new baseline does not smuggle unrelated drift.

Reuse repository-native visual regression tooling. If none exists, one-off comparison remains run-local unless the user explicitly requests a durable baseline location.

## Gate

Return:

```text
VISUAL_REGRESSION_GATE: PASS | REPAIR | BLOCKED
classification:
- <region>: INTENDED|REGRESSION|AMBIGUOUS|NOISE
```

PASS means no material unexplained regression remains.
