# Retrospective decision ledger

A ledger is optional, repository-local evidence stored at `.gearbox/retro-decisions.json` (or a user-approved durable location). Do not create it during a read-only `/retro`. Create/update it only with explicit authorization to apply or track recommendations. Never include private session transcripts, credentials, secrets or raw prompts.

Schema: JSON object with `schema_version: 1` and `decisions: []`. Each entry records:
- `id`: durable unique identifier;
- `first_seen_run`: run ID or evidence pointer;
- `recommendation` and `destination`: narrowly scoped action;
- `status`: `accepted`, `rejected`, or `deferred`;
- `rationale`: specific evidence-based reason;
- `verification_signal`: measurable/checkable condition, including location/command when applicable;
- `follow_up`: optional `{run, observed, result}`, where `result` is `worked`, `failed` or `inconclusive`.

Example:
```json
{
  "schema_version": 1,
  "decisions": [
    {
      "id": "retro-duplicate-dispatch-001",
      "first_seen_run": "2026-11-18-run-a",
      "recommendation": "Reconcile matching child fingerprints before dispatch",
      "destination": "scripts/child_jobs.py",
      "status": "accepted",
      "rationale": "Two retries launched the same work",
      "verification_signal": "No duplicate child fingerprint in subsequent retry run",
      "follow_up": {"run": "2026-11-19-run-b", "observed": "zero duplicates", "result": "worked"}
    }
  ]
}
```

On later retros, compare proposals by destination and failure mode. Accepted decisions require observed follow-up evidence, not automatic success claims. Rejected decisions are not proposed again without materially new evidence; deferred decisions may be reconsidered when their blocking condition changes. Unknown or missing follow-up is `inconclusive`, not `worked`. Surface the decision history in the recommendation, but keep default retro analysis read-only.
