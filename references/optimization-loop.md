# Measured optimization loop

Optimization is an experiment loop with correctness guardrails. The result is a measured delta, not a persuasive code review.

## Define the experiment

Before editing, record:

- primary metric and units;
- representative workload/input;
- command/harness and environment assumptions;
- sample count/warmup when relevant;
- correctness and safety checks that must remain green;
- budget: attempts, time, acceptable complexity/operational cost.

Prefer end-to-end or production-representative measurements. Micro-benchmarks are useful only when they isolate a demonstrated bottleneck.

## Baseline

Run the same measurement more than once when variance is plausible. Keep raw values, not only the best number. Note cold/warm cache, concurrency, fixture size and machine/runtime details that materially affect comparison.

If the baseline is unstable enough that the expected gain cannot be distinguished from noise, fix the benchmark before touching product code.

## Hypothesis

Write one sentence:

`Changing X should move metric Y because mechanism Z dominates the measured workload.`

Reject hypotheses that merely say code will be "cleaner" or "more efficient".

## Variant discipline

Prefer one material change per variant. For each variant:

1. implement the smallest change;
2. run guardrails;
3. measure with the same harness;
4. compare distributions/runs honestly;
5. keep, revert, or mark inconclusive.

A variant loses if it improves the primary number by moving unacceptable cost into memory, reliability, startup, network, operator complexity, security or another user-visible dimension.

## Decision

Report baseline, variant measurements, relative/absolute delta, guardrails, caveats and the exact kept change. Do not overstate statistical confidence from tiny samples.

Stop when the target is achieved, the remaining bottleneck moves elsewhere, the experiment budget is exhausted, or the next hypothesis requires an architectural/product decision.
