---
name: review
description: "Cross-review a diff, branch, PR, or completed plan for requirement coverage, correctness, security, regressions, tests, operational risk, and post-simplification architecture."
argument-hint: "[diff, branch, PR, plan, or scope]"
disable-model-invocation: true
---

# Review the post-simplification change

Review the actual code and requirements, not a hypothetical implementation. For autonomous issue work, this phase runs after `/simplify`.

## Establish scope

Read repository instructions, `.gearbox/config.md` when present, the originating spec/issue/plan, and the full relevant diff. Inspect surrounding code when changed behavior depends on it.

If the change is substantial, launch Gearbox's read-only `cross-reviewer` agent. For any optional reviewer beyond mandatory configured gates, apply `references/delegation-gate.md`; independent judgment must justify the extra dispatch. For issue workflows, pair it with at most one independent read-only Codex worker as the different-model lens when the risk warrants it. Reconcile them centrally. The Claude reviewer should cover requirement compliance plus correctness/security/data-integrity/compatibility/tests/operations in one pass rather than spawning one reviewer per category.

Do not outsource final judgment to any reviewer.

## Finding standard

Apply `references/review-calibration.md` and `references/test-credibility.md`. A material finding must be actionable and supported by a concrete reachable failure path, requirement mismatch, credible verification gap, or maintainability hazard with real future cost. Avoid generic style commentary.

Classify findings:

- **Blocker**: likely correctness, security, data-loss, severe compatibility, or production-safety issue.
- **Important**: meaningful bug/regression risk or material requirement gap.
- **Minor**: directly relevant cleanup with modest impact.
- **Advisory**: useful hardening/rollout/observation that does not make the change incorrect if left as-is.

For each finding include location, evidence/failure path, consequence/failure cost, smallest useful fix direction, and action ownership (`repair|human|release|advisory`).

## Cross-review behavior

When running multiple reviewers, keep their prompts independent enough that one review does not anchor the others. Compare findings after they return. Agreement increases confidence but does not prove correctness; disagreement should be resolved against code, tests, and spec. Do not ask a reviewer to crawl the entire repository by default: start from the final requirements, diff, changed files, and direct dependencies, then expand only on a concrete suspicion.

For Codex review, use a fresh `--ephemeral` read-only run and require structured findings, preferably via `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/codex_worker.py" --kind review ...`. Do not let the reviewer edit the integration tree. Pass compact requirements and refs/paths instead of replaying the implementation conversation or successful test logs.

## Verification audit

Map every acceptance criterion to tests/manual evidence. Distinguish "not tested" from "tested at another seam". Verify UI/UX evidence when visible behavior changed.

If there are no material findings, say so and still state what was inspected and what could not be verified.
