# Lean implementation-plan contract

A Gearbox plan records **decisions the implementer cannot safely make alone**. It is not a transcript of the code that will be written.

The reader is a capable engineer/worker who can write idiomatic implementation once the interface, constraints, evidence seam and exact product values are known.

## Task content

Each task contains only what makes one reasonable implementation unambiguous:

- outcome/spec slice;
- exact files or well-supported touch points;
- interfaces consumed/produced;
- exact signatures or externally-fixed values when the design pins them;
- ownership and shared seams;
- dependencies and `ready_when`;
- context pointers;
- test names/assertions or acceptance probes;
- verification command and what passing means;
- migration/rollback constraints when material.

Do not write function bodies that the signature + tests + repository patterns already determine. Include pseudo-code/body detail only when the algorithm itself is a settled design decision that otherwise has multiple materially different interpretations.

Do not write vague placeholders such as “handle edge cases”, “add validation”, “write tests”, or “TBD”. Either name the decision/assertion or leave it to the capable implementer when it is not a product/architecture decision.

## Review Focus

Every non-trivial plan has one `## Review Focus` section with **0-5** input classes or failure modes most likely to hurt a real user/system but not already obvious from the happy-path task descriptions.

For each item:

- name the condition/input;
- state the expected safe behavior;
- ensure the owning task gets a test/probe when the behavior is testable.

An empty section means the planner checked and found none.

Do not invent requirements unrelated to the accepted spec. Review Focus closes plausible failure surfaces implied by the requested behavior; it does not authorize product expansion.

## Proportion self-check

After drafting:

1. every spec requirement maps to a task/check;
2. every task exists for a requirement, risk reduction, or necessary enabling dependency;
3. later tasks use the same signatures/interfaces earlier tasks produce;
4. Review Focus items map to an owner/check;
5. compare plan size to spec size.

If the plan is several times longer than the spec and code blocks dominate, it is probably implementing in prose. Replace bodies with signatures, assertions, exact values and pointers until it is lean without becoming ambiguous.

For persisted plans, run `scripts/plan_guard.py` when a spec path is available.
