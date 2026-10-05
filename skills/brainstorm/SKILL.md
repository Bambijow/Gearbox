---
name: brainstorm
description: "Interactive product/engineering front door: talk through a fuzzy idea, converge on a compact accepted spec, optionally create the GitHub issue, then enter the normal Gearbox engineering loop without re-deriving the spec."
argument-hint: "[idea or existing spec path] [--issue] [--auto] [--ship] [--models ask|auto|hybrid|claude-heavy|codex-heavy] [--follow-pr] [--max-cycles N] [--workers N] [--no-codex] [--token-profile efficient|strict]"
disable-model-invocation: true
---

# Brainstorm -> spec -> issue -> engineering loop

Use this when the user has an idea, problem, partial feature, or existing spec that still needs collaborative shaping before implementation.

This is a conversational entry point. Do not turn it into a questionnaire, a design document marathon, or an implementation session before the product behavior is clear.

Read:

- `references/artifact-contract.md` for durable/transient artifact locations;
- `references/token-efficiency.md` for context budgets;
- `references/spec-clarification.md` for the final decision-completeness gate;
- `references/domain-modeling.md` for canonical vocabulary and qualifying ADR decisions;
- `references/research.md` when a product decision depends on current external facts;
- `references/control-plane.md` for the parent/worker boundary;
- `references/engineering-loop.md` only once the spec is accepted and implementation begins.

## Flag semantics

- no flags: brainstorm interactively, persist the accepted spec, and produce a GitHub issue draft; do not mutate GitHub or implement yet.
- `--issue`: after the spec is accepted, create the GitHub issue and enter the shared engineering loop. Stop before PR shipping unless `--ship` is also present.
- `--ship`: implies `--issue`; after PASS, commit/push/open the PR and publish the normal Gearbox PR evidence.
- `--auto`: after product intent is decision-complete, authorize ordinary engineering choices and bounded repair cycles. It never authorizes inventing missing product semantics.

## 1. Start a compact brainstorm run

Initialize a transient run through `scripts/run_state.py init`, using a directory such as:

```text
.gearbox/runs/brainstorm-<slug>/
```

The approved state script creates the run directory. Do not use arbitrary product-tree shell mutation merely to set up orchestration state.

Maintain `decisions.md` as a **compressed decision ledger**, not a transcript. Keep only:

- desired outcome and who experiences it;
- important observed/current behavior;
- scope and non-goals;
- accepted product/domain decisions;
- material constraints/invariants;
- concrete examples/acceptance scenarios;
- rejected alternatives only when the reason matters later;
- genuinely open decisions.

Keep the ledger compact, normally under about 800 words. Rewrite/compress it as the conversation evolves instead of appending every turn forever.

If the input is an existing spec path, treat the brainstorm as an amendment session: preserve accepted requirements, discuss only the requested or newly discovered deltas, and update the same spec rather than creating a near-duplicate.

## Wayfinder boundary

If the desired destination is understandable but reaching a spec requires several decision-sized investigations with dependencies/fog that cannot fit comfortably in this session, do not force the brainstorm to absorb the entire initiative. Explain the boundary and hand the user to `/gearbox:wayfinder`. Brainstorm is for converging one spec; Wayfinder is for discovering the route to one.

## 2. Talk, do not interrogate

Start from what the user already gave you. Ask the **highest-leverage unresolved question** next.

Good questions distinguish between materially different outcomes, for example:

- what the user/operator should observe;
- where a boundary or failure case should land;
- whether an existing behavior must remain compatible;
- what is explicitly out of scope;
- which of two materially different UX/domain semantics is intended.

Do not ask the user for facts the repository can answer. If a consequential choice depends on a current external fact, dispatch `researcher` and keep only its conclusion + note pointer in the decision ledger. When repository knowledge can resolve a question, inspect the relevant code/tests/docs once and summarize the fact into `decisions.md`.

Prefer one focused question at a time during genuine product exploration. Bundle a few independent yes/no details only when doing so is clearly cheaper and does not hide a decision.

When there are meaningful alternatives, present at most 2-3 concrete options with concise trade-offs. Do not force an architecture decision into the brainstorm unless it changes externally observable behavior, compatibility, data ownership, safety, migration, or another requirement-level constraint.

## 3. Consult existing knowledge only when relevant

