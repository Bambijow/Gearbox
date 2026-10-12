# Cross-asset art direction

Art direction keeps independent assets inside one coherent visual world.

## Authority

Reuse an existing ART_DIRECTION.md/style bible when present. Otherwise derive direction from approved game/product references and repository assets. Only create/update durable art-direction documentation when explicitly requested or when the repository already treats it as canonical.

## Contract

Record applicable:

- visual thesis / emotional register;
- shape and silhouette language;
- proportion/exaggeration rules;
- palette and value hierarchy;
- material/surface language;
- line/edge/detail density;
- texture resolution/style;
- lighting and shadow language;
- camera/perspective assumptions;
- icon/UI relationship;
- VFX/motion character;
- 2D/3D translation rules;
- forbidden/anti-reference patterns;
- target platform/readability constraints.

## Cross-asset audit

Compare a set, not isolated beauty:

- silhouettes read as one family;
- detail density is compatible;
- material roughness/specular/texture language does not randomly change;
- lighting assumptions do not conflict;
- UI/icons/sprites/models share intentional visual DNA;
- generated assets do not drift toward unrelated model defaults;
- asset scale/perspective/camera assumptions align.

## Classification

- `COHERENT`
- `DRIFT`
- `INTENTIONAL_VARIANT`
- `BLOCKED`

Intentional variant needs an explicit narrative/gameplay reason.

## Gate

Return:

```text
ART_DIRECTION_GATE: PASS | REPAIR | BLOCKED
```

When asset skills run under a known art-direction contract, they must cite which rules they inherit and which they intentionally vary.
