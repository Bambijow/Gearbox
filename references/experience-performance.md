# Experience performance gate

Performance is part of interaction quality. Measure the path users experience, not only bundle size.

## Establish budget

Before profiling expensive UI/creative work, record:

- target device/network class;
- critical journey/scene;
- response/frame-rate expectations;
- asset/texture/video constraints;
- known repository performance budgets.

If no numeric budget exists, report measurements and regressions without inventing universal thresholds.

## Web product surfaces

Measure applicable:

- navigation/load responsiveness;
- LCP/INP/CLS or repository-native web vitals;
- long main-thread tasks;
- hydration/render churn;
- layout shifts;
- image/font loading;
- duplicated requests;
- large client dependencies.

## Creative / motion surfaces

Also inspect:

- frame pacing during the critical scene;
- event/input latency;
- requestAnimationFrame work;
- shader/postprocess cost;
- canvas/WebGL draw behavior;
- texture count/resolution/memory;
- DPR/resize cost;
- video decode/asset loading;
- scene/resource disposal;
- mobile thermal/fidelity behavior where practical.

Do not claim 60fps from source code or one powerful desktop.

## Profiling discipline

1. reproduce the same path/state;
2. capture a bounded trace/profile;
3. identify the dominant bottleneck;
4. repair the smallest cause;
5. remeasure once;
6. stop when the budget is met or the next trade-off needs product/design judgment.

Do not micro-optimize code that is absent from the measured hot path.

## Graceful degradation

Prefer preserving content/task success while reducing expensive fidelity:

- lower DPR;
- smaller textures;
- fewer postprocess passes;
- static/DOM fallback;
- reduced-motion mode;
- lazy scene activation.

## Gate

Return:

```text
PERF_GATE: PASS | REPAIR | BLOCKED
```

Include measured evidence, environment, path and remaining uncertainty.
