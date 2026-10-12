# Web design contract

Web design work is a production decision surface, not a request for decorative CSS.

## 1. Resolve visual authority

Before inventing anything, inspect the strongest existing authority:

1. explicit user brief / approved design direction;
2. existing DESIGN.md or equivalent design-system documentation;
3. repository tokens, shared components, layouts and representative shipped screens;
4. current screenshots/goldens;
5. category convention only when nothing stronger exists.

A missing DESIGN.md does not make an established product visually greenfield.

## 2. Pick the surface mode

Use one mode for the surface being changed:

- **Persuade**: help a visitor decide and act, such as landing/pricing/marketing.
- **Operate**: help a user complete work, such as dashboards, editors and settings.
- **Read**: optimize comprehension and wayfinding, such as docs/articles/changelogs.
- **Experience**: let the work itself lead, such as portfolios, showcases and galleries.

The product category does not decide the mode. A developer tool landing page is Persuade; its dashboard is Operate.

## 3. Pick the scope

### Refine

Preserve identity, product truth, behavior and content outside the requested change. Do not use a narrow task as permission to invent a new visual language.

### Surface

Create a substantial new page/flow inside the established design world. Extend the system coherently.

### Redesign

Replace the visual world only with explicit authorization. Preserve product truth, capabilities, content constraints and native/user expectations while treating the incumbent look as evidence rather than visual authority.

## 4. Design contract

Record only decisions implementation cannot safely improvise:

- audience / primary job / success condition;
- mode and scope;
- incumbent visual authority and what must remain unchanged;
- visual thesis in one short paragraph;
- macrostructure / information hierarchy;
- typography roles and scale;
- palette/tokens and contrast intent;
- spacing, density, radii/material treatment when materially distinctive;
- component language / repeated interaction patterns;
- responsive behavior at meaningful breakpoints;
- loading/empty/error/disabled/focus states;
- motion grammar and reduced-motion behavior;
- accessibility constraints;
- source/evidence references and anti-references;
- intentional departures from category gravity;
- first-viewport / key-state description;
- verification surfaces and target viewports.

Do not transcribe implementation code. The contract is design authority for the build, not a CSS spec.

## 5. Durable design context

Reuse existing design-system docs when present. For a run, keep the working contract in the run artifacts. Only create/update a durable DESIGN.md or equivalent when the user explicitly approves a new/replacement visual world or the repository already treats that file as canonical.

Local refinements should not churn global design documentation.

## 6. Motion handoff

When motion is structurally important, point to the existing `motion-design` contract instead of improvising animation inside the builder packet. The web contract still owns why/where motion matters; the motion lane owns timing and execution detail.
