# Worktree repository identity

Before creating or removing a worker worktree, resolve the approved repository from the persisted run identity. Pass it explicitly as `--expected-repo <approved-repo-root>` to `scripts/worktree_manager.py` and the actual working repository as `--repo <path>`. Both must share Git's canonical common-directory identity; the command exits 7 on mismatch. Do not infer the approved identity from the plugin installation directory or the current process working directory.

Example:

```bash
python3 scripts/worktree_manager.py create --repo "$PROJECT_ROOT" --expected-repo "$RUN_REPO_ROOT" --path "$WORKTREE" --branch "$BRANCH" --base "$BASE"
```

For removal, the target worktree itself must also belong to the approved repository. List is read-only but still requires a valid Git repository. Missing identity blocks mutating commands; no automatic fallback to `.`. This contract intentionally requires callers to propagate the run's repository identity, and should be regression-tested with two distinct repositories.
