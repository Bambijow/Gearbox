# Writing for agents

Apply this reference when creating/editing Gearbox skills, agents, `CLAUDE.md`, `AGENTS.md`, or docs intentionally consumed by agents.

## Context pointers

A pointer should state:

- what material exists;
- the distinct situations that should trigger reading it.

Prefer a sharp pointer to copying the material into every always-loaded file.

## Information hierarchy

Put information at the cheapest level that still fires reliably:

1. in-file execution step when every run needs it now;
2. in-file reference when it is often consulted;
3. disclosed reference behind a context pointer when only some branches need it.

Keep related definition/rules/caveats together. Do not scatter one concept across five files.

## Steering files

`CLAUDE.md` and `AGENTS.md` are expensive because they are loaded repeatedly.

They should contain:

- short repo-wide invariants;
- navigation pointers to focused docs;
- facts an agent cannot cheaply discover from the environment.

They should not cache:

- package scripts visible in `package.json`;
- directory structures visible via one command;
- formatter/linter config already enforced mechanically;
- long troubleshooting guides reachable by pointer.

## Deterministic before prose

If a rule can be rejected mechanically, encode it in lint/typecheck/test/CI/hook rather than spending tokens reminding every agent.

Use prose for judgement and reasons, not machine-checkable syntax.

## Completion criteria

Every multi-step agent instruction needs checkable stopping conditions. Replace vague “understand”, “be careful” and “make sure” with observable outputs/gates.

## No-op pruning

Delete instructions that do not materially change model behavior. One source of truth per meaning.

## Skill composition

Do not assume writing “run /gearbox:foo” inside another skill loads that skill.

Gearbox composition rules:

- user-invoked commands remain user entry points;
- shared behavior belongs in `references/`;
- executable delegated behavior belongs in named `agents/`;
- scripts hold deterministic mechanics;
- a skill may point to shared references/agents, but should not rely on invisible slash-command expansion.

This avoids prompt cosplay where the text names a command but none of its behavior is actually loaded.
