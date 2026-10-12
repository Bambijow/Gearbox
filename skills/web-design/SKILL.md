---
name: web-design
description: "Design, redesign, or materially refine production web surfaces with an Opus 5.5 design director, optional Codex-driven high-fidelity comp generation from the design system, Codex GPT-6.1 Sol implementation, anti-AI-slop gates, responsive/accessibility constraints, and bounded rendered review."
argument-hint: "[brief/surface] [--scope refine|surface|redesign] [--comp auto|require|skip] [--apply]"
disable-model-invocation: true
---

# Directed web design with anti-slop and optional visual comps

Read `references/web-design-contract.md`, `references/web-design-inspiration.md`, `references/web-design-anti-slop.md`, `references/web-design-comp-generation.md`, and `references/web-design-review.md`.

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

Without `--apply`, stop after the approved design contract and, when enabled, approved comps.

With `--apply`, dispatch `web-builder-dispatcher`. The builder may derive idiomatic implementation details but may not invent a new visual direction or fill gaps with generic AI/SaaS defaults. It must run the anti-slop self-check before handoff.

Material motion should reuse the existing `motion-design` lane.

Render and inspect the result. A meaningful web-design task cannot claim visual PASS without real rendered evidence and `SLOP_GATE: PASS`. Use one batched desktop+mobile review, one repair batch, and at most one confirmation review. Stop ordinary polish after that bounded cycle unless a blocker remains.

For user-facing flows, run the relevant dogfood journey after visual review when browser/E2E tooling is available.
