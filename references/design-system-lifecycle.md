# Design system lifecycle

A design system is executable product infrastructure, not a gallery of components.

## Sources of truth

Resolve authority in this order:

1. explicit approved product/design contract;
2. canonical tokens/theme files and shared component APIs;
3. DESIGN.md or equivalent system docs;
4. representative shipped surfaces and stories/tests;
5. local one-off implementations last.

Do not canonize accidental drift merely because it exists in production.

## Audit dimensions

Inventory and group by role, not raw value:

- color and semantic roles;
- typography families/roles/scale/line-height;
- spacing and sizing scale;
- radii;
- border/elevation/material roles;
- motion/easing/duration roles;
- breakpoints/container widths;
- z-index/layering;
- icons;
- component variants/states;
- interaction contracts;
- accessibility semantics.

Find:

- exact duplicates with different names;
- near-duplicates with no behavioral reason;
- raw one-off values bypassing tokens;
- components that represent the same role through divergent APIs;
- variants that differ only cosmetically;
- missing states such as focus/loading/error/disabled;
- tokens nobody uses;
- hard-coded values that should remain local rather than becoming tokens.

## Classification

- `KEEP`: distinct role and consistent use.
- `EXTRACT`: repeated stable value/pattern deserves a token/component.
- `MERGE`: multiple tokens/components represent one role.
- `ALIGN`: implementation drift from an existing canonical primitive.
- `DEPRECATE`: current system no longer needs the primitive, but consumers need migration.
- `BLOCKED`: conflicting product/design truth prevents safe reconciliation.

## Drift rule

Design drift is a mismatch in role, not simply a numeric difference.

Two 16px values can serve different roles and remain separate. A 15px and 16px gap used interchangeably for the same role may be drift.

Every drift finding names:

- role;
- canonical evidence;
- divergent evidence;
- user-visible or maintenance consequence;
- smallest migration path.

## Apply protocol

Without `--apply`, report only.

With `--apply`:

1. change the canonical primitive first;
2. migrate a bounded consumer set;
3. verify representative states and responsive behavior;
4. avoid mass search-replace when semantic roles differ;
5. remove dead aliases only after consumers are gone;
6. update canonical docs only when actual system truth changed.

Do not refactor the whole UI because one component drifted.

## Gate

Return:

```text
DESIGN_SYSTEM_GATE: PASS | DRIFT | BLOCKED
```

PASS means the audited scope has coherent role-level primitives and no material unresolved drift.
