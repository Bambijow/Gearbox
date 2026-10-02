---
name: spec-to-issue
description: "Turn an accepted engineering spec into a concise GitHub implementation issue that preserves outcome, scope, acceptance criteria, constraints, and verification without dumping the whole spec. Optionally create the issue."
argument-hint: "[spec path] [--create] [--title '...'] [--labels a,b]"
disable-model-invocation: true
---

# Convert a spec into a GitHub issue

The issue is an execution contract and navigation surface, not a second copy of the specification. If the accepted spec clearly contains several independently deliverable slices, recommend `/spec-to-issues` instead of producing one Godzilla issue.

## 1. Read and validate the source

Read the supplied spec and relevant repository instructions. If the spec points to code, ADRs, migrations, or prior `docs/solutions/`, verify only the facts needed to avoid publishing stale or contradictory requirements.

Do not silently repair a materially ambiguous spec. Produce the best issue draft possible and clearly mark a blocking open decision instead of inventing product semantics.

## 2. Distill the issue

Create a compact issue body with:

1. **Why**: the user/operator/system problem in plain language.
2. **Outcome**: observable behavior when complete.
3. **In scope**: only implementation-relevant boundaries.
4. **Out of scope**: important exclusions that prevent accidental expansion.
5. **Acceptance criteria**: concrete, checkable scenarios copied semantically from the spec, not implementation tasks.
6. **Constraints / invariants**: compatibility, data, security, migration, API/UI or operational constraints that materially affect implementation.
7. **Verification / evidence**: expected automated checks and UI screenshots/evidence when applicable.
8. **Source spec**: repository path or canonical link.

Keep implementation detail out unless the spec explicitly fixes an architectural constraint. Do not include the implementation DAG; `/loop` or `/issue` will derive the current DAG from the repository when work begins.

Aim for roughly 600 words or less for an ordinary issue. Prefer links/pointers to copied prose.

## 3. Avoid duplicate tracking

When GitHub is available, search open and recently closed issues for the spec title, domain terms, and source spec path. If a likely duplicate exists, report it before creating another issue. Do not create a duplicate automatically.

## 4. Draft first

Write the generated body to a transient run artifact such as `.gearbox/runs/spec-to-issue-<slug>/issue-draft.md` and show the proposed title.

Without `--create`, stop after producing the draft. This keeps external tracker changes explicit.

## 5. Create when authorized

With `--create`, use authenticated `gh issue create` with the generated title/body and only labels explicitly supplied or configured as safe defaults. Do not assign people or milestones unless requested.

Return the created issue URL and number. The resulting issue is compatible with:

```text
/gearbox:issue <created-issue-url> --auto --ship
```

When this conversion is part of `/brainstorm --issue` or another already-authorized parent workflow, do not ask for a redundant second creation confirmation.

## 6. Handoff without spec round-tripping

If implementation continues immediately after issue creation, enter the shared engineering loop with the **accepted source spec as the requirements source** and the created issue as tracker/discussion context. Do not regenerate a new spec from the issue you just distilled from that same spec.

If execution resumes later through `/issue <created-issue-url>`, the issue intake should detect the `Source spec` pointer and reuse that repository spec when it exists and remains applicable. Only issue comments/deltas that materially change requirements should be reconciled into the working intake.
