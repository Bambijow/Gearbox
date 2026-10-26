# Focused independent skill semantic review

Run for **behavior-bearing changes** to agent instructions: triggering, ordering, permissions, tool use, escalation, output schema, or safety boundaries. Typo fixes and purely mechanical reference moves can skip with an explicit reason.

After editing, delegate a **read-only fresh reviewer** with the before/after diff, original intent, impacted callers, relevant referenced documents and 2–3 caller-shaped situations. Do not let the author of the rewrite self-certify meaning. The reviewer must report:
- preserved requirements;
- weakened, strengthened, inverted or ambiguous obligations, each with exact before/after excerpts;
- new collisions with nearby skills;
- tests needed to distinguish intended behavior from a superficially plausible but wrong execution.

Block acceptance of a high-impact semantic drift until corrected or approved by a human. Prefer targeted scenario evaluation over increasing permanent prose. Run normal plugin validation and byte ratchets afterward.
