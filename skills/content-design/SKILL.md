---
name: content-design
description: "Design and audit UX copy for product surfaces: labels, actions, empty/loading/success/error states, validation, onboarding, destructive confirmations, and recovery. Preserves product truth and domain language while removing generic AI/marketing copy."
argument-hint: "[scope/surface] [--apply]"
disable-model-invocation: true
---

# UX writing as interaction design

Read `references/content-design.md`, repository glossary/domain docs, and the relevant product/design contract.

Use `scripts/product_quality_router.py --task-kind content-design`.

The `content-designer` works state-by-state. It must preserve factual claims, capabilities, policies, metrics and customer truth. Never invent social proof or marketing claims to make a screen feel complete.

Without `--apply`, return a state-based copy plan plus `CONTENT_GATE: PASS|REPAIR|BLOCKED`.

With `--apply`, mutate only approved copy/resources through a bounded worker. Preserve localization/pluralization patterns and do not silently rename public/domain concepts.

Prefer concrete actions and recovery guidance over generic "Something went wrong", "Continue", or AI-marketing language.
