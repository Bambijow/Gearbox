# Gearbox Antigravity migration (preview)

The verified distribution path is built with `python3 scripts/build_antigravity.py --output dist/gearbox-antigravity`. Then run `agy plugin validate dist/gearbox-antigravity` and `agy plugin install dist/gearbox-antigravity`. The Antigravity desktop App also installs local plugin folders through Customizations > Installed or from the workspace `.agents/plugins/` directory. Do not install this raw multi-provider source tree until `agy plugin validate .` confirms its legacy Claude agent metadata is accepted; the packaged distribution excludes those agents.

The native manifest in `.antigravity-plugin/plugin.json` is shared with the generated bundle. Claude Code's `.claude-plugin` stays separate. For active Gearbox workflows, verify `/hooks` includes `gearbox-control-plane` before dispatching work.

Status: native manifest, safe packaging, Gemini/Claude router, Gemini headless worker and Antigravity hook adapter, all with offline self-tests. Full `/issue` / `/loop` / `/flow` control-plane integration, Claude cross-provider dispatch, and live MCP/capability preflight are not yet migrated. Those tasks return `MIGRATION_BLOCKED` on Antigravity rather than silently invoking previous provider.

Run `agy models` to verify installed model slugs; no automatic fallback. Review 3D needs Blender/Godot live access on Gemini. Local authenticated Antigravity testing and denied-write hook tests are required before production use.

Architecture policy: Neon handles ordinary design; Carbon is the preferred first author for critical/high-complexity decisions, with independent Claude Opus challenge. Configure actual Gemini model IDs from your installed CLI before running, and do not accept an unreviewed critical decision.
