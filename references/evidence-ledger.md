# Canonical evidence ledger

Claims in a PR must come from recorded evidence, not conversational memory.

Every substantial run maintains `.gearbox/runs/<run-id>/evidence.json`. Use `scripts/evidence.py` where possible.

Evidence records are append-only within a run and may be invalidated by a later commit. Every executable proof includes the commit SHA it applies to.

Supported categories include `test`, `lint`, `typecheck`, `build`, `manual`, `ui`, `review`, `simplification`, `ci`, and `acceptance`.

A command record should include command, exit code, SHA, short summary, and optional log path. UI records include scenario and attachment path. Review records include reviewer/model route, verdict and finding counts.

Before PASS, every acceptance criterion must map to at least one current evidence item. Before shipping, required checks must have successful evidence at the final relevant SHA. If Ponytail or a repair changes code after a check, invalidate/re-run affected evidence.

PR descriptions and technical comments are generated from the ledger plus state, never by inventing unrecorded verification.
