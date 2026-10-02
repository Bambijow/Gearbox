# Gearbox contract evals

These scenarios are regression contracts for orchestration behavior, not benchmark theater. Run Gearbox against a fixture/repository, then check the resulting run directory with:

```bash
python3 scripts/eval_contract.py evals/simple-bug/scenario.json .gearbox/runs/<run-id>
```

The suite covers simple bugs, cross-file features, UI evidence, migrations/human gates, post-PR CI repair, Codex failure, conflicting workers, stale solution memory, Ponytail regressions, and hostile issue text. Expand scenarios when a real failure teaches a new orchestration invariant.

## Spec clarification blocker

`spec-clarification-block/` covers an issue whose material product semantics cannot be inferred from the repository. The expected contract is `BLOCKED` at `SPEC` with `SPEC_BLOCKED`, zero implementation/review dispatches, and persisted clarification questions.

- `orchestrator-no-code`: parent control plane cannot author product files; delegated mutation invariant remains present in run state.
