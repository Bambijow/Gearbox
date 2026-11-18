# A/B evaluation of skill changes

Use this optional, paid experiment after changes that can alter agent behavior. The existing `scripts/behavior_eval.py` validates and grades single scenarios, but a passing scenario alone is not evidence of improvement.

1. Pin **baseline** and **candidate** to full, different immutable Git commit SHAs. Read all `context_files` from the appropriate checked-out Git tree. Do not reuse a mutable branch or working-tree contents for baseline. Preserve the same scenario and assertion definitions for both. Keep held-out scenarios unavailable during candidate tuning.
2. Run matching baseline/candidate scenarios in randomized or counterbalanced order, with at least three independent samples per arm/provider/model when budget allows. Record the exact model ID, effort, runner version, scenario hash, seed (if available), and invocation command. Do not silently compare a Sol baseline with an Astra candidate: stratify by model and effort.
3. Use `scripts/behavior_eval.py`'s isolated provider home/config. Check that personal skills and instructions did not leak. Do not copy full authentication/configuration directories. Use separate worktrees and invocation artifacts for each run.
4. Include negative controls (requests that must not trigger the skill and adversarial cases that must not bypass safety/required work) and verify produced artifacts and code behavior independently, not only the model's prose. Report missing artifacts, failed commands and timeouts as failures, not missing data.
5. Save one report matching the schema consumed by `scripts/skill_ab_compare.py`. Each observation must contain `arm`, `provider`, `model`, `effort`, `scenario`, `repeat`, `pass`, `negative_control`, `artifacts_verified`, `isolation`, and `evidence`. Evidence points to a retained, inspectable local artifact or receipt. Use `--report` to check structural validity and get per-model pass counts. This is a comparison gate, **not** an automated claim of semantic correctness.
6. KEEP only when representative and held-out outcomes improve without negative-control regressions, skipped required work, or broken artifacts. REJECT regressions. Mark noisy/inadequately sampled results INCONCLUSIVE. Explicitly report both weaker and stronger model results; a gain on one model can mask degradation on another.

Example command for the deterministic report check:
```bash
python3 scripts/skill_ab_compare.py --report .gearbox/evals/skill-ab-report.json
```

This work is opt-in and must not make CI call paid models.
