# Design influences and integrations

Gearbox is an original implementation influenced by public engineering-agent projects:

- Matt Pocock's `mattpocock/skills`: small composable engineering moves, deliberate specification, implementation discipline, debugging, and review.
- Every's `EveryInc/compound-engineering-plugin`: explicit engineering loops, multi-step orchestration, shipping/handoff workflows, and capturing reusable lessons back into the repository.
- Jesse Vincent / obra's `obra/superpowers`: evidence-before-completion, bounded fresh-agent SDD, task-scoped review, systematic debugging, and the newer token-efficient pattern of one task reviewer producing separate spec-compliance and code-quality verdicts.
- Dietrich Gebert's `DietrichGebert/ponytail`: an MIT-licensed minimalism/simplification discipline. Gearbox can call an installed Ponytail plugin as an independent post-integration simplification gate.

The Gearbox skill text and orchestration code were written specifically for Gearbox rather than copied from these projects. Superpowers concepts are re-expressed as Gearbox policies rather than vendoring its skill prompts.

Ponytail is not bundled in this repository. Install it separately when you want Gearbox's `/simplify` phase to use the actual Ponytail plugin; otherwise Gearbox uses its own fallback simplification checklist.
