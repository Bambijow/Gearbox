# Research protocol

Use focused research when a Gearbox decision depends on facts not safely available from the current repository/context.

## Context isolation

Research belongs in a fresh `researcher` agent so the parent orchestrator keeps its context for decisions.

The parent sends:

- one concrete research question;
- why the answer matters;
- trusted local pointers;
- the destination path for the note.

The researcher returns a **context pointer**, not a pasted research dump.

Default transient destination:

```text
.gearbox/runs/<run-id>/research/<slug>.md
```

Use a durable repository research directory only when the user/repo already treats research notes as maintained documentation.

## Source hierarchy

Prefer sources that own the fact:

1. official specifications/standards;
2. official product/framework documentation;
3. upstream source code/changelog/release notes;
4. first-party APIs or schemas;
5. only then secondary explanations, clearly labeled as secondary.

For library/framework behavior, do not rely on a blog when upstream docs/source can answer it.

## Note format

```markdown
# <question>

## Answer
<short conclusion>

## Evidence
- <claim> — <primary source pointer>
- ...

## Implications for this run
- <decision this changes>

## Unknowns
- <remaining uncertainty, if any>
```

Keep notes decision-oriented. Do not turn research into a literature review.

## Freshness

Record versions/dates when behavior may change. If the run depends on a rapidly changing API or model/tool capability, verify current documentation rather than relying on remembered behavior.

## Secret safety

Never write credentials, cookies, bearer tokens, signed URLs, private keys, or raw sensitive payloads into research notes. Use `<redacted>` and preserve only the fact needed for the decision.
