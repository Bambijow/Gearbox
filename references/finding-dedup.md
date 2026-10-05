# Canonical finding deduplication

CI, human review, final review and runtime verification can describe the **same failure** in different words. Gearbox should repair the failure once.

Before opening a repair task for a newly validated signal:

1. reduce it to a short canonical identity based on the broken invariant/failure path, not the wording of the comment;
2. include the owning path or contract when it materially disambiguates the failure;
3. ingest the source through `scripts/finding_registry.py`;
4. repair the returned finding id, not the raw source item.

Example identity:

```text
anonymous request | null user dereference | src/foo/handler.ts
```

Then:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finding_registry.py" ingest \
  --run-dir ".gearbox/runs/<run-id>" \
  --identity "anonymous request | null user dereference | src/foo/handler.ts" \
  --source-kind ci \
  --source-id "check:12345" \
  --summary "POST /foo returns 500 for anonymous users" \
  --severity Important \
  --primary-path "src/foo/handler.ts"
```

A matching fingerprint appends the new source to the existing finding instead of creating another repair.

## No fuzzy auto-merge

The script intentionally does not perform semantic similarity. The control plane must first validate the source and choose a canonical identity from code/spec/evidence. This prevents an LLM similarity guess from collapsing two distinct failures.

If two findings were opened separately and later evidence proves they are the same root failure, merge them explicitly with a ruling.

## Source provenance

Keep all contributing sources on the canonical finding:

- CI/check id;
- reviewer/finding id;
- GitHub comment/thread id;
- verifier/runtime id.

The final report can then say one repair closed multiple signals without pretending the signals were independently fixed.

## Repair interaction

Finding deduplication happens **before** `references/repair-findings.md`.

One canonical finding gets:

- one attempt history;
- one same-strategy breaker;
- one scoped re-review;
- one final ruling.

Do not consume three repair cycles because three surfaces reported the same invariant.
