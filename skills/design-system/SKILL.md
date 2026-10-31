---
name: design-system
description: "Audit, extract, reconcile, and maintain a production design system: tokens, component roles, states, interaction contracts, and drift. Use when UI primitives diverge, repeated one-off values accumulate, or a coherent system must be documented without redesigning the product."
argument-hint: "[scope/path] [--apply]"
---

# Maintain the design system as product infrastructure

Read `references/design-system-lifecycle.md`, `references/web-design-contract.md`, `references/component-interaction.md`, and `references/orchestration-compilation.md`.

Use the specialist route from `scripts/product_quality_router.py --task-kind design-system`.

The `design-system-curator` first resolves canonical authority, then classifies findings as `KEEP`, `EXTRACT`, `MERGE`, `ALIGN`, `DEPRECATE`, or `BLOCKED`. Audit roles, not just raw CSS values.

Without `--apply`, report drift and a bounded migration plan only.

With `--apply`, change canonical primitives first, migrate only the scoped consumers, verify representative states/responsive behavior, and avoid mass search-replace across semantically different roles.

Do not use a design-system cleanup as an excuse to redesign established surfaces. A one-off value can remain local when it truly represents a one-off role.

Return the domain verdict plus a normalized `DESIGN_SYSTEM_GATE` envelope matching `schemas/gate-result.schema.json`; persist it in the run when orchestrated.
