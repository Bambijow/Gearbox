# Behavioral evals

These scenarios test prompt behavior that deterministic state/file validators cannot see.

Normal CI **validates the scenarios and harness only**. It never spends model tokens.

To run one scenario against a model CLI, provide a command that reads the assembled eval prompt from stdin:

```bash
GEARBOX_EVAL_CLAUDE_CMD='<your Claude runner reading stdin>' \
  python3 scripts/behavior_eval.py run evals/behavior/plan-lean.json --provider claude

GEARBOX_EVAL_CODEX_CMD='<your Codex runner reading stdin>' \
  python3 scripts/behavior_eval.py run evals/behavior/plan-lean.json --provider codex
```

Outputs land under `.gearbox/evals/` by default. Provider command syntax is deliberately not hard-coded because harness CLIs evolve independently of Gearbox.

Use this lane after behavior-bearing changes to skills/references, or in a scheduled/local eval campaign. Keep scenarios small, non-destructive and discriminating.
