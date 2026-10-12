# Context compilation

Worker context is compiled, not improvised.

## Structured source

Before a substantial worker/reviewer dispatch, create a compact JSON task descriptor containing only:

- role;
- outcome;
- exact spec/acceptance slice;
- cross-task constraints that truly bind this unit;
- one bounded task;
- dependency facts already proven;
- consumed/produced interfaces;
- required capabilities;
- owned/forbidden paths;
- pointers to source/glossary/ADR/research/solution/design artifacts;
- verification commands;
- focused failure modes;
- output contract.

Do not paste source files, full plans, research transcripts, successful logs or whole conversations into this descriptor.

## Compile

Use:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/context_compiler.py" \
  --input ".gearbox/runs/<run>/tasks/<id>/context.json" \
  --output ".gearbox/runs/<run>/tasks/<id>/worker-packet.md" \
  --manifest ".gearbox/runs/<run>/tasks/<id>/worker-packet.json" \
  --max-bytes <budget>
```

The manifest records the exact packet hash and byte size. Feed the compiled packet, not a newly rewritten prompt, to the worker.

## Pointer discipline

Pointers are cheap until needed. A worker reads a pointed artifact only when the assigned task requires it.

Prefer:

```text
docs/adr/007.md — canonical retry ownership
src/billing/types.ts — PaymentAttempt public contract
```

over pasting either file into the packet.

## Repair packets

A repair receives:

- original packet pointer/hash;
- canonical finding;
- repair strategy;
- delta evidence;
- affected ownership/verification.

Do not resend broad discovery context unless the finding proves the old packet lacked a required fact.

## Benefit

Compilation provides:

- deterministic handoffs;
- prompt byte budgets;
- stable dispatch fingerprints;
- less repeated context;
- easier forensic comparison when a worker goes off-scope.
