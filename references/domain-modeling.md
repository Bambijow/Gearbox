# Domain language and architecture decisions

Gearbox uses three different durable-memory channels:

- `GLOSSARY.md` / `GLOSSARY-MAP.md`: canonical domain language;
- `docs/adr/`: hard-to-reverse architecture/product-technical decisions whose reason would otherwise be surprising;
- `docs/solutions/`: reusable technical discoveries, traps, root causes and operational lessons.

Do not collapse them into one document.

## Reading language

Before shaping/planning a domain-heavy change:

1. if `GLOSSARY-MAP.md` exists, read it and then only the relevant context glossary;
2. otherwise read root `GLOSSARY.md` when present;
3. use those canonical terms in specs, decision tickets, task packets, tests and PR text.

Reading a glossary is cheap context grounding. Editing it is a separate act.

## Writing glossary terms

Use `domain-curator` only after a term is actually resolved.

A glossary entry should be project/domain specific, one or two sentences, and opinionated:

```markdown
**Invoice**:
A request for payment created after a shipment becomes billable.
_Avoid_: bill, payment request
```

Do not add general programming vocabulary.

Create glossary files lazily. For most repositories use root `GLOSSARY.md`. For clearly distinct bounded contexts, use root `GLOSSARY-MAP.md` pointing to context-local glossaries.

## ADR qualification gate

Record an ADR only when **all three** are true:

1. changing the decision later is meaningfully expensive;
2. a future reader could reasonably ask “why did we choose this?”;
3. real alternatives/trade-offs existed.

If one condition fails, skip the ADR.

Default path:

```text
docs/adr/NNNN-short-slug.md
```

Minimal ADR:

```markdown
# <Decision title>

<1-3 sentences: context, decision, why.>
```

Optional considered-options/consequences/status sections exist only when they add future value.

## Contradictions

If user language, glossary, code and current behavior disagree, surface the contradiction. Do not silently pick whichever source is convenient.

A changed glossary/ADR is part of the product diff and must be reviewed like any other durable documentation.
