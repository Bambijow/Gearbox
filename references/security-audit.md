# Focused security audit protocol

Security review begins by modeling what an attacker can control and what must be protected. It does not begin with a generic checklist.

## 1. Scope the trust boundary

Record:

- protected assets and privileged actions;
- attacker position and capabilities;
- untrusted inputs/entry points;
- authentication and authorization boundaries;
- sensitive sinks: database writes, shell/interpreters, templates, file paths, network egress, secrets, cryptographic operations, logs;
- relevant tenancy/ownership assumptions.

For a diff, compare before/after attack surface and follow only direct dependencies needed to validate a path.

## 2. Trace plausible abuse paths

Ask concrete questions:

- Can request-controlled identity/ownership data bypass authorization?
- Is input validated before canonicalization-sensitive use?
- Can strings cross into SQL/shell/template/path/query/interpreter contexts unsafely?
- Can URLs/redirects/egress reach internal or privileged resources?
- Can uploads/archives/parsers escape expected type/path/size/resource limits?
- Can deserialization instantiate or execute more than intended?
- Can secrets/tokens leak through logs, errors, client bundles or caches?
- Do crypto choices include unsafe modes, nonce/key reuse, weak fallback or home-grown primitives?
- Can race/retry/idempotency behavior duplicate or corrupt sensitive actions?
- Do config/dependency changes weaken defaults or expand privileges?

Only pursue applicable paths.

## 3. Tools

Use repository-native security tests first. Semgrep/CodeQL/static analyzers can expand search, especially for variants of a suspected pattern. Run narrow rules/queries before huge scans. Validate every scanner hit against reachable behavior and current code.

Never paste secrets into findings. Apply secret redaction to logs/evidence.

## 4. Finding contract

A confirmed finding contains:

- title and severity;
- attacker precondition;
- source/entry point;
- vulnerable path and sensitive sink;
- impact;
- code/evidence location;
- reproduction or reasoning strong enough to falsify;
- smallest viable remediation and verification idea.

Keep unconfirmed hypotheses separate. No finding is better than invented security theater.
