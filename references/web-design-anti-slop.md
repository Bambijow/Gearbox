# Web design anti-slop gate

AI slop is not a specific aesthetic. It is design produced by default associations instead of product-specific decisions.

The web-design lane treats unearned genericity as a quality defect. A surface can be accessible, responsive and technically correct yet still receive `REPAIR` when it looks assembled from model defaults rather than designed for the product.

## Category-rut declaration

Before directing a new surface or redesign, name the likely category rut in five dimensions:

- composition;
- typography;
- color/material treatment;
- component/container habits;
- motion/interaction habits.

Also name the predictable opposite when it is equally generic. "Dark dev-tool SaaS" and "bright editorial minimalism" can both be ruts.

Then record at least two intentional departures tied to product truth, audience behavior, content, or the chosen visual world. Do not be different merely to be strange.

For `refine`, do not invent a new direction. Instead identify whether the requested surface already contains generic habits and remove them only when they fall inside scope.

## Defaults that require explicit justification

These patterns are forbidden as reflexes. They may appear only when the brief, incumbent system, content structure, or a named design decision earns them:

- centered marketing hero made from eyebrow + huge headline + vague subhead + two pill CTAs;
- gradient text used as emphasis;
- violet/blue aurora glows, radial blobs, decorative light leaks, or ambient gradients with no product meaning;
- glassmorphism/blur used as generic decoration;
- bento grids chosen before content structure is understood;
- a page scaffold made mostly of same-size rounded cards;
- three/four feature cards with icon-in-rounded-square + heading + paragraph because "features need cards";
- nested cards;
- pills used for ordinary containers, navigation, or large controls;
- excessive rounded rectangles where spacing/alignment could create grouping;
- uniform soft shadow + 1px border on every container;
- monospace used to cosplay "developer/technical" outside code/data/measurement;
- decorative grid/blueprint backgrounds when the product has no spatial/technical reason for them;
- section numbers like 01/02/03 when sequence is not meaningful;
- generic abstract 3D shapes, floating orbs, mesh gradients, or generated blobs standing in for real product/artifact evidence;
- logo clouds, testimonials, awards, metrics, or customer proof that are invented, placeholder, or not supplied as truth;
- identical fade-up-on-scroll applied to every section;
- every interactive element receiving the same hover lift/glow regardless of hierarchy;
- emoji/Unicode glyphs used as a substitute for a coherent icon system;
- excessive tiny uppercase labels/eyebrows whose only job is to make sections look "designed";
- copy that sounds like generic AI marketing rather than the product's own vocabulary.

The builder must not "modernize" a design by introducing these patterns when the approved contract does not call for them.

## Product-shaped composition

A strong direction should remain recognizable when generic marketing copy is removed.

Before approval, answer:

1. What does this product actually do that changes the page structure?
2. What information or artifact deserves visual primacy?
3. What recurring object, workflow, state, data shape, or interaction can become a genuine design device?
4. What would disappear if this were a different product in the same category?

For a new surface/redesign, the contract names one **signature device** derived from product truth. It can be typographic, spatial, data-driven, interactive, illustrative, or motion-based. It must carry meaning, not merely novelty.

A surface with no product-shaped device and no deliberate reason for conventional composition is not direction-complete.

## Component discipline

Use containers only when they encode a real grouping, state, interaction boundary, or reusable component contract.

Prefer:

- hierarchy from typography, spacing and alignment;
- content-shaped layouts instead of forcing equal cards;
- a small number of radius/elevation/material roles;
- asymmetry or density changes when content calls for them;
- real product UI, real artifacts, diagrams, data or imagery over generic decoration.

Do not turn every paragraph into a card because cards are easy to generate.

## Typography discipline

Typography must have a reason beyond "clean SaaS".

- use roles with meaningful contrast in size/weight/width/style;
- do not default to the currently fashionable geometric/grotesk face solely because peers use it;
- monospace belongs to code/data/measurement or a deliberately established brand voice;
- tiny uppercase kicker labels are not hierarchy;
- gradient text is not typography;
- test real copy and wrapping at real viewports.

When a distinctive display voice is needed, choose it from the approved visual world rather than from model familiarity.

## Color and material discipline

Choose light/dark, accent hue, surfaces and depth from use context and visual direction.

A default dark canvas + electric violet/blue accent is not "technical". A white canvas + black type + one neon accent is not automatically "editorial". Both need reasons.

Use a coherent depth/material system. Decoration must belong to the world or communicate hierarchy/state.

## Motion discipline

Motion must express hierarchy, causality, spatial relationship or product character.

Do not scatter identical entrance animations across the page. Prefer one or a few authored motion moments with different roles. Keep an already-legible default state and honor reduced motion.

If motion is material to the direction, delegate timing/execution to the motion-design lane.

## Truth over decoration

Never create fake proof to make a page feel complete.

Do not invent:

- company/customer logos;
- testimonial quotes/people;
- usage numbers;
- awards;
- benchmark claims;
- "trusted by" statements;
- fake screenshots presented as real product evidence.

Illustrative/demo values must be explicitly framed as such.

## Director output

For `surface` and `redesign`, the design contract MUST contain:

```yaml
category_rut:
  composition: ...
  typography: ...
  color_material: ...
  containers: ...
  motion: ...

intentional_departures:
  - ...
  - ...

signature_device:
  source_in_product_truth: ...
  expression: ...
  why_it_earns_attention: ...

slop_risks:
  - pattern: ...
    prevention: ...
```

For `refine`, include only applicable in-scope slop risks.

## Builder self-check

Before handoff to review, the builder checks the rendered implementation against this reference and the design contract.

It may remove obvious unapproved defaults, but it must not invent a replacement visual direction. If avoiding a slop pattern requires a new design decision, return the decision to the director.

## Reviewer SLOP_GATE

The fresh rendered reviewer returns an explicit:

```text
SLOP_GATE: PASS | REPAIR
```

`REPAIR` is required when a visible generic pattern appears without support from the brief, incumbent system, content structure, or approved contract.

Each slop finding must state:

- the visible pattern;
- where it appears;
- why it is unearned in this design;
- what product-specific contract it weakens;
- the smallest correction.

Do not flag a pattern merely because it appears on this list. If it is explicitly earned by the brief/system/contract, it is not slop.

Visual `PASS` requires both the ordinary web-design review and `SLOP_GATE: PASS`.
