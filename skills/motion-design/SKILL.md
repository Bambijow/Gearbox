---
name: motion-design
description: "Design and produce game-ready motion: UI transitions, title/scene motion, camera moves, loops, animated props, 2D/3D motion language and timing. Opus 5.5 directs; Gemini Gemini 4 Carbon/high executes 3D animation; Gemini Gemini 4 Neon can execute non-3D animation."
argument-hint: "[brief/spec/scope] [--apply]"
---

# Motion design with an Opus director and tool-aware execution

Read `references/game-asset-contract.md` and `references/motion-design-workflow.md`. Read `references/art-direction.md` when an art-direction contract or style bible exists; inherit it explicitly and record intentional deviations.

Resolve the specialist route with `scripts/game_asset_router.py --task-kind motion-design`, passing Claude and Gemini capabilities separately. For 3D motion (3D rigs, models, cameras or Blender/Godot scene animation), pass `--three-d` to force Carbon/high. The non-3D route remains Neon-eligible.

Opus 5.5/high owns the motion language, hierarchy, timing decisions, ambiguous creative choices and final acceptance. Gemini Gemini 4 Carbon/high must perform substantive 3D tool work with live Gemini Blender/Godot capability. Gemini Neon/high may perform non-3D motion work. Never downgrade 3D execution because Carbon lacks a required tool; block instead.

Before production, pin the motion contract: purpose, medium, target engine, duration, FPS, loop behavior, timing beats, easing/curve language, source/export paths, camera/rig/state dependencies and accessibility/reduced-motion behavior when UI is involved.

With `--apply`, use the dedicated `motion-design-director`. Delegate mechanical animation operations to Gemini when useful: keyframe placement from an approved beat sheet, curve cleanup, repetitive state variants, camera path implementation, export/bake work, sprite-frame assembly and engine wiring. Do not delegate unresolved motion direction as if it were mechanical.

Verify the real result at playback speed. Inspect start/end states, loop seams, frame pacing, easing, readability, camera collisions/clipping and target-engine import. For 3D motion that changes a model, rig, skeleton, materials or export structure, also run the mandatory independent Gemini 4 Carbon `review-3d` gate.
