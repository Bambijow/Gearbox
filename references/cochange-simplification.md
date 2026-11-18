# Optional structural history diagnostic

Only for substantive architecture simplification, not small patches, run `python3 scripts/cochange_diagnostic.py --repo <project> --limit 100 --minimum 3`. The helper examines pairs of files repeatedly changed together and returns a reproducible, read-only ranking. Ignore generated/vendor files and large sweeping commits before interpreting the result.

Compare high co-change pairs against current import/dependency edges, ownership, design boundaries and related requirements. Co-change without imports can suggest implicit coupling, while frequent co-change with dependencies can reveal unnecessary abstraction layers. Neither observation proves a defect; never refactor solely to make the score lower. Use concrete failure/maintenance cost, and preserve protected tests per `references/protected-proof-tests.md`. The diagnostic must never mutate files, spend model budget on its own, or override scope.
