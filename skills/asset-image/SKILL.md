---
name: asset-image
description: "Create game-ready 2D image assets from a visual brief. Always routes actual generation through Codex GPT-6.1 Sol; never silently falls back to Claude. Use for icons, props, backgrounds, UI art, textures, concept-to-production images, and other non-pixel game imagery."
argument-hint: "[brief/spec/scope] [--apply]"
disable-model-invocation: true
---

# Create game-ready image assets through Codex Sol

Read `references/game-asset-contract.md` and `references/image-asset-workflow.md`.

This route is hard-pinned:

```text
engine: codex
model: gpt-6.1-sol
```

Resolve it with `scripts/game_asset_router.py --task-kind asset-image --json`. Do not substitute Claude, Luna, Astra, or a different Codex model because of normal model-policy economics. If Codex or GPT-6.1 Sol is unavailable, return `GAME_ASSET_ROUTE_BLOCKED`.

Before generation, make the artifact contract explicit: purpose, dimensions/aspect ratio, transparency, style constraints, engine target, source/export paths, and any tiling/atlas requirement. Reuse repository art direction when present.

With `--apply`, actual image creation belongs to the Codex specialist worker. Give it only the bounded brief, relevant visual references/pointers, allowed paths, and verification/export requirements. Keep Codex memory disabled through the normal Gearbox wrapper.

Verify the resulting files exist, use the requested dimensions/format, preserve transparency/alpha expectations, and are importable by the target engine/toolchain when a credible check exists. Do not claim visual quality from file existence alone; include the smallest useful visual evidence when the host supports it.

Do not overwrite unrelated source art. Keep editable/source form alongside exported runtime form when the workflow supports it.
