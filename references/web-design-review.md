# Web design review

Review rendered output, not only source code.

## Fresh reviewer packet

The reviewer receives:

- approved design contract;
- approved desktop/mobile comps when comp-led;
- target routes/states;
- desktop and mobile/narrow captures from the same build;
- relevant interaction/runtime evidence;
- changed UI paths;
- intentionally deferred states.

Judge against the contract and user job, not personal taste.

## AI-slop gate

Read `references/web-design-anti-slop.md` and return:

```text
SLOP_GATE: PASS | REPAIR
```

A technically clean render still needs `REPAIR` when it visibly falls back to unearned model defaults. A listed pattern is not automatically wrong; flag it only when unsupported by the brief, incumbent system, content structure, or approved contract.

Visual `PASS` requires `SLOP_GATE: PASS`.

## Interaction gate

Read `references/component-interaction.md` and return:

```text
INTERACTION_GATE: PASS | REPAIR | NOT_APPLICABLE
```

For material interactive components, exercise state transitions with the relevant pointer, keyboard and touch paths. Check immediate feedback, focus entry/restoration, loading/success/error, interruption/reversal, rapid repeated input, reduced motion and layout stability.

A transition property existing in source is not proof of good interaction. Motion must follow state semantics and must not delay the real action.

## Comp fidelity

When an approved comp exists, compare the implementation to both contract and comp.

The comp governs composition, hierarchy, material treatment and visual rhythm. Do not demand pixel identity when real content, browser behavior, responsive logic or accessibility requires adaptation. Product truth and contract outrank generated raster text/details.

## Review layers

### Product and hierarchy
- primary job/action is obvious;
- hierarchy matches importance;
- grouping supports the mode;
- product meaning is unchanged.

### Visual system
- typography roles are coherent;
- spacing/density/radii/materials form a system;
- color roles and contrast are intentional;
- refine/surface work belongs to the incumbent system;
- redesign is coherent rather than half-old/half-new.

### Responsive and states
Inspect desktop and mobile/narrow together. Check overflow, nav collapse, reordering, touch/focus states, empty/loading/error/disabled states, long content and zoom/reflow risks.

### Accessibility
Check obvious contrast, keyboard/focus, labels/names, landmarks/semantics where tooling exposes them, reduced motion and perceivable status/errors.

### Motion and polish
Motion should explain hierarchy, causality or spatial relationship. Flag gratuitous repetition, jank and missing reduced-motion behavior.

## Specialist quality gates

For material user-facing web work, final orchestration may additionally require:

- `A11Y_GATE: PASS` from `a11y-audit`;
- `CONTENT_GATE: PASS` when substantial UX copy/state copy changed;
- `DESIGN_SYSTEM_GATE` when shared primitives/tokens were added or drift was reconciled;
- `VISUAL_REGRESSION_GATE: PASS` when an approved visual baseline exists;
- `PERF_GATE: PASS` for performance-sensitive or creative/heavy experiences.

Do not duplicate these specialist audits inside this reviewer when their dedicated evidence exists.

## Bounded finish loop

1. capture desktop + mobile/narrow;
2. collect all validated findings in one batch;
3. repair the batch;
4. capture once more to confirm;
5. stop ordinary polish.

Do not run endless screenshot/tiny-edit loops.

## Verdict

Return `SLOP_GATE`, then `INTERACTION_GATE`, then:

- `PASS`: contract met, SLOP_GATE passes, INTERACTION_GATE passes or is not applicable, and no material defect remains;
- `REPAIR`: concrete contract/comp/responsive/accessibility/runtime defects remain;
- `BLOCKED`: rendered evidence is unavailable or a missing decision prevents fair judgment.

A material web-design task cannot claim visual PASS from source inspection alone.
