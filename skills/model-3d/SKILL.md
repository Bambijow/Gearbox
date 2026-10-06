---
name: model-3d
description: "Create game-ready 3D assets through the dedicated Claude Opus 5.5 specialist. The route is forced and never falls back to Codex or a cheaper Claude model. Requires an available Blender or Godot 3D capability for actual modeling."
argument-hint: "[brief/spec/scope] [--apply]"
disable-model-invocation: true
---

# Model game-ready 3D assets with Opus 5.5

Read `references/game-asset-contract.md` and `references/model-3d-workflow.md`.

Resolve the route with `scripts/game_asset_router.py --task-kind model-3d` plus the live available capabilities. The route MUST remain:

```text
engine: claude
model: claude-opus-5-5
effort: high
```

Actual modeling requires a supported 3D tool surface. Prefer Blender; allow Godot for scene-native/procedural asset work. If neither is available, stop with `GAME_ASSET_ROUTE_BLOCKED` rather than pretending a text-only description is a finished model.

The task packet must pin engine target, scale/unit convention, source/export format, poly/triangle budget, texture/material budget, pivot/origin, UV expectations, collision/LOD/rigging needs, naming and destination paths.

Use the dedicated `model-3d-opus` agent for actual creation. Keep editable source and runtime export where practical. Verify transforms, normals, topology, UV/material assignment, scale/pivot and engine import.

Every completed `model-3d` artifact MUST pass the specialized `review-3d` GPT-6 Astra gate before being considered asset-ready. That review supplements, rather than replaces, normal code review when the same task also changes runtime code.
