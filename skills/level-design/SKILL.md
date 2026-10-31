---
name: level-design
description: "Design, block out, and review game levels or encounters from player verbs, movement metrics, sightlines, pacing, landmarks, checkpoints, rewards, spawn rules, traversal/combat/puzzle beats, and real playtest evidence."
argument-hint: "[brief/scene/scope] [--apply]"
---

# Level and encounter design through playable evidence

Read `references/level-design.md`, `references/orchestration-compilation.md`, repository game-design conventions, and relevant art-direction/gameplay contracts.

Use `scripts/product_quality_router.py --task-kind level-design`.

The `level-designer` (Opus 5.5/high) owns spatial/gameplay direction, metrics, encounter graph and acceptance. Codex GPT-6.1 Sol/high may execute bounded Godot/Blender blockout, collision/navmesh, exact-dimension geometry, spawn/checkpoint placement and repetitive scene wiring.

Without `--apply`, return the level contract, blockout plan and playtest hypotheses.

With `--apply`, require a credible Godot/Blender execution path for blockout. Prove scale/navigation/pacing with cheap geometry before art polish.

A level cannot pass from editor screenshots. Traverse the real blockout and return `PLAYTEST_GATE: PASS|REPAIR|BLOCKED` with orientation, readability, exploits, pacing, checkpoint and performance observations, plus the normalized gate envelope.
