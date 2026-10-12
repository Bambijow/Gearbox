# Motion design workflow

Motion design is about time, hierarchy and perception, not merely adding keyframes.

## Contract

Before execution, pin the applicable fields:

- purpose and viewer/player action;
- medium: UI, 2D sprite, 3D object, camera, title/scene transition, VFX-like loop;
- target engine/tool and source/export path;
- duration and FPS;
- loop: none, seamless, ping-pong or state transition;
- timing beats and holds;
- easing/curve language;
- spatial path, pivot/origin and camera framing;
- dependencies on rig/skeleton/state machine;
- reduced-motion/accessibility behavior for UI;
- performance/export constraints.

## Direction vs execution

Claude Opus 5.5 is the motion director. It owns:

- visual hierarchy and what should move first;
- timing rhythm and emphasis;
- ambiguous easing/style choices;
- camera intent and staging;
- whether motion supports gameplay/readability;
- acceptance of the final result.

Codex GPT-6.1 Sol may execute bounded instructions through Blender, Godot or Aseprite. Good delegated work includes translating an approved beat sheet into keyframes, curve cleanup, repetitive variants, baking/export, camera path implementation, state wiring and sprite-frame assembly.

If only Codex has the required tool capability, Opus writes an exact execution packet and reviews the produced artifact before acceptance. Tool access may move; creative ownership does not.

## Verification

Review at intended playback speed, not just frame-by-frame. Check:

- first and final states;
- loop seam and accumulated drift;
- timing/holds and ease-in/out;
- overshoot or motion that obscures gameplay/UI;
- camera clipping/collision/framing;
- transform/pivot consistency;
- animation/rig import into the target engine;
- reduced-motion fallback when applicable.

For motion that mutates a 3D model/rig/export contract, run `review-3d` after Opus acceptance.
