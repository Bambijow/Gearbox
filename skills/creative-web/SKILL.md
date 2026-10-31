---
name: creative-web
description: "Create high-craft interactive web experiences where motion, interaction, typography, spatial composition, canvas/WebGL, or narrative behavior are part of the product. Uses Opus 5.5 creative direction, optional Inspo/comp generation, Codex GPT-6.1 Sol implementation, explicit interaction contracts, anti-slop/anti-gimmick gates, performance fallbacks, and fresh rendered review."
argument-hint: "[brief/experience] [--comp auto|require|skip] [--apply]"
---

# Creative web as interaction-led production

Read `references/web-design-contract.md`, `references/web-design-anti-slop.md`, `references/component-interaction.md`, `references/accessibility-audit.md`, `references/experience-performance.md`, `references/semantic-visual-regression.md`, `references/experience-probe.md`, `references/orchestration-compilation.md`, `references/creative-web-workflow.md`, `references/web-design-comp-generation.md`, and `references/web-design-review.md`.

Use this lane only when interaction/motion/spatial behavior is part of the requested experience, not merely because a page should look premium.

The `creative-web-director` (Opus 5.5/high) owns the interaction thesis, art direction, scene/state architecture, creative-tech choice, motion hierarchy, fallback strategy and acceptance. It may use Inspo as evidence, never as a template and never to imitate a specific creator.

Reuse the web-design comp pipeline when useful. Visual comps establish composition/material/hierarchy; they cannot specify time. The director must also produce an interaction storyboard/state graph for the key moments.

Every material component/scene needs the applicable interaction contract: states, triggers, focus, interruption/reversal, pointer/touch/keyboard semantics, latency feedback, motion role and reduced-motion behavior.

Choose the least complex rendering stack that expresses the interaction thesis. DOM/CSS/SVG come before Canvas/WebGL unless the experience truly needs continuous pixels, spatial depth, custom rendering or shader behavior.

If the approved brief explicitly requires a rendered marketing/hero video, schedule `video-create` with its mandatory `asset-image` prerequisite when no approved reference still exists. Treat video output as an asset dependency; do not substitute native UI animation or incur fal.ai charges without model/budget approval. See `references/video-production.md`.

Without `--apply`, stop after the creative direction, interaction architecture, comp/storyboard and implementation plan.

With `--apply`, Codex GPT-6.1 Sol/high implements the approved experience. Use the repository's existing motion/render stack where capable; do not add Three.js/GSAP/Lenis/etc. by habit.

Collect the representative runtime journey once through the compiled shared experience probe; A11Y/PERF/interaction/visual/creative reviewers consume the same bundle at their required depth. The final fresh reviewer must pass:

```text
SLOP_GATE
INTERACTION_GATE
A11Y_GATE
PERF_GATE
VISUAL_REGRESSION_GATE (when baseline exists)
CREATIVE_GATE
VERDICT
```

Performance, reduced-motion, keyboard/touch alternatives and WebGL/canvas fallback are part of correctness, not optional polish. Run `experience-perf` on measured expensive paths and `a11y-audit` before final PASS.
