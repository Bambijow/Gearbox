# Decision evidence, uncertainty and adversarial development

Reuse the existing Gearbox control plane, clarification blocker, context compiler, review and quality gates. These small deterministic helpers supplement them; they are not a second orchestrator or a second test truth.

## 1. Decisions and invalidation

Keep only material decisions (source fact, hypothesis, or explicitly accepted target choice) in a compact JSON ledger. `scripts/decision_trace.py --input <ledger.json>` validates evidence files by SHA-256 and a common source fingerprint, checks dependency references/cycles and reports the impacted decisions and tasks when an evidence ID is invalid or changed (`--changed-evidence E1`). The input contains `schema_version:1`, `run_id`, `source_fingerprint`, `evidence:[{id,path,sha256,source_fingerprint}]`, and `decisions:[{id,statement,kind,decision_reason,falsifier,evidence_ids,depends_on,affected_tasks,approval_pointer?}]`. `approved-target` requires a genuine accepted-spec pointer; the helper **cannot validate human intent itself**.

Do not replace the verified file with a different digest and claim its old conclusion persists. After changes to the source capture, oracle or destination, recalculate only affected claims/tasks. `VERIFIED_LEDGER` attests file integrity and graph consistency, not semantic truth. Keep the ledger small; rely on context pointers and existing run state rather than re-reading histories.

## 2. Separate risk from uncertainty

Risk measures **consequence if wrong**; uncertainty measures **insufficient knowledge**. An unknown but low-consequence integration may need a cheap probe; a well-understood critical data migration still needs critical quality gates. Use `scripts/investigation_plan.py --input <plan.json>` with explicit `risk: low|medium|high|critical`, `uncertainty: known|partial|high|blocked`, `hypotheses` IDs, `probes:[{id,cost,predictions:{hypothesis_id:observable_result}}]`, `probe_budget`, and optional `blocking_product_questions`.

A deterministic plan selects at most **one** affordable probe that predicts different observable results for competing hypotheses. It never invents probabilities; run the probe only under existing approvals and then reclassify on actual evidence. A budget/availability gap becomes `EVIDENCE_BLOCKED`. Product-semantic questions become `HUMAN_BLOCKED`, never guessed through auto mode. `required_quality_floor` is a one-way minimum and does not drop as uncertainty decreases. A technical reconnaissance before plan approval may justify an explicit lighter planning route but cannot remove user-required gates.

## 3. Adversarial contract challenge

On transfer/migration work, independently test what would make the reconstructed contract **wrong**. Before a reviewer reads the implementer's rationale, supply the accepted reference contract, independent reference evidence pointers, candidate revision and failure modes. For each material claim seek an input likely to falsify it, then attach a real run/test artifact from the candidate. Capture status `COUNTEREXAMPLE`, `NO_COUNTEREXAMPLE_OBSERVED`, or `UNKNOWN`; record the actual `evidence.path` and `evidence.sha256` (relative to report directory).

`python3 scripts/contract_challenge.py --contract contract.json --report challenge.json` checks source/target binding, challenge-to-claim coverage and file hashes. Returns `REPAIR` on a counterexample, `GAPS` on untested claims, `BLOCKED` on invalid/stale evidence and `REVIEWED_NOT_PROVEN` on a complete bounded challenge. It **never** proves universal equivalence. The verifier owns execution; a reviewer is read-only. Use a fresh reviewer only where the gate or independent judgment justifies it, not for every routine edit. For material behavioral transfer, final review requires explicit `--behavior-transfer --contract-challenge-status ...`; missing evidence never selects lite review.

## 4. Evaluation

Keep deterministic validation in normal CI. Use `evals/behavior/` for prompt-contract scenarios and the existing isolated agentic benchmark runner for real comparisons: baseline without these changes, API reverse only, full candidate. Pin reference captures/target revisions; measure correction/failure rate, missing assumptions, real proof coverage, accidental live network writes, cost/latency and repair loops. Only compare economics after correctness and safety both pass. A validated eval JSON or green Python test is not a model-run benchmark result.
