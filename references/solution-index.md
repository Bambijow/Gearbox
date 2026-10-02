# Solution-memory index

`docs/solutions/` is active memory. Keep `docs/solutions/index.md` as a cheap retrieval surface when the corpus is non-trivial.

New/updated solution notes should use compact YAML frontmatter:

```yaml
---
title: Cache invalidation after transactional writes
tags: [postgres, cache, transactions]
areas: [src/cache/**, src/write/**]
verified_against: <git-sha>
last_verified: 2026-10-01
---
```

The index contains one line per current note: title, tags/areas, path and verification date. It is a routing aid, not another copy of the note.

Normal issue intake reads/searches the index first and deep-reads only the most relevant solution notes, normally 1-3. `/learn` updates the index after creating/updating a note. `/clean-solutions` regenerates/repairs it after refresh/merge/delete operations.

Use `scripts/solutions_index.py` to regenerate deterministically when possible.
