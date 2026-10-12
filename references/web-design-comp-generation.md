# Web design comp generation

A web comp is a visual prototype of an already-decided design system. It is not permission for the image model to invent product truth.

## Ownership

- Claude Opus 5.5 owns the design contract and approves the comp.
- Codex GPT-6.1 Sol owns the comp-generation pass.
- A GPT Image model renders the pixels under Codex orchestration.
- The final web builder receives both the approved contract and approved comps.

Codex is the reasoning/execution owner of the pass; the GPT Image model is the rendering engine.

## When to run

Default policy:

- `refine`: skip unless explicitly requested or the visual change is large enough that a comp would remove ambiguity;
- `surface`: generate when image generation is available;
- `redesign`: generate when image generation is available;
- `--comp require`: block with `WEB_COMP_BLOCKED` if no supported image-generation path exists;
- `--comp skip`: code-led path; rendered review still remains mandatory.

Do not make a trivial spacing/copy fix pay for image generation.

## Inputs

The comp packet contains:

1. approved web design contract;
2. `references/web-design-anti-slop.md`;
3. canonical design-system source when present: DESIGN.md, tokens, component docs, CSS variables;
4. 1-4 representative incumbent screenshots/components when available;
5. selected Inspo evidence and intentional departures;
6. exact product copy/content that must remain true;
7. target desktop/mobile viewports;
8. source paths and provenance.

Never put credentials, private URLs, secrets, or unpublished customer data into image-generation prompts.

## Design-system distillation

Before generation, Codex distills the design system into a visual prompt packet:

```yaml
identity:
  visual_thesis: ...
  surface_mode: ...
  scope: ...
  signature_device: ...

type:
  display_character: ...
  body_character: ...
  scale_and_weight_roles: ...

color:
  paper: ...
  text: ...
  accent_roles: ...
  semantic_roles: ...

material:
  radii: ...
  border_or_shadow: ...
  depth_rules: ...

layout:
  macrostructure: ...
  density: ...
  alignment: ...
  first_viewport: ...

components:
  nav: ...
  buttons: ...
  forms: ...
  cards_or_non_card_grouping: ...

motion:
  grammar: ...

anti_slop:
  category_rut: ...
  intentional_departures: ...
  prohibited_defaults: ...
```

Do not dump raw CSS into the image prompt when a shorter semantic description carries the design more faithfully.

## Rendering path

Preferred initial-generation renderer: configured `web_comp_image_model` (default `gpt-image-2.5-flare`).

Preferred correction/edit renderer: configured `web_comp_edit_model` (default `gpt-image-2.5-sunburst`).

When representative screenshots exist, prefer an image-edit/reference path so the new comp inherits the actual product's visual system. Otherwise generate from the distilled design system + design contract.

Generate one coordinated pair from the same prompt/seeded direction:

- desktop: landscape composition, normally 1536x1024;
- mobile: portrait composition, normally 1024x1536.

The mobile comp is not a cropped desktop comp. It expresses the same system with a real mobile information hierarchy.

## Truth boundary

Generated comps may hallucinate text, icons, logos, metrics or product details.

Therefore:

- exact product copy from the contract wins over raster text;
- never promote generated customer logos, testimonials, awards, usage numbers or claims into product code;
- use generated text only as placement texture when exact copy is not visually material;
- semantics, accessibility, interaction and data behavior always come from the contract/codebase;
- a generated screenshot of nonexistent product capability is illustrative only and must not become a claim.

## Comp anti-slop gate

The comp itself must pass the anti-slop contract before approval.

Reject/revise comps that fall back to unearned:

- purple/blue glow SaaS hero treatment;
- generic card soup;
- icon-card feature trios;
- gradient headline emphasis;
- generic 3D blobs/orbs;
- developer-costume monospace;
- fake social proof;
- identical fade-up section rhythm;
- other category-rut habits explicitly rejected by the contract.

A beautiful but generic comp is a failed comp.

## Approval and correction budget

The Opus director reviews desktop + mobile together against:

- design contract;
- design-system authority;
- anti-slop gate;
- product truth.

Verdict:

- `COMP_APPROVED`;
- `COMP_REVISE`;
- `COMP_BLOCKED`.

Allow at most one targeted image-edit correction round before implementation. The edit packet names concrete mismatches; it does not ask the image model to "make it better".

If the second comp still cannot carry the contract, fall back to code-led implementation or block according to the user's `--comp` policy. Do not start an infinite visual generation loop.

## Artifacts

Store transient comps under the run directory, for example:

```text
.gearbox/runs/<run-id>/web-design/
├── comp-manifest.json
├── comp-desktop.png
├── comp-mobile.png
└── comp-prompt.md
```

The manifest records:

- design-contract hash;
- design-system/source pointers;
- Codex model;
- image-generation/edit model;
- prompt path;
- output paths;
- reference-image paths;
- approval/revision status.

Do not persist raw secrets or API credentials.

## Build handoff

The final Codex builder gets:

1. approved design contract;
2. approved desktop/mobile comps;
3. incumbent components/tokens;
4. exact product copy/data constraints;
5. responsive/state/accessibility rules.

For conflicts:

```text
product truth / accessibility / behavior
    > design contract
    > approved comp
    > builder preference
```

The comp governs visual composition/material/hierarchy, not semantic correctness.

## Finish review

Rendered implementation is compared against both the contract and approved comp. The reviewer names material drift, but does not demand pixel-identical reproduction where browser behavior, real content or accessibility requires adaptation.
