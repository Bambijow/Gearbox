# Component interaction and motion contract

Component motion starts from state topology, not decoration.

```text
state machine
  -> interaction semantics
  -> feedback/focus/latency
  -> motion
```

Never start with "add a fade/scale" and reverse-engineer meaning afterward.

## When an interaction contract is required

Create one when any of these is true:

- the component has three or more meaningful user-visible states;
- opening/closing changes focus or spatial context;
- async work creates loading/success/error/retry states;
- the user can interrupt, reverse, drag, scrub or rapidly reopen;
- keyboard navigation has a stateful model;
- pointer/touch interactions differ materially;
- the component reorders, expands, collapses, overlays or moves content;
- optimistic UI or undo changes perceived causality;
- scroll/pointer position drives visual state.

A static card or simple color hover does not earn a contract.

## Contract

Record only meaningful fields:

```yaml
component: ...
states:
  - idle
  - hover
  - pressed
  - loading
  - success
  - error

transitions:
  idle_to_loading:
    trigger: click
    feedback: immediate
    focus: preserved
    reversible: false
    interruption: ignore_duplicate
    motion_role: acknowledge action

input:
  keyboard: ...
  pointer: ...
  touch: ...

latency:
  immediate_feedback: ...
  delayed_feedback: ...
  optimistic_behavior: ...

focus:
  entry: ...
  movement: ...
  restore: ...

motion:
  spatial_model: ...
  duration_class: instant|local|structural
  easing_language: ...
  reduced_motion: ...
```

Do not invent states that product behavior does not need.

## Response before animation

The interface should acknowledge input immediately. Motion must not delay the feeling that an action registered.

Useful heuristics, not rigid constants:

- press/hover acknowledgment: roughly one frame to 100ms;
- small local transitions: often 120-220ms;
- larger spatial/overlay transitions: often 180-350ms;
- async operations that become perceptibly long need progress/working feedback rather than a long decorative transition.

Prefer continuity and interruption safety over hitting exact durations.

## State semantics

### Hover

Hover is enhancement, never the only carrier of required information or action. Touch and keyboard must have equivalent semantics.

### Press

Press state acknowledges causality. It should not make the user wait for a decorative sequence before the real action starts.

### Loading

Preserve context and avoid layout jumps. Disable duplicate destructive submission when appropriate, but do not indiscriminately freeze unrelated UI.

### Success

Success feedback should match consequence. Tiny local actions rarely need a celebration animation. Large completion moments may.

### Error

Errors prioritize recovery and legibility. Do not animate the user's attention away from the correction path.

### Open/close

Dialogs, drawers, menus, popovers and command palettes define entry focus, focus trap/roving model where appropriate, Escape semantics, outside-click semantics, exit focus restoration and interruption behavior.

## Reversibility and interruption

For interruptible UI, define what happens when the user acts mid-transition.

Examples:

- accordion reverses from its current interpolated state rather than snapping;
- drawer close during open reverses smoothly;
- repeated submit does not spawn duplicate async actions;
- rapid tab changes settle on the latest requested state;
- drag cancellation returns predictably.

Never make animation state the source of product state.

## Spatial continuity

Movement should preserve mental models:

- an expanding element should appear to grow from its source;
- a shared object moving between states should retain identity;
- overlays should communicate where they came from when that context matters;
- content reordering should help track moved items.

Use crossfades when spatial continuity would be fake or distracting.

## Component motion hierarchy

Use three classes:

- **instant**: state acknowledgment, hover/press/focus;
- **local**: expand/collapse, popover, tab underline/content transition, toast;
- **structural**: drawer, route/view transition, major layout transformation.

Structural motion that becomes a creative language should hand off to the motion-design or creative-web lane.

## Accessibility

Always specify:

- keyboard semantics and visible focus;
- screen-reader-relevant state changes when applicable;
- `prefers-reduced-motion` behavior;
- touch target/input alternatives;
- no critical information available only through motion;
- no motion that blocks reading or input.

Reduced motion usually preserves state change while removing travel/parallax/large transforms, not removing all feedback.

## Verification

Exercise the component with:

- pointer;
- keyboard;
- touch/emulation where relevant;
- rapid repeated input;
- interruption/reversal;
- loading -> success;
- loading -> error/retry;
- reduced motion;
- narrow layout.

The reviewer judges the actual state transition, not the presence of CSS transition properties.
