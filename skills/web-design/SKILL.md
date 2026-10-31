---
name: web-design
description: "Design, redesign, or materially refine production web surfaces with an Opus 5.5 design director, optional Codex-driven high-fidelity comp generation from the design system, Codex GPT-6.1 Sol implementation, anti-AI-slop gates, responsive/accessibility constraints, and bounded rendered review."
argument-hint: "[brief/surface] [--scope refine|surface|redesign] [--comp auto|require|skip] [--apply]"
---

# Directed web design with anti-slop and optional visual comps

Read `references/web-design-contract.md`, `references/web-design-inspiration.md`, `references/web-design-anti-slop.md`, `references/component-interaction.md`, `references/design-system-lifecycle.md`, `references/content-design.md`, `references/accessibility-audit.md`, `references/semantic-visual-regression.md`, `references/experience-probe.md`, `references/orchestration-compilation.md`, `references/web-design-comp-generation.md`, and `references/web-design-review.md`.

Resolve the lane with `scripts/web_design_router.py`. Opus 5.5/high owns visual direction and ambiguous design decisions. Codex GPT-6.1 Sol owns optional comp generation and final implementation. A fresh Claude reviewer judges rendered output.

First classify the surface mode: `Persuade`, `Operate`, `Read`, or `Experience`. Then classify scope:

- `refine`: preserve the incumbent visual world and behavior;
- `surface`: create a substantial new surface inside an existing visual world;
- `redesign`: replace the visual world only when explicitly authorized.

A local spacing, copy, component, accessibility, or bug fix MUST NOT become a redesign.

Before implementation, `web-design-director` produces the design contract. For `surface`/`redesign`, it MUST also declare the category rut, at least two product-grounded departures, one product-shaped signature device, and explicit slop risks. Generic SaaS composition is not a valid undecided default.

When Inspo is available, use it as evidence: a small set of exemplars, comparisons and design-system details that sharpen the direction. Never clone a captured site or let category consensus replace judgment.

Comp policy:

- `auto`: generate coordinated desktop/mobile comps for `surface` and `redesign` when an image-generation path is available; skip ordinary `refine`;
- `require`: comp generation is mandatory or return `WEB_COMP_BLOCKED`;
- `skip`: use the code-led path.

The comp pass is owned by Codex Sol. It distills the approved design system/contract, then orchestrates a configured GPT Image renderer. Opus approves the pair before implementation. Exact product truth, copy, accessibility and behavior always outrank raster contents.

If the approved brief explicitly requires a rendered marketing/hero video, schedule `video-create` with its mandatory `asset-image` prerequisite when no approved reference still exists. Treat video output as an asset dependency; do not substitute native UI animation or incur fal.ai charges without model/budget approval. See `references/video-production.md`.

Without `--apply`, stop after the approved design contract and, when enabled, approved comps.

With `--apply`, dispatch `web-builder-dispatcher`. The builder may derive idiomatic implementation details but may not invent a new visual direction or fill gaps with generic AI/SaaS defaults. It must run the anti-slop self-check before handoff.

Material components with non-trivial state/focus/async/gesture behavior require the interaction contract from `references/component-interaction.md`; use `interaction-designer` when ambiguous. For shared primitives or visible design drift, invoke the design-system gate. Substantial new UX copy/state copy invokes the content-design gate. Material motion reuses `motion-design`.

Render once through the compiled shared `experience` probe when multiple UI gates need the same journey; independent reviewers reuse that immutable bundle. A meaningful web-design task cannot claim PASS without real rendered evidence, `SLOP_GATE: PASS`, `INTERACTION_GATE: PASS|NOT_APPLICABLE`, and `A11Y_GATE: PASS`. When an approved visual baseline exists, also require `VISUAL_REGRESSION_GATE: PASS`; when substantial copy changed, require `CONTENT_GATE: PASS`. Use one batched desktop+mobile review, one repair batch, and at most one confirmation review. Stop ordinary polish after that bounded cycle unless a blocker remains.

For user-facing flows, run the relevant dogfood journey after visual review when browser/E2E tooling is available.
