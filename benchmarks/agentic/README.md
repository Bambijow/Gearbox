# Gearbox agentic benchmark lane

This lane measures **real engineering-agent sessions**, not one-shot prompt completions.

The benchmark is intentionally outside normal CI. Live runs spend model tokens and are started explicitly.

## Design

Each matrix cell gets:

- a fresh clone of a pinned repository commit;
- a fresh agent process/context;
- one explicit plugin arm;
- the same task/model/run index;
- deterministic correctness and safety commands after the agent stops;
- preserved workspace + raw metrics for offline rescoring.

Economy metrics are only compared when **every run being compared passes correctness and safety**. Less code/tokens/time that ships less behavior is not a win.

## Arms

A typical comparison is:

```json
{
  "arms": {
    "baseline": {"plugin_dir": "/tmp/Gearbox-1.4.1"},
    "candidate": {"plugin_dir": "/path/to/current/Gearbox"}
  }
}
```

Baseline can also be `null` to compare Gearbox against the same agent with no plugin.

Do not point both arms at the same mutable directory.

## Anti-contamination contract

The included Claude runner uses:

- `--setting-sources project,local` so globally enabled plugins are excluded;
- exactly one `--plugin-dir` per plugin arm;
- `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`;
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`;
- a new process and repository clone per cell.

If you replace the runner, it must preserve equivalent isolation. A benchmark where the candidate leaks into the baseline is invalid.

## Manifest

Start from `manifest.example.json`. Pin the target repo to an exact commit and provide deterministic post-run commands for both correctness and safety.

Validation and harness self-tests are free:

```bash
python3 scripts/agentic_bench.py self-test
python3 scripts/agentic_bench.py validate benchmarks/agentic/manifest.example.json
```

A live run:

```bash
python3 scripts/agentic_bench.py run benchmarks/agentic/my-benchmark.json \
  --runner "python3 benchmarks/agentic/claude_runner.py" \
  --workers 2
```

Workspaces and metrics are preserved under `benchmarks/agentic/runs/<timestamp>/`.

After changing a scorer, rescore the kept workspaces without paying the model again:

```bash
python3 scripts/agentic_bench.py rescore \
  benchmarks/agentic/my-benchmark.json \
  benchmarks/agentic/runs/<timestamp>
```

## What to measure

Prefer a small matrix of tasks that stress Gearbox behavior:

- bounded feature with loud/local failures;
- silent shared-seam bug;
- repair after CI/review feedback;
- interrupted run + resume;
- `/issue` with and without `--auto`;
- high-consequence change that should trigger full review.

Useful metrics include correctness/safety rate first, then source lines, tokens, provider-reported cost, duration, turns/dispatches and repair cycles.

Use at least 3 runs per cell before drawing conclusions from nondeterministic metrics.

## Honesty boundary

A benchmark result belongs to its pinned repo, task set, models and harness version. Do not print “Gearbox saves X%” for an arbitrary repository from these numbers.

If correctness/safety drops, economy deltas are marked `NOT_COMPARABLE`.
