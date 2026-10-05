# Auxiliary delegation gate

Gearbox delegates product mutation because the control-plane boundary requires it. This gate is for **auxiliary analysis/judgment subagents**, not mandatory implementation, opposite-provider task review, integration, verification, knowledge-curation, simplification, or shipping roles.

Before dispatching an auxiliary subagent, name exactly why delegation pays for itself. At least one reason must apply:

1. **Flood protection** — the agent must read materially more context than it returns, and the parent will not need the raw material afterward.
2. **Independent judgment** — fresh context is part of the product: review, verification, alternative design, judging, adversarial analysis.
3. **Parallel unit** — a substantial independent question can run concurrently without shared mutable state.
4. **Selectable model** — the harness can genuinely route this work to a model/provider whose different cost/capability is useful.

If none applies, do the read-only reasoning in the current owner context instead of dispatching another agent.

## Broken dispatches

Do not dispatch an agent to recover information that exists only in the parent's conversation unless the packet explicitly carries the needed decision/fact. A fresh agent cannot “extract the conversation” it never received.

Do not dispatch when the parent will immediately reread the entire raw result. That pays both contexts. Prefer a file artifact plus a short result pointer when flood protection is the reason.

Do not dispatch a second agent merely because the first agent's output is inconvenient. Fix the packet, tool access, route, or ownership problem.

## Dispatch record

For every auxiliary dispatch, record one compact line in the run artifact or DAG:

```text
dispatch_reason: flood-protection | independent-judgment | parallel-unit | selectable-model
expected_return: <artifact/pointer/verdict>
```

Multiple reasons may apply, but one concrete reason is enough.

## Typical Gearbox mappings

- `researcher`: usually flood protection; sometimes parallel unit.
- `design-proposer`: independent judgment, often parallel unit.
- extra repo-research agent: only when flood protection or true parallel discovery applies.
- extra reviewer beyond the mandatory hybrid/task/final gates: independent judgment only when the risk justifies the additional spend.
- `domain-curator`: not an auxiliary analysis dispatch when it owns an accepted durable mutation.
- implementation workers: excluded from this gate; the control-plane rule already mandates worker ownership.
