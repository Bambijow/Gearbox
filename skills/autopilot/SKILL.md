---
name: autopilot
description: "Drain a repository's labelled GitHub issue backlog autonomously: each ready issue runs in its own fresh `claude -p` Gearbox loop, and PRs merge only through a gate (all checks green on the exact head, no guarded path touched). Stops on empty backlog, human-needed blockers, pause issue, or budget."
argument-hint: "<GitHub URL | owner/name | local path> [--max-merges N] [--max-hours H] [--queue]"
disable-model-invocation: true
---
# Autopilot: drain the issue backlog

The user invoking this command is the separate merge authorization that `references/post-pr-loop.md` requires. It covers only PRs that pass `scripts/autopilot.py`'s merge gate; never merge any other way.

This main thread is a coordinator only: it does not plan, edit, or review product code. All mechanics live in `scripts/autopilot.py`; each issue gets a fresh process, so context never accumulates across issues.

## Preconditions

- The script refuses to start unless `claude` is on PATH and `gh auth status` succeeds; relay that message.
- The target repository has open issues with the autopilot label (default `autopilot`) whose bodies name dependencies as `Dépend de #N` / `Depends on #N`, plus a CI that really verifies (`autopilot` treats "no checks" as red).
- Product decisions are in an accepted spec: `/gearbox:issue --auto` never invents them, so an under-specified issue ends as `needs-human`.

## Run

1. `--queue` only: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" queue <target>` and report the pending PR, next issue, and open labelled issues.
2. Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" run <target> [--max-merges N] [--max-hours H]` **in the background**, and wait for its completion notification instead of polling.
3. Report the stop reason and, from the `report.json` it names, each issue: merged PR, blocked reason (`needs-human`), deploy result.

## Behaviour (from `.gearbox/config.md`, flat keys)

| Key | Default | Meaning |
|---|---|---|
| `autopilot_label` | `autopilot` | issues it may take |
| `autopilot_max_merges` / `autopilot_max_hours` | 10 / 8 | run budgets |
| `autopilot_guarded_paths` | `.github/,.claude/,.gearbox/config.md` | PRs touching these wait for a human |
| `autopilot_deploy` | empty | shell command run on the base branch after each merge |
| `autopilot_permission_mode` | `auto` | `--permission-mode` of each child `claude -p` |
| `autopilot_check_timeout_min` | 30 | wait for CI per PR |

Order of work: an open PR closing a labelled issue is finished first; otherwise the lowest-numbered ready issue. A red PR gets one `/gearbox:continue-pr --auto`, then `needs-human`. Three consecutive failures, or any open issue labelled `autopilot-pause`, stop the run. Logs and `report.json` go to `.gearbox/runs/autopilot-<timestamp>/`.
