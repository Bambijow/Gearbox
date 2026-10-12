# Content design and UX writing

Interface copy is behavior. It should help a person understand state, choose an action and recover from failure.

## Source of truth

Preserve factual/product claims. Do not invent benefits, customers, metrics, guarantees, policies or capabilities.

Use the repository glossary/domain language when it exists.

## Design by state

For each material surface/component, cover applicable:

- entry/heading;
- primary action;
- secondary/destructive actions;
- helper text;
- loading;
- empty;
- success;
- validation;
- recoverable error;
- permission/blocked;
- destructive confirmation;
- irreversible outcome;
- onboarding/first-use.

## Rules

- name actions with verbs that match consequence;
- say what happened and what the user can do next;
- prefer concrete domain nouns over generic "item/data/content";
- remove repeated headings/intros that say the same thing;
- avoid generic AI marketing language and inflated adjectives;
- avoid blaming the user;
- do not hide destructive consequences in vague buttons such as "Continue";
- use progressive disclosure for detail that is necessary only at decision time;
- keep error copy close to the failing action/field when possible;
- preserve localization expansion and pluralization needs.

## Empty states

An empty state answers:

1. what is this area?
2. why is it empty?
3. what can I do next?

Do not turn every empty state into marketing.

## Errors

Good error content includes:

- concrete problem;
- consequence;
- recovery;
- persistence expectation when relevant.

Do not expose internal stack/errors or fake precision.

## Gate

Return:

```text
CONTENT_GATE: PASS | REPAIR | BLOCKED
```

A content finding must name the state, the comprehension/action risk and a proposed intent-preserving correction.
