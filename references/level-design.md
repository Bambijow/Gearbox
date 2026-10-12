# Level and encounter design

Level design turns player verbs, metrics and encounter pacing into navigable space.

## Contract

Before blockout, pin:

- player verbs and movement metrics;
- camera/FOV perspective;
- navigation scale;
- jump/reach/speed constraints;
- critical path and optional loops;
- landmarks/wayfinding;
- sightlines and information reveal;
- encounter beats;
- spawn/checkpoint/recovery rules;
- resource/reward rhythm;
- traversal/combat/puzzle mix;
- accessibility/difficulty constraints;
- target engine and owned scene paths.

## Blockout first

Prove scale, navigation, sightlines and pacing with cheap geometry before art polish.

A beautiful environment with wrong metrics is not a level-design success.

## Encounter graph

Represent major beats:

```text
arrival -> read -> commit -> pressure -> release -> reward/reorient
```

Not every encounter needs every beat, but pacing should be intentional.

## Delegation

Opus 5.5 owns spatial/gameplay direction and acceptance. Codex GPT-6.1 Sol may execute bounded Godot/Blender blockout, collision/navmesh, spawn placement, exact metrics and repetitive scene wiring.

If only Codex has Godot/Blender, Opus writes the blockout packet and reviews the real scene.

## Playtest evidence

Do not approve from editor screenshots alone.

Run representative playthroughs and observe:

- time to orientation;
- navigation mistakes;
- path readability;
- unreachable/skip exploits;
- camera collision;
- encounter pacing;
- checkpoint frustration;
- dead time;
- performance hot spots;
- accessibility/difficulty failure modes.

## Gate

Return:

```text
PLAYTEST_GATE: PASS | REPAIR | BLOCKED
```

A level cannot pass without actual traversal evidence.
