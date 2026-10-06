# 3D asset review checklist

The reviewer is GPT-6 Astra and is read-only. Review the real asset through Blender or Godot capability when available; screenshots alone are insufficient when geometry/tool inspection is possible.

## Geometry and transforms

- scale/units match the contract;
- origin/pivot and axes are correct;
- transforms are applied/normalized as required;
- normals/tangents and shading are sane;
- topology is appropriate; non-manifold/duplicate/degenerate geometry is addressed where relevant;
- triangle/poly budget is respected.

## UVs, materials and textures

- UVs are present and suitable for the material workflow;
- unintended overlaps/stretching are absent or justified;
- material slots/names are stable;
- texture size/count and color-space/import expectations are within budget;
- missing/broken texture references do not survive export.

## Game integration

- runtime export imports successfully;
- scene hierarchy/naming is usable;
- collision/LOD requirements are present;
- pivots/sockets/bones line up with gameplay needs;
- rig/weights/animations are coherent where applicable;
- engine scale/orientation and material conversion are correct.

## Review result

Return `PASS`, `REPAIR`, or `BLOCKED`. Findings must name the concrete object/material/bone/node/path when possible and explain runtime or production consequence. Aesthetic preference is not a blocker unless it violates the supplied art direction or gameplay/readability contract.
