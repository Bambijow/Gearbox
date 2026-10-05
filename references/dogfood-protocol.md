# Product dogfood protocol

Dogfooding evaluates a real user job in the product. It is deliberately broader than an E2E assertion and narrower than an unstructured design critique.

## Journey card

Capture:

- persona/role and permissions;
- starting state/data;
- job to be done;
- success condition;
- critical states worth touching;
- environment/device/viewport when relevant.

A journey should be reproducible by another person without reading the implementation.

## Observe in layers

### Functional
Can the job complete? Are state transitions, persistence, validation, permissions and recovery correct?

### Interaction / comprehension
Does the next action make sense? Are labels, hierarchy, feedback and irreversible actions understandable?

### Runtime
Watch console/runtime errors, rejected promises, failed requests, duplicate calls, suspicious retries and obvious performance stalls.

### Accessibility
For relevant UI, check keyboard reachability, focus movement, labels/names, obvious contrast/zoom/layout failures and whether errors are perceivable.

### Visual / responsive
Inspect key states, not every pixel. Capture evidence for broken layout, clipping, overflow, stale/loading flashes or inconsistent component states.

## Non-happy states

Choose only states that are material to the journey: empty data, invalid input, denied permission, network/API failure, retry, cancellation, timeout, destructive confirmation, mobile/narrow layout.

## Findings

Use:

- `BLOCKER`: job cannot be completed or causes unsafe/destructive behavior;
- `FUNCTIONAL`: observable product behavior is wrong but workaround may exist;
- `UX`: job works but friction/confusion is material;
- `POLISH`: low-cost visual/copy refinement with no material task failure.

Every finding needs steps, observed result, expected intent and smallest useful evidence. Keep subjective preferences clearly labeled.

Dogfood does not waive tests. Reproduced defects should enter the ordinary debug/build/review loop.
