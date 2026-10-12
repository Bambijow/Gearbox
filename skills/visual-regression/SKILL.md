---
name: visual-regression
description: "Compare current UI renders against approved baselines semantically, separating intended change, real regression, ambiguity, and rendering noise. Use after material UI changes or when maintaining visual baselines without freezing the product to pixel identity."
argument-hint: "[route/surface/baseline] [--record]"
disable-model-invocation: true
---

# Semantic visual regression

Read `references/semantic-visual-regression.md`, the approved design contract, and repository visual-test conventions.

Use `scripts/product_quality_router.py --task-kind visual-regression`.

The `visual-regression-reviewer` compares baseline/current captures under equivalent viewport/theme/state conditions. Pixel-diff output is supporting evidence, never the verdict.

Classify changed regions as `INTENDED`, `REGRESSION`, `AMBIGUOUS`, or `NOISE`. Return `VISUAL_REGRESSION_GATE: PASS|REPAIR|BLOCKED`.

With `--record`, update a durable baseline only when the change is approved, capture conditions are reproducible, relevant design/a11y gates pass, and unrelated drift is absent. Reuse repository-native baseline storage; do not invent a committed baseline directory silently.

If capture conditions differ materially, block instead of manufacturing certainty.
