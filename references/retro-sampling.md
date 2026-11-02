# Selective retrospectives

Do not dispatch retrospectives for every successful task. Use `scripts/retro_selector.py --run-id <id> --state .gearbox/runs/<id>/state.json` to select approximately 20% of ordinary runs deterministically while always favoring failures, repeated repairs and escalations. This emits a suggestion only; no autonomous worker or background action is started. Respect explicit user requests for `/retro` regardless of sampling. Persist the selection and reason when proactively proposing analysis. Never manufacture telemetry.
