---
name: a11y-audit
description: "Run a focused accessibility audit on a component, page, or user journey using runtime/browser evidence plus repository-native automated tooling when available. Covers keyboard/focus, semantics, names, contrast, reflow, forms/errors, reduced motion, touch, and sensory alternatives."
argument-hint: "[scope/journey] [--fix]"
disable-model-invocation: true
---

# Accessibility as a runtime gate

Read `references/accessibility-audit.md`, `references/component-interaction.md`, and the relevant product/design contract.

Use `scripts/product_quality_router.py --task-kind a11y-audit`.

The fresh `accessibility-reviewer` is read-only for the audit. Prefer browser/accessibility-tree/runtime evidence. Use axe/Lighthouse/Playwright or repository-native tools when present, but never treat an automated clean scan as complete proof.

Without `--fix`, return findings and `A11Y_GATE: PASS|REPAIR|BLOCKED`.

With `--fix`, send only validated findings through normal worker-owned mutation, then rerun the affected accessibility path. Do not rewrite the product to satisfy a linter mechanically.

For material web-design/creative-web work, an unresolved blocking accessibility failure prevents final PASS.
