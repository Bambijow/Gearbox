# Game audio and sound design

Audio design is a state/priority system, not a folder of sound files.

## Audio contract

Capture:

- game event / user action;
- intended perceptual function: acknowledge, warn, reward, locate, texture, ambience, music transition;
- source type: one-shot, loop, layer, stem, procedural;
- variation strategy;
- priority/concurrency limit;
- bus/category;
- loudness/headroom target relative to the project mix;
- spatialization/attenuation;
- loop/crossfade behavior;
- ducking/sidechain relationships;
- state-machine entry/exit;
- latency requirement;
- platform/import/codec constraints;
- accessibility alternative when audio carries important information.

## Event map

Prefer semantic events such as `player.damage` or `ui.confirm`, not filenames as contracts.

Multiple gameplay events may share a sound family while varying pitch/sample/texture. Avoid repetitive machine-gun playback.

## Mix hierarchy

Define what wins when many events happen:

1. critical gameplay information;
2. player feedback;
3. dialogue/mission information;
4. environment/ambience;
5. decorative texture.

Project-specific direction overrides this example.

## Execution

Opus 5.5 owns sonic direction and event/mix architecture. Codex Sol may implement bounded engine/middleware wiring, import settings, event hookups, buses, attenuation, concurrency and deterministic variations.

Use live capabilities such as Godot, FMOD, Wwise, Reaper or other audio tooling when available. Do not invent an unavailable audio-generation capability.

If no sound-generation tool exists, the skill can still design the audio system and wire supplied assets.

## Verification

Listen in context, not solo only. Test:

- repeated event spam;
- simultaneous priorities;
- pause/menu transitions;
- scene/state transitions;
- loop seams;
- spatial falloff;
- headphones/speakers when relevant;
- missing asset/fallback;
- accessibility alternative for critical cues.

## Gate

Return:

```text
AUDIO_GATE: PASS | REPAIR | BLOCKED
```
