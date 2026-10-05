# Secret redaction

Treat logs, evidence files, research notes, worker reports and PR text as potentially publishable.

Never persist or repeat raw:

- passwords or passphrases;
- API keys/access tokens/bearer tokens;
- session cookies;
- private keys;
- signed URLs/query credentials;
- database URLs containing credentials;
- raw secret-bearing environment variables.

## Runtime helper

Before storing command/evidence summaries, use:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/redact.py" < input.txt
```

Before publishing PR body/report, guards must reject obvious secret-like material.

The helper is defense-in-depth, not proof that content is safe. If a value looks sensitive and the redactor misses it, redact it manually.

Use `<redacted>` while preserving enough surrounding context to make debugging/evidence useful.
