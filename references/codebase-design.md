# Codebase design vocabulary

Use this only when a change materially alters a shared interface, seam, dependency direction, or architectural module. Ordinary feature work does not need an architecture ceremony.

## Vocabulary

**Module**: implementation hidden behind one caller-facing interface.

**Interface**: everything callers must know to use the module correctly: types plus invariants, ordering, errors, config and meaningful performance constraints.

**Seam**: the location where behavior can vary without editing the caller.

**Adapter**: a concrete implementation occupying a seam.

**Depth**: useful behavior/leverage delivered per unit of interface callers must learn.

**Locality**: how strongly related behavior/change/verification stays concentrated instead of leaking across callers.

## Design tests

### Deletion test

Imagine deleting the proposed module.

- if complexity largely disappears, the module may be a pass-through/shallow wrapper;
- if the complexity reappears across many callers, the module is earning its depth.

### Seam reality

One adapter is usually a hypothetical seam. Two real variants are evidence of a real seam. Avoid interfaces created only for imagined futures.

### Test surface

The public interface should also be the natural stable test surface. Needing to bypass it routinely is evidence the module may be the wrong shape.

## Design-it-twice gate

Use parallel alternative designs only when all are true:

- the interface is shared or hard to reverse;
- the decision materially affects architecture/testability;
- reasonable designs differ.

For `deep` risk, generate 2 materially different proposals. For `exceptional`, up to 3.

Give each proposer a different constraint, for example:

- minimize the interface / maximize depth;
- maximize extensibility for known variants;
- optimize the common caller.

Compare by **depth**, **locality**, **seam placement**, migration cost and verification surface. Pick one. Do not carry all abstractions forward.

Do not use design-it-twice for routine functions/classes or trivial refactors.
