# Image asset workflow

Use for non-pixel game imagery: UI art, icons, props, backgrounds, textures, decals and other 2D assets.

## Brief contract

Before generation, pin:

- exact purpose and target screen/gameplay context;
- dimensions/aspect ratio and output format;
- alpha/transparency requirements;
- art direction, palette and visual references already owned by the repository;
- tiling/seamless requirement if applicable;
- source/export destinations and engine target.

## Generation

Actual generation is always Codex GPT-6.1 Sol. The worker may use the model's direct image-generation path and any explicitly required compatible tool, but may not silently substitute another model.

Prefer a small number of deliberate variants over a spray of near-duplicates. Preserve the selected source/editable form when the workflow exposes one.

## Verification

Check exact pixel dimensions, format, alpha channel, tiling/seam behavior, atlas compatibility when relevant, import success and obvious visual corruption. If the asset is meant for UI/gameplay readability, inspect it at intended display size rather than only zoomed in.

Do not infer visual success from a zero exit code.
