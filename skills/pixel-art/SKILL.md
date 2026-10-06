---
name: pixel-art
description: "Create or edit game-ready pixel art through Codex GPT-6.1 Sol. Prefer the local Aseprite MCP when capability `aseprite` is available; otherwise use direct Sol generation. Use for sprites, tiles, icons, sprite sheets, frame animation, palettes, and pixel-art cleanup."
argument-hint: "[brief/spec/scope] [--apply]"
disable-model-invocation: true
---

# Pixel art: Aseprite first, Codex Sol always

Read `references/game-asset-contract.md` and `references/pixel-art-workflow.md`.

The model route is hard-pinned to Codex GPT-6.1 Sol. Resolve it with `scripts/game_asset_router.py --task-kind pixel-art` plus the live capability set.

If Aseprite is available, generation/editing MUST use it as the required MCP capability. If it is unavailable, fall back to direct GPT-6.1 Sol image generation, not to another provider/model. If neither path is executable, return `GAME_ASSET_ROUTE_BLOCKED`.

Before work, pin sprite/tile dimensions, palette constraints, transparency, frame count/timing, directions/states, pivot/origin convention, source/export paths, and target engine import expectations.

With Aseprite, preserve an editable `.aseprite` source plus exported runtime PNG/sprite-sheet outputs when applicable. Avoid accidental anti-aliasing, sub-pixel transforms and palette drift. Verify frame dimensions/order and nearest-neighbor-friendly output.

With direct Sol generation, verify that the result still obeys exact pixel dimensions and pixel-art constraints; do not accept merely "pixel-art-looking" high-resolution imagery.
