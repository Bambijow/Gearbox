# Gearbox on Antigravity

Gemini is the primary orchestrator; Claude Code is the independent architecture challenger, creative director and reviewer. Main control-plane must not write product files. Use `scripts/gemini_claude_router.py` to select Gemini/Claude, then isolated worktrees and approved worker packets. No previous provider runtime calls in Antigravity mode.

Before invoking a legacy skill, read its `SKILL.md` and the relevant Gearbox references. Legacy previous provider or Claude-only orchestration instructions are not executable here until adapted; report `MIGRATION_BLOCKED` rather than silently bypassing capabilities or review policy.

For 3D require actual Blender/Godot access on the Gemini worker and an independent review. Confirm model IDs with `agy models`; defaults in the new router are candidates, not proof of availability. Never use `--dangerously-skip-permissions`. Check `/hooks` for the native guard before running an orchestrated skill. If missing, block.

For independent Claude review, dispatch `python3 scripts/claude_review_worker.py` from a fresh, clean review worktree with a focused prompt. This is read-only (`--permission-mode plan` and read-only tool allowlist), and checks repository integrity after execution. Do not reuse the Gemini producer's conversation.

## Architecture decision routing

For ordinary/reversible architecture or domain-modeling questions, prefer Gemini Neon. For `risk=critical` or `complexity=high`, route the primary design to configured Gemini Carbon (`frontier`) and require a fresh independent Claude Opus adversarial review before acceptance. The reviewer challenges assumptions, invariants, alternatives, migration/rollback and operational consequences. Gearbox adjudicates using specs, code and tests, not model agreement. If Claude is unavailable, block critical approval, never silently skip the second opinion. Gemini 4 model identifiers in the preview are illustrative: verify installed IDs with `agy models` and persist explicit overrides before live execution.
