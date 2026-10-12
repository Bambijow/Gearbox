# Accessibility audit

Accessibility is observable interaction behavior, not ARIA decoration.

## Scope

Audit the smallest complete user journey or component set that can establish the requirement. Prefer browser/accessibility-tree/runtime evidence over static source guesses.

## Required dimensions

### Keyboard and focus

Check:

- every interactive function reachable without pointer;
- logical tab/roving order;
- visible focus;
- focus entry/restoration for dialogs, menus, drawers and route transitions;
- no focus traps except intentional modal containment;
- Escape/cancel behavior;
- skip/landmark navigation where appropriate.

### Semantics and names

Check:

- native elements preferred over reimplemented roles;
- accessible names/descriptions;
- headings/landmarks;
- form label/error association;
- live regions/status only when users need announced updates;
- table/list semantics where structure matters.

### Visual access

Check:

- contrast;
- zoom/reflow;
- text resizing;
- orientation/responsive assumptions;
- information not encoded only by color;
- focus/error states visible across themes.

### Motion and sensory access

Check:

- reduced-motion behavior;
- no required information only in animation;
- flashing/seizure risk where relevant;
- alternatives for drag, hover precision, audio-only or gesture-only interaction.

### Forms and errors

Check:

- errors identify field/problem/recovery;
- validation timing does not fight input;
- required/invalid state is perceivable;
- submission state and async errors are announced appropriately.

### Touch and targetability

Check practical target size, spacing, gesture alternatives and orientation/device behavior.

## Automated tools

Use repository-native axe/Lighthouse/Playwright accessibility tooling when available, but treat automated findings as evidence, not completeness. Manual keyboard/focus/interaction checks remain required for material UI.

## Severity

- `BLOCKER`: a user cannot perform the required job through an accessibility path.
- `IMPORTANT`: material semantics/focus/contrast/reflow failure with a reasonable repair.
- `MINOR`: local quality issue with low task impact.

## Gate

Return:

```text
A11Y_GATE: PASS | REPAIR | BLOCKED
```

No material web-design or creative-web PASS when the requested surface contains a known blocking accessibility defect.
