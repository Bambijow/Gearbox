# Selective retrospectives

Do not dispatch retrospectives for every successful task. Use `scripts/retro_selector.py --run-id <id> --state .gearbox/runs/<id>/state.json` to select approximately 20% of ordinary runs deterministically while always favoring failures, repeated repairs and escalations. This emits a suggestion only; no autonomous worker or background action is started. Respect explicit user requests for `/retro` regardless of sampling. Persist the selection and reason when proactively proposing analysis. Never manufacture telemetry.

Before recommending recurring environment changes, consult `references/retro-decision-ledger.md` if a ledger exists. Re-test accepted fixes against their recorded verification signals; do not reopen rejected proposals without materially new evidence. Proactive analysis must remain read-only.
