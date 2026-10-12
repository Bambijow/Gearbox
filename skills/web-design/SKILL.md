---
name: web-design
description: "Design, redesign, or materially refine production web surfaces with an Opus 5.5 design director, Codex GPT-6.1 Sol implementation, optional Inspo evidence, responsive/accessibility constraints, and bounded rendered review. Use for landing pages, dashboards, product UI, app shells, docs, portfolios, pricing, onboarding, and design-system-level UI work."
argument-hint: "[brief/surface] [--scope refine|surface|redesign] [--apply]"
disable-model-invocation: true
---

# Web design as a directed production lane

Read `references/web-design-contract.md`, `references/web-design-inspiration.md`, and `references/web-design-review.md`.

Resolve the lane with `scripts/web_design_router.py`. Opus 5.5/high owns visual direction and ambiguous design decisions. Codex GPT-6.1 Sol implements the approved contract. A fresh Claude reviewer judges rendered output.

First classify the surface mode: `Persuade`, `Operate`, `Read`, or `Experience`. Then classify scope:

- `refine`: preserve the incumbent visual world and behavior; fix only the requested surface;
- `surface`: create a substantial new surface inside an existing visual world;
- `redesign`: replace the visual world only when the request explicitly authorizes it.

A local spacing, copy, component, accessibility, or bug fix MUST NOT become a redesign.

Before implementation, the `web-design-director` produces a compact design contract: product/user job, visual authority, mode/scope, hierarchy, typography, palette/tokens, macrostructure, responsive behavior, interaction states, motion grammar, accessibility constraints, evidence references, anti-references, and intentional departures.

When Inspo is available, use it as visual evidence. Prefer a small evidence packet: `recommend` or search, 2-4 exemplars, `compare` when useful, and `get_design_system` only for references actually being studied. Extract principles and contrasts; never clone a captured site or let category consensus replace judgment.

Without `--apply`, stop after the approved design contract and implementation plan.

With `--apply`, dispatch `web-builder-dispatcher` to run the bounded Codex Sol build. The builder may derive implementation details but may not invent a new visual direction. Material motion should reuse the existing `motion-design` lane rather than ad-hoc animation.

Render and inspect the result. A meaningful web-design task cannot claim visual PASS without real rendered evidence. Use one batched desktop+mobile review, apply the reviewer's findings in one repair batch, then perform at most one confirmation review. Stop polishing after that bounded cycle unless a blocker remains.

For user-facing flows, run the relevant dogfood journey after visual review when browser/E2E tooling is available.
