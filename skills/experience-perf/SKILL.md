---
name: experience-perf
description: "Profile and improve real user-experience performance for web/product/creative surfaces using measured browser/runtime evidence. Covers web vitals, input latency, long tasks, image/font loading, frame pacing, canvas/WebGL cost, textures, DPR, disposal, and graceful fidelity reduction."
argument-hint: "[journey/scene/scope] [--fix]"
disable-model-invocation: true
---

# Measure the experience, not theoretical performance

Read `references/experience-performance.md`, `references/experience-probe.md`, `references/orchestration-compilation.md`, and the relevant web/creative interaction contract.

Use `scripts/product_quality_router.py --task-kind experience-perf`.

The Codex Sol profiler executes the bounded browser/runtime profiling pass only when a matching shared experience bundle does not already contain credible performance artifacts. The fresh `experience-perf-reviewer` adjudicates the evidence.

Without `--fix`, return measurements, dominant bottleneck, uncertainty and `PERF_GATE: PASS|REPAIR|BLOCKED`, plus its normalized gate envelope.

With `--fix`, repair the measured hot path only, then remeasure once. Do not micro-optimize absent/non-dominant code.

Creative WebGL/canvas experiences must include runtime/mobile evidence, resource cleanup and graceful fidelity/fallback behavior. Never claim a frame-rate target from static source inspection.
