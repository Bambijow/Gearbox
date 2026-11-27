# Capability-aware execution

Gearbox treats external tools as execution constraints, not conveniences discovered after a model has already been paid.

## Task contract

Every executable DAG node records:

```yaml
required_capabilities: []
```

Use stable external capability names. For Gemini MCP-backed tools, the capability name is the MCP server name reported by `gemini mcp list --json` (for example `godot` or `blender`). Ordinary repository read/write/shell ability is part of the worker role and does not belong in this list. An empty list is meaningful: it authorizes minimal tool exposure for that task.

## Gemini / Claude capability discovery

For Antigravity, call `python3 scripts/capabilities.py inventory --cwd <worktree>`. It reads `~/.gemini/config/mcp_config.json` and workspace `.agents/mcp_config.json` without persisting command arguments, URLs, environment variables or secrets. The output is a **configured-only** hint, not proof of an authenticated, usable live MCP.

Use `scripts/capabilities.py route` to select eligible Gemini/Claude providers by declared capabilities. Immediately before any tool-dependent dispatch, require an independently observed live tool call or other provider-native proof. `gemini_worker.py` currently refuses required-capability dispatches unless that live preflight is implemented: report `CAPABILITY_BLOCKED`, never turn a configuration entry into a false PASS.

Do not use old CLI-specific TOML MCP overrides; Antigravity uses JSON MCP configuration. Prune or scope tools using provider-native permissions once tested. Independently inspect the effective worker tool surface; a configured allowlist cannot substitute for a real security check.

## Fingerprints and duplicate dispatches

Before dispatch, fingerprint the exact base SHA, task packet bytes, provider, model, effort, worker kind and required capability set with `scripts/invocation_fingerprint.py`, then register it through `child_jobs.py` with workspace/artifact pointers.

If registration reports `DUPLICATE_INVOCATION`, do not launch another worker. Reconcile the existing child/worktree/artifact. This is not blind result caching: implementation reuse is valid only when recorded git/worktree evidence still carries the mutation.

Gemini workers retain prompt/result hashes and provider-reported usage; live MCP inventory, environment fingerprints and pruning remain blocked until independently verified.

## Failure behavior

- stale setup snapshot -> live refresh;
- missing/disabled/auth-blocked tool -> `CAPABILITY_BLOCKED`;
- capability disappears after planning -> reroute when allowed, otherwise block;
- pruning override rejected -> surface failure; never claim minimal exposure;
- duplicate fingerprint -> reconcile instead of paying twice.

## Game-asset capability preferences

Game-asset model identity is resolved by `scripts/game_asset_router.py`, not by generic capability economics. Pass Claude and Gemini capability sets separately. Aseprite is preferred for `pixel-art` on Gemini; otherwise Neon uses direct generation. For `model-3d` and `motion-design --three-d`, Opus directs while Gemini Carbon/high is the required substantive 3D executor with live Blender/Godot capability on Gemini; if missing, block. Non-3D motion can still use Gemini Neon or Claude's available tools. `review-3d` specifically requires Blender or Godot on Gemini because Carbon must inspect the real asset. Missing tool access blocks rather than silently changing model identity.

## Web-design capability preferences

For `web-design`, capability routing distinguishes useful evidence from hard execution requirements:

- `inspo` is preferred for the Claude design director. Use it for exemplar/macrostructure/design-system evidence when present; absence does not block design.
- browser / Playwright / Chrome-style tooling is preferred for the Gemini builder and rendered review.
- missing browser tooling may still allow implementation, but a material design task cannot claim visual PASS until credible rendered desktop/mobile evidence exists.

Do not route away from the specialist director/builder models merely because an optional design capability is missing.

For web comps, generation is optional under `auto` and mandatory under `--comp require`. Gemini must use a configured and verified image-generation backend. Never persist API credentials while probing availability.

## Product-quality capability rules

These specialist routes still obey live capability preflight:

- `a11y-audit` and `visual-regression` prefer browser/Playwright/accessibility-tree tooling; when material runtime evidence cannot be captured, block rather than claim a runtime gate.
- `experience-perf` requires a credible runtime profiling path for the target experience; source review alone cannot PASS PERF.
- `audio-design --apply` uses exact discovered audio/engine capabilities. Godot can wire supplied audio assets but does not imply sound-generation capability.
- `level-design --apply` requires a credible Godot or Blender blockout path; actual traversal evidence remains mandatory.
- `design-system`, `content-design`, and `art-direction` may produce read-only contracts/audits without external tools; applying mutations still follows normal worker ownership.