Once the problem/domain is clear enough to search intelligently, check relevant `docs/solutions/` notes and repository terminology. Pull only directly relevant facts or warnings into the decision ledger.

Use canonical terms from the relevant glossary when one exists. If the conversation genuinely resolves a domain term or a qualifying hard-to-reverse trade-off, delegate the minimal glossary/ADR update to `domain-curator` after user acceptance.

Historical solutions are evidence, not requirements. If a prior solution conflicts with the user's intended behavior, surface the conflict rather than silently inheriting the old choice.

## 4. Convergence gate

The brainstorm is ready to become a spec when all of these are true:

- the desired observable outcome is clear;
- important scope/non-goals are explicit;
- material product/domain semantics are decided;
- meaningful compatibility/data/security/migration constraints are known or explicitly not applicable;
- there are concrete acceptance scenarios;
- no unresolved decision would cause two reasonable implementations to produce materially different user-visible behavior.

Do not keep brainstorming for cosmetic preferences or implementation details that `/plan` can decide later.

Before materializing the spec, apply the same DEDUCED / ASSUMED / QUESTION classification from `references/spec-clarification.md`. Conversational brainstorm may resolve questions one at a time, but the accepted spec must have no unresolved blocking QUESTION.

If a material product decision remains open, keep the conversation in brainstorm mode even with `--auto`. `--auto` is not permission to guess.

## 5. Materialize the accepted spec

Transform the compressed ledger plus verified repository facts into a decision-complete, compact spec using the specification content and clarification gates defined in this skill plus `references/spec-clarification.md`.

On convergence, save or update the accepted spec canonically under:

```text
docs/engineering/specs/YYYY-MM-DD-short-kebab-title.md
```

unless repository configuration already defines the specs directory. The brainstorm front door is intended for work substantial enough to earn a spec; if the request collapses into a trivial edit, say so rather than manufacturing document theatre.

The spec should contain the destination and constraints, not the brainstorm transcript and not the implementation DAG. Aim for roughly 1,000 words or less for ordinary changes.

Run a contradiction pass against the relevant current code/docs before calling it accepted.

Without `--auto`, if the user has not already clearly approved the converged behavior during the conversation, show a compact summary and get one final acceptance before creating external tracker state.

## 6. Spec -> issue without lossy round-tripping

Create a concise issue body that points back to the accepted spec. Include Why, Outcome, In scope, Out of scope, checkable Acceptance criteria, material Constraints/invariants, expected Verification/evidence, and the Source spec pointer. Do not include the implementation DAG.

Always create the issue draft in the brainstorm run directory.

Without `--issue` or `--ship`, stop after the spec and issue draft and report the next command.

With `--issue` (or implied by `--ship`), create the GitHub issue. This parent command is the user's authorization for that issue creation; do not ask for an additional tracker confirmation after the spec has been accepted.

Record the created issue URL/number in the run state and, when appropriate, add the tracker reference to the spec without duplicating the issue body.

## 7. Enter the classic engineering loop

After issue creation, enter `references/engineering-loop.md` using:

- the **accepted spec file as the durable requirements source**;
- the **created GitHub issue as tracking/discussion context**.

Do **not** immediately reconstruct a new spec from the issue you just generated. That round-trip adds tokens and can lose nuance.

If execution resumes later from `/issue <number>`, the issue-to-spec intake should detect the `Source spec` path and reuse that spec when it still exists and has not been superseded.

Once implementation begins, the same delegated control-plane invariant applies: the parent does not author product changes. Run the same DAG/TDD/workers/integrator/Ponytail/review/verifier/repair/knowledge-curator gates as any other Gearbox loop. `/learn` remains conditional and writes canonically to `docs/solutions/` only when a reusable lesson qualifies.

## Finish

Report the current stage and artifacts:

- brainstorm decisions converged or still open;
- accepted spec path;
- issue draft path;
- GitHub issue URL/number when created;
- engineering-loop state/cycle count when executed;
- learning result;
- PR URL when `--ship` succeeds.

## Post-PR continuation

When `--follow-pr` is present with `--ship`, continue through `references/post-pr-loop.md` after the PR is opened, bounded by `max_pr_repair_cycles`. Without it, create/update the PR and leave later CI/review repair to `/continue-pr`.
