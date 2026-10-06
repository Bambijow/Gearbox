# Capability-aware execution

Gearbox treats external tools as execution constraints, not conveniences discovered after a model has already been paid.

## Task contract

Every executable DAG node records:

```yaml
required_capabilities: []
```

Use stable external capability names. For Codex MCP-backed tools, the capability name is the MCP server name reported by `codex mcp list --json` (for example `godot` or `blender`). Ordinary repository read/write/shell ability is part of the worker role and does not belong in this list. An empty list is meaningful: it authorizes minimal tool exposure for that task.

## Setup inventory

When Codex is available, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/capabilities.py" inventory --codex-bin "<configured codex>"
```

The helper emits only sanitized fields: server name, enabled/disabled state, auth-status label and transport type. It never emits MCP commands, URLs, environment contents, tokens or credentials. Persist only the `available` names as a planning hint; live preflight remains authoritative. Record Claude capabilities only when explicitly visible/configured.

## Provider gate

Capability eligibility happens before risk/cost/model routing:

- one eligible provider -> route there;
- multiple -> normal Gearbox economics decide;
- none -> `CAPABILITY_BLOCKED`.

Use `scripts/capabilities.py route` with the required and known provider capability sets. Never spend a worker merely to discover that its required tool is absent.

## Live Codex preflight

Immediately before Codex dispatch, read the effective MCP inventory from the worker worktree with `codex mcp list --json`. A required capability blocks dispatch when missing, disabled, or clearly auth-blocked. `unsupported` auth is allowed because stdio servers commonly have no auth flow.

## Per-worker MCP pruning

Default policy: `required-only`. Call Codex workers with `--prune-mcp` plus one `--required-capability <name>` per required MCP. Gearbox keeps normal Codex config/credentials loaded but adds one-run overrides for every unrelated enabled server:

```text
--config 'mcp_servers."<name>".enabled=false'
```

Do not use `mcp_servers={}` as a clearing mechanism. Disable discovered servers individually. If a task declares no external capability, pruning disables all discovered MCP servers for that worker only.

## Fingerprints and duplicate dispatches

Before dispatch, fingerprint the exact base SHA, task packet bytes, provider, model, effort, worker kind and required capability set with `scripts/invocation_fingerprint.py`, then register it through `child_jobs.py` with workspace/artifact pointers.

If registration reports `DUPLICATE_INVOCATION`, do not launch another worker. Reconcile the existing child/worktree/artifact. This is not blind result caching: implementation reuse is valid only when recorded git/worktree evidence still carries the mutation.

Codex metadata additionally records CLI version, prompt/schema hashes, active MCP set, memory policy, environment fingerprint and a stricter invocation fingerprint. No secrets are persisted.

## Failure behavior

- stale setup snapshot -> live refresh;
- missing/disabled/auth-blocked tool -> `CAPABILITY_BLOCKED`;
- capability disappears after planning -> reroute when allowed, otherwise block;
- pruning override rejected -> surface failure; never claim minimal exposure;
- duplicate fingerprint -> reconcile instead of paying twice.

## Game-asset capability preferences

Game-asset model identity is resolved by `scripts/game_asset_router.py`, not by generic capability economics. Aseprite is a preferred capability for `pixel-art`: when live it becomes required for that invocation, otherwise Codex GPT-6.1 Sol uses its direct-generation fallback. `model-3d` and `review-3d` require a live Blender or Godot 3D capability; missing 3D tooling blocks the forced route rather than changing models.
