---
name: audio-design
description: "Design and implement game/product audio systems: semantic events, one-shots/loops/layers, variation, priority/concurrency, buses, spatialization, attenuation, ducking, state transitions, import constraints, and accessibility alternatives."
argument-hint: "[brief/system/scope] [--apply]"
disable-model-invocation: true
---

# Audio as a state and priority system

Read `references/audio-design.md`, `references/orchestration-compilation.md`, and the project's audio/engine conventions.

Use `scripts/product_quality_router.py --task-kind audio-design`.

The `audio-director` (Opus 5.5/high) owns sonic intent, event taxonomy, mix hierarchy, variation, spatialization and acceptance. Codex GPT-6.1 Sol may execute bounded Godot/FMOD/Wwise/Reaper/other available tool wiring and deterministic import/event/bus setup.

Do not invent an audio-generation capability. If no sound-generation tool exists, design the system and wire supplied assets only.

Without `--apply`, return the audio contract/event map and `AUDIO_GATE` readiness.

With `--apply`, capability-preflight exact external tools, keep generated/supplied asset provenance, implement bounded wiring, and verify repeated events, concurrency, state transitions, loop seams, spatial falloff, missing assets and critical-cue alternatives.

Return `AUDIO_GATE: PASS|REPAIR|BLOCKED` plus the normalized gate envelope with runtime-evidence fingerprint.
