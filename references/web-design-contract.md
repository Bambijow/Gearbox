# Web design contract

Web design work is a production decision surface, not a request for decorative CSS.

## Resolve visual authority

Before inventing anything, inspect the strongest existing authority:

1. explicit user brief / approved direction;
2. DESIGN.md or equivalent;
3. repository tokens, components, layouts and representative shipped screens;
4. current screenshots/goldens;
5. category convention only when nothing stronger exists.

A missing DESIGN.md does not make an established product visually greenfield.

## Surface mode

Use one mode for the surface:

- **Persuade**: help a visitor decide and act.
- **Operate**: help a user complete work.
- **Read**: optimize comprehension and wayfinding.
- **Experience**: let the work itself lead.

## Scope

### Refine
Preserve identity, truth, behavior and content outside the requested change.

### Surface
Create a substantial new page/flow inside the established visual world.

### Redesign
Replace the visual world only with explicit authorization. Preserve product truth and functional constraints.

## Anti-slop direction gate

Read `references/web-design-anti-slop.md`. For `surface` and `redesign`, the director MUST name the category rut, choose at least two product-grounded departures, define one product-shaped signature device, and record slop risks. Generic composition with no deliberate justification is not direction-complete.

For `refine`, preserve the incumbent world and address generic habits only inside scope.

## Design contract

Record decisions implementation cannot safely improvise:

- audience / primary job / success condition;
- mode and scope;
- incumbent authority and what must remain unchanged;
- visual thesis;
- macrostructure / information hierarchy;
- typography roles and scale;
- palette/tokens and contrast intent;
- spacing, density, radii/material treatment;
- component language;
- interaction contracts for material stateful components;
- responsive behavior;
- loading/empty/error/disabled/focus states;
- motion grammar and reduced-motion behavior;
- accessibility constraints;
- source/evidence references and anti-references;
- category rut and slop risks when applicable;
- intentional departures from category gravity;
- product-shaped signature device;
- first viewport / key-state description;
- verification surfaces and target viewports.

The contract is design authority for the build, not a CSS transcript.

## Durable design context

Reuse existing design-system docs. Keep the working contract in run artifacts. Only update a durable DESIGN.md/equivalent when the user explicitly approves a new visual world or the repository already treats that file as canonical.

## Comp handoff

When comp generation is enabled, read `references/web-design-comp-generation.md`. The comp visualizes an already-decided system. It does not replace the contract.

## Interaction handoff

Read `references/component-interaction.md`. A component with material state topology, focus movement, async feedback, interruption/reversal, gestures, drag/scrub behavior, or non-trivial keyboard semantics gets an interaction contract before implementation. Do not make animation the source of state.

## Motion handoff

When motion is structurally important, delegate timing/execution to the existing `motion-design` lane.
