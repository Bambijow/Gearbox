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
- it belongs to the **exact current SHA**;
- the requested command/path scope matches when supplied;
- it is not marked volatile;
- any TTL has not expired.

If the query returns `reusable: true`, reviewers/verifiers should **read and use the existing proof** instead of rerunning the same expensive command merely for reassurance.

## Rerun triggers

Rerun when any of these is true:

- current SHA differs;
- an affected repair/simplification invalidated the proof;
- the requested check is broader/different than the recorded command;
- evidence is missing, truncated, or illegible for the claim;
- the check depends on external state and its TTL expired;
- a finding specifically challenges the seam/tool that produced the evidence;
- the evidence was marked `--volatile`.

Do not reuse old green output across code changes just because the diff “looks unrelated”. Exact-SHA reuse is the conservative default.

## Volatile evidence

Environment/UI/external-service observations may be recorded with `--volatile` or a bounded `--ttl-seconds`. They remain useful forensic evidence but do not become immortal completion proof.

## Review economy

A reviewer is not a test runner by default. Its job is to assess requirements/code/risk and inspect the evidence package. Running checks is justified only by a concrete verification gap or freshness failure.

This reduces duplicate expensive suites without weakening the evidence-before-claims rule.
