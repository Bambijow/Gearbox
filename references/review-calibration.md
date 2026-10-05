# Review calibration by failure cost

A review finding exists to prevent a concrete cost, not to reward maximal defensiveness.

Before creating a material finding, state:

1. the reachable failure path or accepted-requirement mismatch;
2. who/what is affected;
3. what the failure costs if it lands;
4. the smallest useful remedy or decision.

If those cannot be stated, downgrade to advisory or omit it.

## Severity

- **Blocker** — likely exploitable security issue, data loss/corruption, severe correctness/compatibility break, destructive operational failure, or explicit critical requirement violation.
- **Important** — concrete meaningful user/system regression or material acceptance gap that should be fixed before merge.
- **Minor** — localized maintainability/test/readability issue with low failure cost.
- **Advisory** — useful observation, rollout note, or possible hardening whose absence does not make the change incorrect.

## I/O and defensive checks

Do not flag every missing validation/timeout/retry merely because it could exist.

Raise it when at least one is true:

- the accepted contract requires it;
- a reachable caller/input can trigger a harmful failure before another guard catches it;
- adding it later would be expensive because it touches stored data, money, security, or a public/shared interface.

A downstream guard that already catches the failure counts. Instructions telling a human to avoid the failure do not.

## Action ownership

Findings may declare:

- `repair` — bounded code/test change;
- `human` — product/architecture judgment required;
- `release` — rollout/operational follow-up;
- `advisory` — no merge-blocking action.

The reviewer proposes; the orchestrator validates the finding against code/spec/evidence before acting.
