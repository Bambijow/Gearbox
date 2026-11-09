---
name: seo-audit
description: "Audit the technical SEO of a deployed public site with a deterministic check: sitemap pages and internal links answer 200, a real 404, robots/llms.txt, noindex on production, unique titles and descriptions, one h1, canonical, Open Graph, parseable JSON-LD, img alt, optional Lighthouse, and project-banned claims. Report-only by default; --apply repairs in scope."
argument-hint: "<base-url> [--prod] [--lighthouse] [--banned FILE] [--apply]"
---

# SEO as a measured gate, not a checklist

Read `references/seo-audit.md` and the project's brief/product truth.

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/seo_check.py" <base-url> [--prod] [--lighthouse] [--banned FILE]`. Pass `--prod` only for the production URL; a preview is expected to carry noindex. Pass the project's banned-claims file when it has one (`banned.txt`, one regex per line). The script's `FAIL` lines are the evidence; do not restate them as opinions.

Then review what the script cannot see, against the brief only:

- one page per search intent (service × place), no near-duplicate pages;
- JSON-LD describes what the page visibly says (name, address, services, prices) and nothing more;
- canonical and `og:url` point to the production host on every environment;
- no review, `AggregateRating`, testimonial, client count or figure that the brief does not contain.

Without `--apply`, change nothing: return the script output, the review findings with `file:line`, the off-code actions for the user, and the verdict.

With `--apply`, fix validated findings inside the project only (meta, headings, canonical, sitemap, robots, JSON-LD, alt text), never by inventing content, then rerun the script. Copy changes come from the brief; when a fix needs a fact the brief lacks, leave it as a finding.

```text
SEO_GATE: PASS | FAIL | NOT_APPLICABLE
```

`PASS`: the script exits 0 on the audited URL and no review finding remains. `FAIL`: any script failure, banned match or invented claim. `NOT_APPLICABLE`: the surface is not meant to be indexed (app behind login, internal tool, intentional noindex).
