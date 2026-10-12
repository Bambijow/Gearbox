# Creative web workflow

Creative web treats the browser as a medium, not as a slideshow of effects.

The goal is an original experience whose interaction, motion, typography, imagery and technical implementation support the subject. Do not imitate the distinctive visual identity of a particular designer or developer.

## When to use

Use the creative-web lane for:

- immersive portfolios and showcases;
- campaign / cultural / entertainment experiences;
- interactive editorials;
- product launches where interaction is part of the story;
- bespoke visualizers, spatial interfaces or WebGL/canvas experiences;
- surfaces explicitly asking for experimental interaction or art-direction-led implementation.

Do not use it for an ordinary dashboard or settings form that merely needs good UX.

## Direction

The creative director starts from:

- subject/product truth;
- audience and use scene;
- narrative or exploratory structure;
- available real assets;
- existing brand/design authority;
- intended device/input classes;
- performance/accessibility constraints.

Then define one interaction thesis:

```text
"What does the visitor DO that makes this experience itself?"
```

Examples of interaction theses:

- browse work through spatial depth;
- scrub chronology through typography;
- reveal material through pointer pressure/velocity;
- navigate chapters through a continuous camera;
- transform a data object rather than switch pages.

The interaction thesis must make sense without naming a library or effect.

## Creative-tech selection

Choose the least complex rendering stack that can express the thesis.

Decision order:

1. semantic DOM + CSS;
2. SVG / CSS transforms / Web Animations;
3. Canvas 2D;
4. WebGL / Three.js / OGL / custom shaders;
5. mixed DOM + WebGL only when layering adds real value.

WebGL is not a quality badge. Do not add it for a background blob, generic displacement or cursor trail that CSS/canvas could handle.

Do not add a new animation/rendering dependency when the repository already has a capable stack unless the gain is concrete.

## Scene / interaction architecture

For creative surfaces, record:

- scene/chapter/state graph;
- camera or viewport model if spatial;
- input mapping: wheel, pointer, touch, keyboard, drag, device motion where applicable;
- scroll ownership: native, mapped, or synthetic;
- transitions between chapters/scenes;
- DOM/WebGL layering;
- loading strategy;
- asset lifecycle/disposal;
- mobile and reduced-motion alternatives;
- deep-link/back/forward expectations.

Scroll is one input channel, not a timeline generator by default. Avoid hijacking native scroll unless the experience genuinely requires a controlled camera/timeline.

## Typography and motion

Typography may be an interactive material, but still carries language.

Define:

- readable default state;
- kinetic transformation;
- when motion pauses for comprehension;
- how resize and localization affect geometry;
- fallback when variable font/WebGL text technique fails.

Motion follows an authored rhythm, not identical easing everywhere.

## Pointer and cursor

A custom cursor is allowed only when it communicates interaction state or belongs to the approved world.

Never hide the native cursor just to display a larger circle. Critical actions must remain discoverable on touch and keyboard.

## Images and media

Real assets outrank generic generated spectacle.

Use image/video/3D generation only when it serves the direction and provenance is understood. Do not let decorative generated imagery become fake product proof.

## Performance contract

Set a budget before building:

- target device class;
- expected frame-rate class;
- maximum initial asset weight when known;
- texture/video resolution strategy;
- lazy/preload boundaries;
- shader/postprocess complexity;
- DOM count / layout pressure for hybrid scenes.

Measure, do not claim "60fps" from code inspection.

Protect:

- input responsiveness;
- main-thread long tasks;
- GPU memory / texture disposal;
- resize/device-pixel-ratio cost;
- mobile thermal/battery behavior when material.

Prefer graceful fidelity reduction over a broken masterpiece.

## Accessibility / escape hatch

Every creative experience needs a usable path when:

- reduced motion is requested;
- pointer precision is unavailable;
- WebGL fails;
- GPU is weak;
- keyboard is primary;
- screen size is small;
- assets are still loading.

Do not build a separate boring website unless necessary. Preserve the same content and hierarchy with a simpler interaction model.

## Anti-gimmick test

Before accepting an effect, ask:

1. what information/feeling/action does it clarify?
2. would the experience lose identity without it?
3. is there a cheaper technique with the same value?
4. does it survive mobile/reduced-motion/failure?
5. can a visitor still understand and navigate while it runs?

If the answer is mostly "it looks cool", remove or demote it.

## Evidence

Creative web requires actual runtime evidence:

- captures/video or browser playback for key scenes;
- input-state tests;
- mobile/narrow behavior;
- reduced-motion fallback;
- performance traces/measurements for expensive paths;
- console/GPU/runtime errors;
- cleanup/disposal behavior for WebGL scenes.

The source code is not the experience.

## Specialist gates

Before final creative-web PASS:

- run `a11y-audit` for the representative journey;
- run `experience-perf` for expensive canvas/WebGL/media/motion paths;
- run semantic visual regression when an approved baseline exists;
- run content-design when the experience introduces substantial narrative/UX copy.

The creative reviewer consumes these results instead of replacing them with vibes.
