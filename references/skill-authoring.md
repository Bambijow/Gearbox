# Skill ecosystem maintenance

Skills are routing surfaces. Their first job is to be selected at the right time; their second is to provide only the context needed after selection.

## Trigger quality

A description should say both what the skill does and when it should be used. Audit neighboring skills as a set:

- overlapping intent words can cause collisions;
- vague descriptions create retrieval holes;
- implementation details in the description consume discovery space without helping routing.

If two skills resolve the same user intent and differ only by minor procedure, prefer one skill with conditional references.

## Progressive disclosure

Keep always-read skill bodies lean:

1. frontmatter/description for discovery;
2. core procedure and hard rules in `SKILL.md`;
3. conditional depth in `references/`;
4. deterministic mechanics in scripts/lint/tests/hooks.

Do not duplicate a long policy in five skills. Put the policy in one reference and leave short pointers at the actual decision points.

## Prose vs enforcement

Use prose for judgment and context. Move mechanically checkable rules to deterministic tooling when practical. A rule that repeatedly causes model mistakes and can be checked cheaply is a candidate for a guard, schema, lint or test.

## Budget and drift

When prompt budgets exist, treat them as ratchets. New capability should pay for its context. Check manifests against discovered skills, dead references, renamed commands, obsolete examples and duplicated steering instructions.

## Evals

Behavior-bearing prompt changes deserve small discriminating evals. Test failure modes, not prose snapshots. Useful scenarios ask whether the skill makes the right routing/stop/escalation decision.

Do not require live model calls in ordinary CI when schema/harness validation is enough; run paid behavioral campaigns explicitly.

## Preferred remedies

In order: delete stale text, deduplicate, move conditional detail behind references, turn mechanical rules into tooling, merge overlapping skills, sharpen triggers, then add a new skill only if it represents a genuinely distinct job.
