# Evidence freshness and reuse

Fresh evidence is required before a completion claim. **Fresh does not mean rerun blindly.**

Gearbox may reuse recorded evidence only when the ledger proves it still applies.

## Reuse gate

Before rerunning a check, query the ledger:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/evidence.py" reuse \
  --file ".gearbox/runs/<run-id>/evidence.json" \
  --kind test \
  --sha "<current-head-sha>" \
  --command "<exact command>"
```

Evidence is reusable when all applicable conditions hold:

- it is still valid;
- it passed;
- by default it belongs to the **exact current SHA**; alternatively, an expensive scoped gate may explicitly use an identical dependency `scope_fingerprint`;
- the requested command/path scope matches when supplied;
- it is not marked volatile;
- any TTL has not expired.

If the query returns `reusable: true`, reviewers/verifiers should **read and use the existing proof** instead of rerunning the same expensive command merely for reassurance.

## Rerun triggers

Rerun when any of these is true:

- current SHA differs when using the default exact-SHA mode;
- the recorded dependency scope fingerprint differs when scoped reuse is explicitly enabled;
- an affected repair/simplification invalidated the proof;
- the requested check is broader/different than the recorded command;
- evidence is missing, truncated, or illegible for the claim;
- the check depends on external state and its TTL expired;
- a finding specifically challenges the seam/tool that produced the evidence;
- the evidence was marked `--volatile`.

Do not reuse old green output across code changes merely because the diff “looks unrelated”. Exact-SHA reuse remains the conservative default. Cross-SHA reuse requires a fingerprint computed from the gate's declared dependency files plus relevant environment/scenario metadata with `evidence.py fingerprint`.

## Volatile evidence

Environment/UI/external-service observations may be recorded with `--volatile` or a bounded `--ttl-seconds`. They remain useful forensic evidence but do not become immortal completion proof.

## Review economy

A reviewer is not a test runner by default. Its job is to assess requirements/code/risk and inspect the evidence package. Running checks is justified only by a concrete verification gap or freshness failure.

This reduces duplicate expensive suites without weakening the evidence-before-claims rule.

## Dependency-scoped reuse

For a costly scoped gate whose dependencies are explicit, compute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/evidence.py" fingerprint \
  --repo-root . \
  --path src/components/Button.tsx \
  --path src/theme/tokens.css \
  --meta-json '{"scenario":"checkout-submit","viewport":"mobile"}'
```

Record the returned `scope_fingerprint` when adding evidence, then query reuse with that fingerprint. A change outside those dependencies may reuse the proof across SHAs; a dependency-content or scenario/environment change may not.

Do not use scoped reuse for evidence whose true dependency surface is unknown.

## Automatic local dependency closure

For supported Python and JS/TS/CSS local imports, `scripts/evidence_deps.py` can derive a bounded dependency closure from one or more entry files. Add contracts/tokens/fixtures not visible through imports as explicit extras.

Use the derived list as input to `evidence.py fingerprint`. If dynamic imports/generated files/runtime configuration make the dependency surface uncertain, do not pretend the closure is complete; retain exact-SHA reuse.
