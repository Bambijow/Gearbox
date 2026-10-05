# Finding-scoped repair policy

Repair loops converge on **findings**, not on vague “try again” cycles.

Each validated repairable finding gets a stable id such as `REV-004` and a compact record in `state.json.repair_findings`.

Use `scripts/repair_findings.py` before each repair dispatch.

## Attempt policy

Default policy:

- attempts 1-2 may use the same strategy when new evidence justifies iteration;
- a third dispatch with the same strategy is blocked: re-diagnose, split the task, change the evidence seam, provider, model, or implementation approach;
- after 5 total repair attempts for one finding, stop automatic repair and require controller adjudication;
- a repaired finding gets a **scoped re-review** of the finding + delta, not a full task replay;
- broad final re-review runs only if the repair changed the broader risk surface.

“Same strategy” means materially the same ownership/approach/evidence route, not merely the same model name.

## Controller adjudication

At the breaker, classify the remaining finding:

- **load-bearing** — concrete correctness/security/data/accepted-requirement failure: replan/escalate or block;
- **human decision** — requires product/architecture intent: block with the decision needed;
- **advisory** — improvement whose absence does not make the change wrong: record residual risk and stop repairing;
- **invalid/stale** — evidence disproves the finding: close it with the ruling.

Never burn repair budget indefinitely because a reviewer prefers another style.
