# Pixel art workflow

Pixel art is a constrained production medium. Exact dimensions and palette behavior matter more than a generic stylistic resemblance.

## Preferred path: Aseprite MCP

When capability `aseprite` is live, use it as the required MCP through the Codex GPT-6.1 Sol worker. Preserve editable `.aseprite` source and export PNG/sprite-sheet artifacts.

Pin:

- sprite/tile dimensions;
- palette or maximum palette size;
- transparent/background index;
- directions/states;
- frame count and timing;
- onion-skin/loop expectations when applicable;
- origin/pivot convention;
- sprite-sheet ordering and padding.

Use integer coordinates and nearest-neighbor-safe transforms. Avoid accidental anti-aliasing, blur, fractional scaling and palette drift.

## Fallback path

If Aseprite is unavailable, route still remains Codex GPT-6.1 Sol using direct image generation. The fallback must still obey exact target dimensions. Do not accept a large raster that merely imitates pixel art.

## Verification

Verify each frame/tile dimension, frame order, transparency, palette constraints, edge continuity for tiles, animation loop/readability and target-engine import settings. For sprite sheets, record the frame grid explicitly.
