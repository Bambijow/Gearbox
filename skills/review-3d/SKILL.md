---
name: review-3d
description: "Review game-ready 3D assets with GPT-6 Astra only. Use after 3D creation or when auditing an existing model for topology, transforms, UVs, materials, engine import, performance budgets, rigging, collision, LODs, and production readiness."
argument-hint: "[asset/path/scope]"
disable-model-invocation: true
---

# Review 3D assets with Astra

Read `references/game-asset-contract.md` and `references/review-3d-checklist.md`.

This is a hard route:

```text
engine: codex
model: gpt-6-astra
effort: high
kind: review
```

Resolve it with `scripts/game_asset_router.py --task-kind review-3d` and the live available capabilities. Prefer Blender, otherwise allow Godot when it can inspect the actual asset. If no credible 3D inspection capability exists, return `GAME_ASSET_ROUTE_BLOCKED`. Do not silently downgrade to Sol or use Claude for the review.

Run the reviewer read-only. The packet contains the artifact contract, source/export paths, engine target, budgets, relevant screenshots/metrics and only the repository context required to understand integration constraints.

The Astra reviewer returns:

- `PASS | REPAIR | BLOCKED`;
- concrete findings with asset/object/material/bone/node identity when possible;
- severity based on runtime/production consequence;
- verification gaps;
- smallest useful repair;
- residual risks.

Do not accept aesthetic preference as a blocker unless it violates the supplied art direction or gameplay/readability contract. A passing review is not permission to skip import/runtime verification.
