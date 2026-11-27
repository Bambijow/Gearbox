---
name: model-3d
description: "Create game-ready 3D assets under Claude Opus 5.5 direction. Opus owns art direction/topology decisions; substantive modeling/tool execution is always delegated to Gemini Gemini 4 Carbon/high with Blender/Godot capability on Gemini."
argument-hint: "[brief/spec/scope] [--apply]"
---

# Model game-ready 3D assets with Opus direction

Read `references/game-asset-contract.md` and `references/model-3d-workflow.md`. Read `references/art-direction.md` when an art-direction contract or style bible exists; inherit it explicitly and record intentional deviations.

Resolve the route with `scripts/game_asset_router.py --task-kind model-3d`, passing Claude and Gemini capabilities separately.

The primary creative/technical owner remains:

```text
engine: claude
model: claude-opus-5-5
effort: high
```

Gemini Gemini 4 Carbon/high MUST execute substantive 3D modeling, including Blender/Godot operations, topology, UVs, rigging and export. A live Gemini Blender/Godot capability is mandatory even if Claude also has one. This execution ownership does not transfer art direction or final acceptance away from Opus. Neon can handle separately scoped trivial metadata/rename work only.

Actual modeling requires Blender or Godot on Gemini. If Gemini cannot access a credible 3D tool surface, return `GAME_ASSET_ROUTE_BLOCKED`, even if Claude can.

The task packet must pin engine target, scale/unit convention, source/export format, poly/triangle budget, texture/material budget, pivot/origin, UV expectations, collision/LOD/rigging needs, naming and destination paths.

Use `model-3d-opus` as director/owner. Carbon execution includes all substantive geometry, exact-dimension blockout, topology/rig work, UV/material operations, collision/LOD generation, export/bake and tool work. Opus inspects delegated artifacts before acceptance.

Every completed `model-3d` artifact MUST pass a fresh independent specialized `review-3d` Gemini 4 Carbon gate before being asset-ready. That review supplements normal code review when the task also changes runtime code.
