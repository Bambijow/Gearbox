# Game asset contract

Game assets are production artifacts, not chat illustrations. Every game-asset task must make the asset contract explicit before generation.

## Required fields

Capture the applicable fields:

- gameplay/UI purpose and visual brief;
- target engine and import path;
- editable source path plus runtime export path;
- dimensions/resolution or real-world scale;
- transparency/background rules;
- palette/style/art-direction pointers;
- animation states/frames when applicable;
- texture/material budgets;
- poly/triangle, LOD, collision and rigging budgets for 3D;
- naming conventions and owned paths;
- verification/import command or manual probe.

Prefer repository-native conventions over inventing a second asset pipeline.

## Source + export

When the tool supports an editable source format, keep it alongside the runtime export unless repository policy says otherwise:

- Aseprite source + PNG/sprite sheet;
- Blender source + glTF/GLB/engine-native export;
- layered/source image + runtime texture/image.

Do not silently replace source art with only a flattened export.

## Asset safety

Do not overwrite unrelated artist-authored files. Keep generated changes inside owned paths. Do not embed credentials, private URLs or licensed source material into artifacts or metadata.

## Evidence

File existence proves packaging, not visual correctness. Record the smallest useful evidence available: dimensions/metadata, engine import result, viewport/render screenshot, frame manifest, geometry/UV/material checks, or asset-review verdict.

## Routing invariants

Specialist routes are hard constraints:

- image asset -> Codex GPT-6.1 Sol;
- pixel art -> Codex GPT-6.1 Sol, Aseprite MCP preferred;
- 3D creation -> Claude Opus 5.5;
- 3D review -> GPT-6 Astra.

Normal `auto`, `claude-heavy`, `codex-heavy`, `--no-codex` and economy routing do not override these. An unavailable forced route blocks instead of degrading silently.
