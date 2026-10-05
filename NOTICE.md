# Design influences and integrations

Gearbox is an original implementation influenced by public engineering-agent projects:

- Matt Pocock's `mattpocock/skills`: small composable engineering moves, deliberate specification, Wayfinder-style decision mapping, isolated primary-source research, domain glossaries/ADRs, tight debugging loops, ready-frontier implementation scheduling, PR evidence/merge-danger framing, and writing-for-agents/context-pointer discipline.
- Every's `EveryInc/compound-engineering-plugin`: explicit engineering loops, multi-step orchestration, shipping/handoff workflows, durable learnings, subagent-dispatch economics, failure-cost review calibration, systemic debugging/defense-in-depth, solution retirement conditions, trustworthy agent-facing test loops, prompt-budget ratchets, and behavioral/conversation eval discipline.
- Jesse Vincent / obra's `obra/superpowers`: evidence-before-completion, bounded fresh-agent SDD, task-scoped review, systematic debugging, lean decision-oriented plans, Review Focus, same-shape task batching, plan-scoped repair ledgers/circuit breakers, credible/falsifiable tests, forensic session diagnosis, evidence reuse over redundant reruns, and bounded child-wait reconciliation.
- Dietrich Gebert's `DietrichGebert/ponytail`: an MIT-licensed minimalism/simplification discipline. Gearbox can call an installed Ponytail plugin as an independent post-integration simplification gate.

The Gearbox skill text and orchestration code were written specifically for Gearbox rather than copied from these projects. Superpowers concepts are re-expressed as Gearbox policies rather than vendoring its skill prompts.

Ponytail is not bundled in this repository. Install it separately when you want Gearbox's `/simplify` phase to use the actual Ponytail plugin; otherwise Gearbox uses its own fallback simplification checklist.
