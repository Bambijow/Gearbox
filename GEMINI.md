# Gearbox on Antigravity

Gemini is the primary orchestrator; Claude Code is the independent architecture/creative specialist and reviewer. Main control-plane must not write product files. Use `scripts/gemini_claude_router.py` to select Gemini/Claude, then isolated worktrees and approved worker packets. No Codex runtime calls in Antigravity mode.

Before invoking a legacy skill, read its `SKILL.md` and the relevant Gearbox references. Legacy Codex or Claude-only orchestration instructions are not executable here until adapted; report `MIGRATION_BLOCKED` rather than silently bypassing capabilities or review policy.

For 3D require actual Blender/Godot access on the Gemini worker and an independent review. Confirm model IDs with `agy models`; defaults in the new router are candidates, not proof of availability. Never use `--dangerously-skip-permissions`. Check `/hooks` for the native guard before running an orchestrated skill. If missing, block.
