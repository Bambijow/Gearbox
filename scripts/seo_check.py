#!/usr/bin/env python3
"""Deterministic SEO check of a deployed static site.

Usage: python3 seo_check.py <base-url> [--prod] [--lighthouse] [--banned FILE]
  --prod        the URL is production: any noindex (x-robots-tag or meta robots) and
                `Disallow: /` in robots.txt fail, and the Lighthouse SEO score is judged.
  --lighthouse  run Lighthouse on up to 3 sitemap pages (skipped with a note when
                `lighthouse` or a Chrome is missing).
  --banned FILE one regex per line (case-insensitive, `#` comments); any match in a
                page's HTML fails: claims the product truth does not support.
Output: one `FAIL ...` line per problem, then `OK` or the count; exit 1 on any problem.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import urllib.error
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

TITLE_LEN = (10, 70)
LH_MIN = 0.95
LH_PAGES = 3
CHROMES = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Chromium.app/Contents/MacOS/Chromium")


def get(url):
    """(status, headers, body) without raising on 4xx/5xx; status 0 on network error."""
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "gearbox-seo-check"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()
    except (urllib.error.URLError, OSError):
        return 0, {}, b""


class Page(HTMLParser):
    """Collects the SEO-relevant facts of one HTML page."""

    def __init__(self):
        super().__init__()
        self.urls, self.metas, self.jsonld = set(), {}, []
        self.title, self.canonical, self.h1, self.img_no_alt = None, None, 0, 0
        self._in_title, self._in_jsonld = False, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            if a.get(k):
                self.urls.add(a[k])
        if a.get("srcset"):
            self.urls.update(p.split()[0] for p in a["srcset"].split(",") if p.strip())
        if tag == "title":
            self._in_title, self.title = True, ""
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and "alt" not in a:
            self.img_no_alt += 1
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key:
                self.metas[key] = a.get("content") or ""
        elif tag == "link" and "canonical" in (a.get("rel") or "").lower().split():
            self.canonical = a.get("href") or ""
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_jsonld = True
            self.jsonld.append("")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_jsonld:
            self.jsonld[-1] += data


def internal(base, page, href):
    s = urlsplit(urljoin(page, href))
    if s.scheme not in ("http", "https") or s.netloc != urlsplit(base).netloc:
        return None
    return s._replace(fragment="").geturl()


def noindex(value):
    return bool(re.search(r"\b(noindex|none)\b", value or "", re.I))


def check(base, prod=False, banned=(), fetch=get):
    """Return (problems, pages, urls_checked). `fetch(url) -> (status, headers, body)`."""
    base = base.rstrip("/")
    problems = []
    status, _, body = fetch(base + "/sitemap.xml")
    if status != 200:
        return [f"sitemap.xml answers {status}"], [], 0
    # shortcut: a sitemap index (<sitemapindex>) is not followed; flat sitemaps only.
    # The sitemap holds production URLs: rebase each <loc> on the URL under test.
    pages = [base + (urlsplit(loc.strip()).path or "/")
             for loc in re.findall(r"<loc>(.*?)</loc>", body.decode("utf-8", "replace"), re.S)]
    if not pages:
        problems.append("sitemap.xml lists no page")

    seen, titles, descriptions = {}, {}, {}
    for page in pages:
        status, headers, body = fetch(page)
        seen[page] = status
        if status != 200:
            problems.append(f"{status} {page}")
            continue
        html = body.decode("utf-8", "replace")
        p = Page()
        p.feed(html)
        if prod and noindex(headers.get("x-robots-tag")):
            problems.append(f"x-robots-tag '{headers.get('x-robots-tag')}' on {page}")
        if prod and noindex(p.metas.get("robots")):
            problems.append(f"meta robots '{p.metas['robots']}' on {page}")
        title = (p.title or "").strip()
        if not title:
            problems.append(f"no <title> on {page}")
        else:
            titles.setdefault(title, []).append(page)
            if not TITLE_LEN[0] <= len(title) <= TITLE_LEN[1]:
                problems.append(f"title length {len(title)} outside {TITLE_LEN[0]}-{TITLE_LEN[1]} on {page}")
        desc = p.metas.get("description", "").strip()
        if not desc:
            problems.append(f"no meta description on {page}")
        else:
            descriptions.setdefault(desc, []).append(page)
        if p.h1 != 1:
            problems.append(f"{p.h1} <h1> on {page} (expected 1)")
        if not p.canonical:
            problems.append(f"no canonical on {page}")
        for prop in ("og:title", "og:image"):
            if not p.metas.get(prop):
                problems.append(f"no {prop} on {page}")
        for i, block in enumerate(p.jsonld, 1):
            try:
                json.loads(block)
            except ValueError as e:
                problems.append(f"JSON-LD block {i} does not parse on {page}: {e}")
        if p.img_no_alt:
            problems.append(f"{p.img_no_alt} <img> without alt on {page}")
        for pattern in banned:
            if re.search(pattern, html, re.I):
                problems.append(f"banned pattern '{pattern}' on {page}")
        for href in sorted(p.urls):
            u = internal(base, page, href)
            if u and u not in seen:
                seen[u] = fetch(u)[0]
                if seen[u] != 200:
                    problems.append(f"{seen[u]} {u} (linked from {page})")

    for label, index in (("title", titles), ("meta description", descriptions)):
        problems += [f"duplicate {label} '{v}' on {', '.join(ps)}" for v, ps in index.items() if len(ps) > 1]

    status, _, body = fetch(base + "/robots.txt")
    if status != 200:
        problems.append(f"/robots.txt answers {status}")
    elif prod and re.search(r"^\s*disallow:\s*/\s*$", body.decode("utf-8", "replace"), re.I | re.M):
        problems.append("robots.txt has 'Disallow: /' in production")
    status = fetch(base + "/llms.txt")[0]
    if status not in (200, 404):
        problems.append(f"/llms.txt answers {status}")
    missing = f"{base}/gearbox-missing-{uuid.uuid4().hex[:8]}"
    if (status := fetch(missing)[0]) != 404:
        problems.append(f"a missing page answers {status} instead of 404")
    return problems, pages, len(seen)


def lighthouse(base, pages, prod):
    """Problems from Lighthouse, or None when it cannot run here."""
    lh = shutil.which("lighthouse")
    chrome = os.environ.get("CHROME_PATH") or next(
        (c for c in (*CHROMES, shutil.which("google-chrome"), shutil.which("chromium")) if c and os.path.exists(c)), None)
    if not lh or not chrome:
        return None
    out = []
    for page in pages[:LH_PAGES]:
        r = subprocess.run([lh, page, "--quiet", "--chrome-flags=--headless=new", "--output=json"],
                           capture_output=True, text=True, env={**os.environ, "CHROME_PATH": chrome})
        try:
            scores = {k: c["score"] or 0 for k, c in json.loads(r.stdout)["categories"].items()}
        except (ValueError, KeyError):
            out.append(f"Lighthouse could not run on {page}: {r.stderr.strip()[-200:]}")
            continue
        print("Lighthouse", page, " ".join(f"{k}={round(v * 100)}" for k, v in scores.items()))
        # A preview's noindex sinks the SEO score: judge it on production only.
        out += [f"Lighthouse {k} = {round(v * 100)} on {page}" for k, v in scores.items()
                if v < LH_MIN and (prod or k != "seo")]
    return out


def load_banned(path):
    with open(path, encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    return [line for line in lines if line and not line.startswith("#")]


def main(argv):
    args = list(argv)
    banned = []
    if "--banned" in args:
        i = args.index("--banned")
        if i + 1 >= len(args):
            print(__doc__, file=sys.stderr)
            return 2
        banned = load_banned(args.pop(i + 1))
        args.pop(i)
    flags = {a for a in args if a.startswith("--")}
    rest = [a for a in args if not a.startswith("--")]
    if len(rest) != 1 or flags - {"--prod", "--lighthouse"}:
        print(__doc__, file=sys.stderr)
        return 2
    prod = "--prod" in flags
    problems, pages, checked = check(rest[0], prod=prod, banned=banned)
    if "--lighthouse" in flags:
        lh = lighthouse(rest[0].rstrip("/"), pages, prod)
        if lh is None:
            print("SKIP Lighthouse: `lighthouse` on PATH and a Chrome (or CHROME_PATH) are required")
        else:
            problems += lh
    print(f"{len(pages)} pages, {checked} internal URLs checked.")
    for p in problems:
        print("FAIL", p)
    print("OK" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
