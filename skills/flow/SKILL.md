---
name: flow
description: "Compatibility entry for the Gearbox engineering loop on substantial non-issue work. Prefer /loop for new usage."
argument-hint: "[request or spec] [--auto] [--ship] [--max-cycles N]"
disable-model-invocation: true
---

# Run the Gearbox loop

`/flow` remains as a compatibility entry point. Execute the shared protocol in `references/engineering-loop.md` directly; do not rely on another slash command being implicitly loaded.

Read `references/control-plane.md`, `references/engineering-loop.md`, normalize the supplied request/spec, and execute to PASS, BLOCKED, or the configured cycle limit.

Keep the historical Gearbox phase order:

1. shape only as much as needed;
2. plan and pre-flight the DAG;
3. delegate every product edit to bounded workers; inspect centrally and delegate accepted integration to `integrator`;
4. simplify the integrated diff with Ponytail/fallback discipline;
5. independently review and delegate verification to `verifier`;
6. repair only failed gates instead of restarting the full workflow;
7. run the conditional learning gate after PASS through `knowledge-curator` when needed;
8. ship only when `--ship` authorizes it, through `shipper`.

For a GitHub issue, prefer `/issue`. For a general request or accepted spec, prefer `/loop`.
