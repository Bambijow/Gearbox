# SEO audit

Search visibility for a small public site comes from pages that answer a real query, are technically reachable, and say only true things. Measure the deployed site; the source is not what crawlers see.

## Deterministic check

`scripts/seo_check.py <base-url> [--prod] [--lighthouse] [--banned FILE]` (standard library only):

- reads `sitemap.xml`, rebases every `<loc>` on the URL under test, and requires 200 for each page and for every internal `href`, `src` and `srcset`;
- requires a random missing URL to answer 404 (a soft 404 dilutes the index);
- requires `robots.txt` to answer 200, and `llms.txt` to answer 200 when present;
- per page: a `<title>` that exists, is unique and is 10–70 characters; a unique meta description; exactly one `<h1>`; a canonical; `og:title` and `og:image`; every JSON-LD block parses; no `<img>` without `alt` (`alt=""` is a valid decorative image);
- with `--prod`: any `noindex`/`none` in `x-robots-tag` or meta robots fails, and so does `Disallow: /` in `robots.txt`;
- with `--lighthouse`: runs Lighthouse on up to three sitemap pages when `lighthouse` and a Chrome (or `CHROME_PATH`) exist, otherwise prints `SKIP`. Each category must reach 95; the SEO score is judged only with `--prod`, because a preview's noindex sinks it;
- with `--banned FILE`: any match of a project regex in a page's HTML fails.

One `FAIL` line per problem, then `OK`; exit 1 on any problem.

## Page structure

- One page per search intent: one service in one place (`/plombier-lyon/`, `/plombier-villeurbanne/`), each with its own title, description, h1 and genuinely distinct content. Do not generate city pages that only swap the place name.
- The title names the service, the place and the business; the description says what the visitor gets. Both are written from the brief, not from keyword tools.
- Every indexable page is in `sitemap.xml`, linked from at least one other page, and has a canonical to its own production URL.

## Structured data

JSON-LD must match the visible content of the same page: the same name, address, phone, hours, services and prices, and nothing the visitor cannot read there. Pick the most specific schema.org type that is true (`Plumber`, `LocalBusiness`, `Person`, `ProfessionalService`). Validate with the Rich Results Test after deployment.

## Preview pitfalls

- Hosts such as Cloudflare Pages add `x-robots-tag: noindex` on preview URLs. That is correct for the preview and fatal if it reaches production: run `--prod` on the production URL after each launch.
- The canonical, `og:url` and sitemap `<loc>` always point to the production host, also on previews. The check rebases sitemap URLs so a preview can still be crawled.
- A preview's Lighthouse SEO score is low by design; do not "fix" it by removing the noindex.

## Product truth

Never add reviews, `AggregateRating`, testimonials, client counts, years of experience, prices or any figure that the brief does not contain, in the copy or in JSON-LD. Search engines penalise review markup that does not reflect real, visible reviews, and an invented claim is a lie to the client's customers.

Each project may keep a banned-claims file (for example `banned.txt`): one case-insensitive regex per line, `#` for comments, covering placeholders (`À FOURNIR`, `data-placeholder`), prices, testimonial wording and client counts that are not yet true. Pass it with `--banned`; a match fails `SEO_GATE`. Remove a line only when the brief supplies the fact.

## Off-code actions for the user

The audit ends with the steps only the site owner can do:

1. Google Search Console: verify the domain, submit `sitemap.xml`, request indexing of the main pages, then check coverage after a few days.
2. Google Business Profile, for a local business: create or claim it with the same name, address, phone and hours as the site, and link to the site.
3. Links from the owner's real profiles (GitHub, LinkedIn, Malt, directories, professional associations) to the site.
4. Bing Webmaster Tools: import from Search Console.

## Out of scope

Paid keyword tools, rank tracking, backlink buying, and filler "SEO content" written to hit keywords. A page that does not help a real visitor is not added.

## Gate

```text
SEO_GATE: PASS | FAIL | NOT_APPLICABLE
```

`NOT_APPLICABLE` when the surface is not meant to be indexed. Optional for public `Persuade` web surfaces; it never replaces `A11Y_GATE` or `SLOP_GATE`.
