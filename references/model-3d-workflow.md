# Game-ready 3D modeling workflow

Claude Opus 5.5 directs 3D creation. Codex GPT-6.2 Astra/high executes substantive Blender/Godot modeling under an explicit packet. A live Blender or Godot capability **on Codex** is mandatory. Do not silently fall back to Sol or Claude-only tools.

## Asset contract

Pin before modeling:

- gameplay purpose and silhouette/readability requirement;
- target engine;
- unit/scale convention;
- source and export format/path;
- triangle/poly budget;
- texture resolution/material budget;
- pivot/origin and forward/up axes;
- UV requirements;
- collision, LOD, rigging, animation and socket/bone needs;
- naming and hierarchy conventions.

## Ownership and delegation

Opus owns the choices that are expensive to misunderstand:

- art direction and silhouette;
- topology strategy when deformation/shading matters;
- rig/skeleton architecture;
- ambiguous material/look decisions;
- asset acceptance against gameplay/readability.

Codex Astra/high owns substantive executable 3D work:

- blockout from exact dimensions/reference constraints;
- repetitive geometry or variants;
- UV unwrap/packing with stated constraints;
- material slot assignment and texture wiring;
- collision and LOD generation;
- deterministic cleanup/transforms;
- baking/export/import loops.

Opus writes an exact tool packet and checks the resulting source/export/evidence. A Codex-side Blender/Godot capability is required even when Claude also has one. Tiny non-geometry metadata/rename work can remain on Sol as a separate cheap task; never use Sol as a fallback for modeling.

## Tool choice

Prefer Blender for general modeling, UVs, materials, rigging and export. Godot is valid for engine-native scene/procedural geometry. If neither provider has a usable 3D capability, block rather than returning a textual concept as a finished model.

## Modeling discipline

Keep topology appropriate to deformation and shading needs. Apply/normalize transforms where required. Check normals, manifold expectations, material slots, UVs, pivots and scale. Avoid hidden high-poly or texture cost that violates the contract.

## Export and import

Preserve editable source when practical. Export to the repository's runtime format and perform a credible target-engine import/probe. Verify orientation, scale, materials, animation/rig, collision and hierarchy survive export.

## Mandatory review

Every completed 3D asset passes a **fresh, independent** GPT-6.2 Astra `review-3d` session before it is asset-ready. Do not reuse the producer's context or self-review.
