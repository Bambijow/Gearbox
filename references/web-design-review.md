# Web design review

Review rendered output, not only source code.

## Fresh reviewer

The reviewer did not direct or implement the design. It receives:

- approved design contract;
- target routes/states;
- desktop and mobile/narrow captures from the same build;
- relevant interaction/runtime evidence;
- changed UI paths;
- any intentionally deferred states.

Judge the artifact against the contract and user job, not personal taste.

## Review layers

### Product and hierarchy

- primary job/action is obvious at intended viewing size;
- visual hierarchy matches importance;
- copy/content grouping supports the mode;
- the result does not accidentally change product meaning.

### Visual system

- typography roles are coherent;
- spacing/density/radii/materials are systematic rather than random;
- color roles and contrast are intentional;
- new work belongs to the existing system for refine/surface scopes;
- redesign scope is internally coherent and fully committed rather than half-old/half-new.

### Responsive and states

Inspect desktop and mobile/narrow in the same review pass. Check major intermediate behavior when the layout has a known risk.

Verify relevant:

- overflow/clipping;
- navigation collapse;
- content reordering;
- touch target/focus states;
- empty/loading/error/disabled states;
- long content / i18n-sensitive regions;
- zoom/reflow-sensitive areas.

### Accessibility

Check obvious color contrast, keyboard/focus behavior, names/labels, landmarks/semantics where visible to tooling, reduced motion, and whether error/status information is perceivable. Specialized accessibility tooling remains stronger evidence when available.

### Motion and polish

Motion should explain change, hierarchy or causality. Flag gratuitous animation, competing motion, bad easing, jank and missing reduced-motion behavior.

Polish findings must have a concrete visual consequence. Do not manufacture pixel-level churn once the quality bar is met.

## Bounded finish loop

One finish cycle means:

1. capture desktop + mobile/narrow and inspect them together;
2. collect all validated findings in one batch;
3. repair the batch;
4. capture once more to confirm;
5. stop.

Do not run endless screenshot -> tiny edit -> screenshot loops. A blocker discovered in confirmation may re-enter normal repair, but ordinary polish does not reopen the finish cycle.

## Verdict

Use:

- `PASS`: contract met; no material visual/UX defect remains;
- `REPAIR`: concrete contract/responsive/accessibility/runtime defects remain;
- `BLOCKED`: rendered evidence is unavailable or a missing product/design decision prevents fair judgment.

A meaningful web-design task cannot claim visual PASS from static code inspection alone.
