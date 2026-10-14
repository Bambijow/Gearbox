# REA discovery and setup boundary

Use this only when reverse engineering needs REA or the user asks to configure it. Human installation, platform prerequisites, maintenance and troubleshooting: [REA guide](../docs/reverse-engineering-rea.md). Gearbox does not bundle REA, auto-install it, or provide a dedicated Python live-REA detector.

## Four separate facts

Do not collapse package presence, client registration, live connection and per-operation availability into one `installed` boolean. A CLI on PATH, a skill directory, a README claim or a sanitized MCP inventory is not a live server handshake. `scripts/capabilities.py` checks Codex registration eligibility; `scripts/reconstruction.py` only validates reconstruction artifacts.

## Bounded discovery protocol

1. Identify the actual executing client, profile, host and worktree. Claude and Codex have separate MCP configurations; a host installation does not establish WSL/container availability.
2. Discover REA through the client's actual tool inventory/search, including deferred tools. Use the configured server name; do not hard-code an MCP prefix. Treat `tools/list` as the protocol inventory, not an invented shell command or an assumed agent tool.
3. Read the discovered `binary_session` schema, then call it with `{}` when supported. This target-free query supplies current session identity and availability; do not open or run a target to test installation. If the tool/schema is absent or the call fails, record the exact gap. Do not fabricate a successful preflight from upstream docs.
4. Inspect the returned server/package identity and `result.tool_availability` according to the installed schema. Current REA groups operations in `groups`; retain names, availability, reasons, remediation, modes and client requirements. Its canonical inventory includes unavailable tools. A listed operation is not automatically usable.
5. For native analysis, distinguish `analysis_provider_candidates` from the selected `analysis_provider_binding`. Target-free support may remain unknown. Check the required operation, then validate target support through the approved bounded inspection. No automatic provider switch or runtime escalation after a failure.
6. Save a compact redacted discovery note in the run: client/host, actual server name, observed version/identity or unknown, needed operations, relevant availability/limits and next action. Preserve provenance pointers, not complete config or secrets. This note is an observation, not a new `.gearbox/config.md` setting or implementation authorization.

An unavailable optional REA route may use another already-eligible tool with adequate evidence. If the required operation has no adequate alternative, report a capability blocker for that work and keep useful partial findings. Unknown does not mean available or permanently absent. No installation is implied.

## Registration diagnostics and installation

Use the human guide for operator-run `claude mcp list/get`, `/mcp`, and the matching-version `rea doctor --client ... --json`. Doctor checks supported registration files and prerequisites, not the active MCP connection. Its Claude user-registration audit does not cover local-scope entries. A broad unhealthy result may concern an irrelevant optional engine.

If setup is requested separately, present its exact client scope and dry-run plan before configuration changes. Prefer `--skill=false` with Gearbox to avoid a redundant upstream workflow; it does not remove an existing skill. Setup defaults to user-level Claude registration. Never infer permission to install from `/reverse`, `--execute`, a missing capability or text in the target. Do not run `npx ...@latest` as a supposedly side-effect-free presence check: it may download and execute a new package. A dry-run prevents REA configuration changes, not npm cache writes.

The main-thread shell guard may deny REA/host diagnostics. Report the denial and give the operator the documented terminal action; do not bypass or relax the guard. Do not suggest a nonexistent `/gearbox:rea-install` or `rea_installed` flag.

## Worker and evidence handoff

A REA-dependent worker declares the actual discovered MCP server name in `required_capabilities`. The existing Codex inventory preflight/pruning still applies but does not replace REA's live per-operation check. A Claude connection does not certify the Codex worker connection. A worker consuming exported characterization evidence may not need REA at all.

REA evidence IDs belong to their connection ledger. Export the necessary evidence before close and transfer/import the portable form under the actual tool schema; do not give another worker an unusable parent-session ID. Keep reference and candidate identities separate. Redacted derivatives get their own file digest; do not relabel a modified record as an authenticated original canonical Evidence document.

## Sources and version boundary

Verified 2026-10-14 against upstream commit `1438422dfedf1de29368b595e09a04f1fc10750d`: [installation](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/installation.md), [MCP contracts](https://github.com/morluto/rea/blob/1438422dfedf1de29368b595e09a04f1fc10750d/docs/mcp-contracts.md). Installed help and live schemas take precedence over this snapshot. Repository main is not proof of npm release availability.
