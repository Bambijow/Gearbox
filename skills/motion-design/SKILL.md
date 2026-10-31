---
name: motion-design
description: "Design and produce game-ready motion: UI transitions, title/scene motion, camera moves, loops, animated props, 2D/3D motion language and timing. Opus 5.5 directs; Codex GPT-6.1 Sol may execute bounded Blender/Godot/Aseprite animation work."
argument-hint: "[brief/spec/scope] [--apply]"
---

# Motion design with an Opus director and tool-aware execution

Read `references/game-asset-contract.md` and `references/motion-design-workflow.md`. Read `references/art-direction.md` when an art-direction contract or style bible exists; inherit it explicitly and record intentional deviations.

Resolve the specialist route with `scripts/game_asset_router.py --task-kind motion-design`, passing Claude and Codex capabilities separately.

Opus 5.5/high owns the motion language, hierarchy, timing decisions, ambiguous creative choices and final acceptance. Codex GPT-6.1 Sol/high may execute bounded tool work when that is cheaper or when Blender/Godot/Aseprite is available only to Codex.

Before production, pin the motion contract: purpose, medium, target engine, duration, FPS, loop behavior, timing beats, easing/curve language, source/export paths, camera/rig/state dependencies and accessibility/reduced-motion behavior when UI is involved.

With `--apply`, use the dedicated `motion-design-director`. Delegate mechanical animation operations to Codex when useful: keyframe placement from an approved beat sheet, curve cleanup, repetitive state variants, camera path implementation, export/bake work, sprite-frame assembly and engine wiring. Do not delegate unresolved motion direction as if it were mechanical.

Verify the real result at playback speed. Inspect start/end states, loop seams, frame pacing, easing, readability, camera collisions/clipping and target-engine import. For 3D motion that changes a model, rig, skeleton, materials or export structure, also run the mandatory GPT-6 Astra `review-3d` gate.
