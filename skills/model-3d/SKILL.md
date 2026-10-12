---
name: model-3d
description: "Create game-ready 3D assets under Claude Opus 5.5 direction. Opus owns art direction/topology decisions; bounded modeling/tool execution may be delegated to Codex GPT-6.1 Sol when useful or when Blender/Godot is available only to Codex."
argument-hint: "[brief/spec/scope] [--apply]"
disable-model-invocation: true
---

# Model game-ready 3D assets with Opus direction

Read `references/game-asset-contract.md` and `references/model-3d-workflow.md`. Read `references/art-direction.md` when an art-direction contract or style bible exists; inherit it explicitly and record intentional deviations.

Resolve the route with `scripts/game_asset_router.py --task-kind model-3d`, passing Claude and Codex capabilities separately.

The primary creative/technical owner remains:

```text
engine: claude
model: claude-opus-5-5
effort: high
```

Codex GPT-6.1 Sol/high may execute bounded modeling/tool work when useful, and may perform the concrete Blender/Godot tool pass when the required MCP is available only to Codex. That delegation does not transfer art direction, topology/rig architecture, ambiguous silhouette choices or final acceptance away from Opus.

Actual modeling requires Blender or Godot on at least one provider. If neither can access a credible 3D tool surface, return `GAME_ASSET_ROUTE_BLOCKED`.

The task packet must pin engine target, scale/unit convention, source/export format, poly/triangle budget, texture/material budget, pivot/origin, UV expectations, collision/LOD/rigging needs, naming and destination paths.

Use `model-3d-opus` as director/owner. Good Codex delegation includes repetitive geometry, exact-dimension blockout, UV/material operations, collision/LOD generation, export/bake and other mechanically specified tool work. Opus inspects delegated artifacts before acceptance.

Every completed `model-3d` artifact MUST pass the specialized `review-3d` GPT-6 Astra gate before being asset-ready. That review supplements normal code review when the task also changes runtime code.
