---
name: simplify
description: "Run a fresh post-integration simplification agent, using Ponytail when available, to remove over-engineering and then apply safe simplifications without changing required behavior."
argument-hint: "[diff/base ref]"
disable-model-invocation: true
---

# Simplify after integration, before final review

This is a dedicated change-reduction gate. It happens **after implementation is integrated** and **before final cross-review**.

The goal is not code golf. The goal is the smallest architecture that still satisfies the spec, repository conventions, safety boundaries, and operational needs.

## Independence

Launch Gearbox's `ponytail-simplifier` plugin agent through the Agent/Task tool. It must be a fresh Claude subagent with no implementation-history framing beyond what it needs to understand the spec and diff. Give it:

- originating requirements/spec;
- the integrated diff against the base branch;
- repository instructions;
- relevant surrounding code/tests;
- explicit permission to edit the integration worktree;
- the verification commands it must preserve.

Do not ask the original implementation agent to grade its own architecture.

## Ponytail path

When the Ponytail plugin is installed, require the simplification subagent to use Ponytail's over-engineering review behavior, preferably the `ponytail-review` skill, before editing. Ponytail is the primary simplification lens.

When Ponytail is unavailable, use this fallback ladder:

1. Does this new code need to exist at all?
2. Does equivalent behavior already exist in the codebase?
3. Can standard library/framework/native platform behavior replace custom code?
4. Can an already-installed dependency replace new machinery without adding coupling?
5. Can a helper/layer/config option be deleted because it has one caller or no present requirement?
6. Can duplicate branches become one direct path?
7. Only then keep the minimum custom implementation that makes the acceptance behavior true.

Never trade away validation at trust boundaries, security, accessibility, data-loss protection, required error handling, compatibility, or observability merely to reduce line count.

## Review then edit

The subagent must first identify concrete simplification opportunities tied to the current diff. It then applies only the ones that preserve behavior and improve clarity/maintenance.

Typical valid changes:

- delete speculative abstractions or extension points;
- inline single-use wrappers that obscure rather than clarify;
- reuse an existing repository primitive;
- replace custom plumbing with stdlib/framework/native behavior;
- collapse unnecessary configuration;
- remove duplication introduced by parallel workers;
- simplify naming/data flow after integration reveals a cleaner seam.

Avoid broad unrelated refactors.

## Verification

After the subagent edits:

1. inspect the new diff against the pre-simplification state;
2. run the focused tests for edited behavior;
3. run any affected lint/type/build checks;
4. verify that acceptance coverage is unchanged;
5. revert a simplification if it makes behavior less explicit, weakens safety, or creates a hidden compatibility change.

Report what was deleted/simplified and the net architectural effect. A valid result may be "nothing worth simplifying".
