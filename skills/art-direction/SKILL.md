---
name: art-direction
description: "Create or audit cross-asset art direction so independently generated 2D, pixel, 3D, UI, VFX, and motion assets remain in one coherent visual world. Use for style bibles, asset drift, family consistency, and translating one direction across media."
argument-hint: "[scope/asset-set] [--apply]"
---

# Keep the asset world coherent

Read `references/art-direction.md`, `references/game-asset-contract.md`, and `references/orchestration-compilation.md`.

Use `scripts/product_quality_router.py --task-kind art-direction`.

The `art-director` owns the cross-asset visual contract: silhouette/proportion language, palette/value hierarchy, materials, detail density, lighting, texture style, camera assumptions, UI/icon relationship, VFX/motion character, and 2D/3D translation rules.

Without `--apply`, audit assets as `COHERENT`, `DRIFT`, `INTENTIONAL_VARIANT`, or `BLOCKED`, then return `ART_DIRECTION_GATE`.

With `--apply`, update durable ART_DIRECTION.md/style-bible docs only when explicitly requested or already canonical. Actual asset repairs remain owned by the relevant image/pixel/3D/motion worker lane.

Do not make every asset identical; intentional variants need a gameplay/narrative reason. Persist a normalized `ART_DIRECTION_GATE` envelope when orchestrated.
