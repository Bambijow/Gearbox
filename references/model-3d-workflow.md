# Game-ready 3D modeling workflow

3D creation is performed only by the dedicated Claude Opus 5.5 specialist. Actual modeling requires a live Blender or Godot capability.

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

## Tool choice

Prefer Blender MCP for general modeling, UVs, materials, rigging and export. Godot may be used for engine-native scene/procedural geometry tasks. If neither is available, block rather than returning a textual concept as a finished model.

## Modeling discipline

Keep topology appropriate to deformation and shading needs. Apply/normalize transforms where required by the target pipeline. Check normals, manifold expectations, material slots, UVs, pivots and scale. Avoid hidden high-poly or texture cost that violates the budget.

## Export and import

Preserve editable source when practical. Export to the repository's runtime format and perform a credible target-engine import/probe. Verify orientation, scale, materials, animation/rig, collision and hierarchy survive export.

## Mandatory review

Every completed 3D asset passes the GPT-6 Astra `review-3d` gate before it is asset-ready.
