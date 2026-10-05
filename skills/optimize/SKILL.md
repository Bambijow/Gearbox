---
name: optimize
description: "Improve an explicit measurable engineering metric with a reproducible baseline, correctness/safety guardrails, bounded hypotheses, one-variable experiments, and evidence-backed keep/revert decisions. Use for latency, throughput, memory, bundle/image size, build time, cost, token usage, or similarly measurable targets."
argument-hint: "[target/metric/scope] [--apply] [--budget N]"
disable-model-invocation: true
---

# Optimize what can be measured

Use this when the system already works and the user wants a measurable engineering property to improve. This is not a cleanup pass and not a license to rewrite architecture because it feels faster.

Read `references/optimization-loop.md`, `references/test-credibility.md`, `references/evidence-reuse.md`, and repository instructions. If an optimization crosses auth, persistence, public contracts, production rollout, or other high-consequence boundaries, preserve the normal Gearbox review route.

## Contract

1. Name one primary metric, workload and measurement command before proposing implementation.
2. Capture a reproducible baseline plus correctness/safety guardrails.
3. State a falsifiable hypothesis and predicted mechanism.
4. Prefer the smallest experiment that isolates the hypothesis.
5. Change one material variable at a time unless variables are inseparable by design.
6. Re-measure under the same workload and environment.
7. Keep only a variant whose gain survives noise and whose guardrails remain green; otherwise revert/decline it.

Never report an optimization from code inspection alone. Never compare unlike workloads, warmed vs cold runs without saying so, or a micro-benchmark that bypasses the real bottleneck.

## Applying changes

Without `--apply`, return the baseline, hypotheses, experiment plan and expected decision rule.

With `--apply`, keep product mutation worker-owned during an active Gearbox run. A direct standalone invocation may execute a bounded experiment, but preserve unrelated changes and record enough evidence to undo a losing variant cleanly.

Stop when the target is met, the budget is exhausted, measurements are too noisy, or further gains require a product/architecture decision not authorized by the user.
