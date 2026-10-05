# Targeted test hardening

Use hardening after ordinary correctness tests are green and only where false confidence would be expensive.

## Choose the invariant first

State the rule independently of the implementation, for example:

- a tenant never observes another tenant's data;
- debits and credits preserve balance;
- parser round-trips preserve canonical meaning;
- state transitions reject invalid edges;
- authorization depends on the resource owner, not request-controlled metadata.

If no independent invariant can be stated, property testing will likely generate noise.

## Mutation testing

Prefer targeted mutations at the seam under test:

- invert/remove a condition;
- change a boundary comparison;
- skip an authorization guard;
- return stale/default data;
- omit a persistence/update step;
- change ordering/deduplication;
- drop an error path;
- alter a parser branch.

A surviving meaningful mutant means the existing tests failed to distinguish a plausible wrong program. Equivalent mutants and impossible states should be documented and excluded, not "killed" with brittle assertions.

Run the smallest supported mutation scope. Repository-wide mutation by default is wasteful.

## Property-based testing

Use properties when many examples instantiate the same rule. Good properties have an oracle independent from the implementation and useful shrinking/minimization.

Avoid tautologies such as comparing a function to itself through another wrapper.

## Fuzzing

Use bounded fuzzing for parsers/protocol decoders/serializers/state machines/input validators when crashes, hangs or invariant violations have a clear oracle. Keep corpus, seed/time budget and reproduction artifacts when a failure is found.

## Exit

Hardening is sufficient when high-value plausible mutants die, important properties hold under generated examples, and failures are reproducible. More test volume without a new failure model is not automatically more confidence.
