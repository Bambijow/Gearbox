---
name: ship
description: "Publish completed work after final gates: verify, commit, push, create/update a stakeholder-readable PR, then post a technical evidence comment with critical code, checks, simplification notes, and UI screenshots when relevant."
argument-hint: "[optional issue/PR/base-branch instructions]"
disable-model-invocation: true
---

# Ship a change without hiding risk

## Orchestrated-run ownership

When shipping is reached from an active Gearbox engineering loop, the parent orchestrator delegates this entire publication phase to the `shipper` agent. Direct `/ship` invocation by the user remains a standalone command and may perform these actions in the active session. The shipper never repairs product code; any discovered defect returns to a worker repair cycle.

Invoking `/ship` authorizes normal source-control actions needed to publish the completed change, but not deployment, merge, or destructive production actions.

## Preflight

Read repository instructions and `.gearbox/config.md`. Inspect `git status`, relevant diff, branch/upstream state, and recent commits. Never include unrelated user changes.

Check for secrets, debug artifacts, temporary orchestration files, accidental generated output, and unexpected binaries. Read persistent `state.json` and canonical `evidence.json`; shipping is idempotent and must reuse a recorded PR.

## Final verification

Run the most relevant configured checks. If the integrated diff has not had the dedicated simplification and independent review gates, run them before shipping substantial work.

If a check is unavailable or too expensive, say so instead of implying a clean bill of health.

## Commit

Stage only intended files. Prefer one coherent commit unless repository conventions or reviewability clearly benefit from multiple commits. Follow existing commit-message conventions. Do not rewrite published history unless explicitly requested.

## Push and PR

When remote credentials are available, push the current branch. For GitHub repositories use `gh` to create or update the PR. If run state already contains a PR, update it. Store a newly created PR ID/URL immediately in state.

Use the repository's PR template when present, but preserve the two-audience contract from `references/pr-reporting.md`.

### Main PR description

Write primarily for a non-technical stakeholder. Explain the problem, observable change, scope boundaries, confidence/verification, rollout caveats, and linked issue in plain language. Avoid implementation internals.

### Technical evidence comment

After the PR exists, create or update one separate technical comment identified by `<!-- gearbox-report:v1 -->` that gives an engineer control of the change:

- implementation/architecture map;
- important changed areas and why;
- 1-5 short, exact, source-backed critical code excerpts with file/line ranges, why they matter, and review focus; plain path bullets are not sufficient;
- tests/lint/typecheck/build/manual checks actually run;
- simplifications made by the Ponytail gate;
- material engineering-loop repair cycles and the failed gates they resolved;
- cross-review findings fixed and residual risks;
- durable `docs/solutions/...` notes created or updated by the conditional learning gate;
- screenshots/videos for UI/UX changes.

For screenshots/videos, prefer GitHub CLI's `--attach` support. The comment Markdown may reference local evidence paths and pass those same files as repeated `--attach` values so GitHub uploads and rewrites them. Do not commit screenshots solely to make them visible in the PR when attachments are available.

Before posting the technical comment, persist it as the run's `pr-technical-report.md` and validate it with `scripts/pr_report_guard.py`. Use `--require-code` when the PR changes substantive code/config/schema/migrations/runtime behavior. `SHIP_REPORT_INCOMPLETE` blocks publication until the report contains real source-backed excerpts.

If the installed GitHub CLI does not support attachments, post the technical text and explicitly report that visual evidence could not be uploaded automatically.

## Handoff

If another engineer will continue the work, keep the handoff short: current state, key decisions, verification, remaining work, sharp edges.

Do not deploy, merge, modify production data, or approve your own PR unless the user separately requested that action.

## Evidence and continuation

Generate verification claims from `evidence.json`. After push, record the final head SHA. If configured/requested to follow the PR, enter `references/post-pr-loop.md`; otherwise `/continue-pr` can resume later without replaying the issue.
