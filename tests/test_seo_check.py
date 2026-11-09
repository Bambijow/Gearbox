from __future__ import annotations

import unittest

from scripts import seo_check as sc

BASE = "https://preview.example.dev"


def page(title="Plombier à Lyon — Dupont", desc="Dépannage plomberie à Lyon.", h1=1, extra="", jsonld='{"@type": "Plumber"}'):
    return f"""<!doctype html><html><head><title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="https://www.example.fr/">
<meta property="og:title" content="{title}"><meta property="og:image" content="/og.png">
<script type="application/ld+json">{jsonld}</script></head>
<body>{"<h1>Titre</h1>" * h1}<img src="/a.webp" srcset="/a.webp 1x, /a@2x.webp 2x" alt="">
<a href="/contact/">Contact</a><a href="https://other.example.com/x">ext</a>{extra}</body></html>"""


class FakeSite:
    """In-memory site: path -> (status, headers, body); unknown paths answer 404."""

    def __init__(self, **overrides):
        sitemap = "<urlset><url><loc>https://www.example.fr/</loc></url><url><loc>https://www.example.fr/contact/</loc></url></urlset>"
        self.routes = {
            "/sitemap.xml": (200, {}, sitemap),
            "/": (200, {}, page()),
            "/contact/": (200, {}, page(title="Contact — Dupont plomberie", desc="Écrire à Dupont.")),
            "/robots.txt": (200, {}, "User-agent: *\nAllow: /\nSitemap: https://www.example.fr/sitemap.xml\n"),
            "/og.png": (200, {}, ""), "/a.webp": (200, {}, ""), "/a@2x.webp": (200, {}, ""),
        }
        self.routes.update(overrides)
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        path = url[len(BASE):] or "/"
        status, headers, body = self.routes.get(path, (404, {}, "not found"))
        return status, headers, body.encode()


def run(site, **kw):
    return sc.check(BASE, fetch=site, **kw)[0]


class SeoCheckTests(unittest.TestCase):
    def test_clean_site_passes_and_rebases_sitemap_on_tested_url(self):
        site = FakeSite()
        problems, pages, checked = sc.check(BASE + "/", prod=True, fetch=site)
        self.assertEqual(problems, [])
        self.assertEqual(pages, [BASE + "/", BASE + "/contact/"])
        self.assertIn(BASE + "/a@2x.webp", site.calls)  # srcset followed
        self.assertNotIn("https://other.example.com/x", site.calls)  # external not fetched
        self.assertEqual(checked, 4)  # 2 pages + 2 images

    def test_missing_page_must_answer_404(self):
        site = FakeSite()
        real = site.__call__
        soft = lambda url: (200, {}, b"home") if "gearbox-missing-" in url else real(url)
        self.assertIn("a missing page answers 200 instead of 404", run(soft))

    def test_duplicate_title_fails(self):
        problems = run(FakeSite(**{"/contact/": (200, {}, page(desc="Autre description."))}))
        self.assertTrue(any(p.startswith("duplicate title") for p in problems), problems)

    def test_noindex_fails_only_in_prod(self):
        site = FakeSite(**{"/": (200, {"x-robots-tag": "noindex"}, page())})
        self.assertEqual(run(site), [])
        self.assertTrue(any("x-robots-tag" in p for p in run(site, prod=True)))
        meta = FakeSite(**{"/": (200, {}, page(extra='<meta name="robots" content="noindex, follow">'))})
        self.assertTrue(any("meta robots" in p for p in run(meta, prod=True)))

    def test_broken_internal_link_fails(self):
        problems = run(FakeSite(**{"/": (200, {}, page(extra='<a href="/gone/">x</a>'))}))
        self.assertIn(f"404 {BASE}/gone/ (linked from {BASE}/)", problems)

    def test_invalid_jsonld_fails(self):
        problems = run(FakeSite(**{"/": (200, {}, page(jsonld='{"@type": "Plumber",}'))}))
        self.assertTrue(any("JSON-LD block 1 does not parse" in p for p in problems), problems)

    def test_page_content_rules(self):
        bad = page(title="Court", desc="", h1=2, extra='<img src="/a.webp">')
        problems = run(FakeSite(**{"/": (200, {}, bad.replace('<link rel="canonical" href="https://www.example.fr/">', ""))}))
        for expected in ("title length 5", "no meta description", "2 <h1>", "no canonical", "1 <img> without alt"):
            self.assertTrue(any(expected in p for p in problems), (expected, problems))

    def test_banned_pattern_blocks(self):
        site = FakeSite(**{"/": (200, {}, page(extra="<p>Avis clients : 4,9/5</p>"))})
        self.assertIn(f"banned pattern 'avis clients?' on {BASE}/", run(site, banned=["avis clients?"]))

    def test_robots_and_llms(self):
        self.assertIn("/robots.txt answers 404", run(FakeSite(**{"/robots.txt": (404, {}, "")})))
        closed = FakeSite(**{"/robots.txt": (200, {}, "User-agent: *\nDisallow: /\n")})
        self.assertEqual(run(closed), [])
        self.assertIn("robots.txt has 'Disallow: /' in production", run(closed, prod=True))
        self.assertIn("/llms.txt answers 500", run(FakeSite(**{"/llms.txt": (500, {}, "")})))

    def test_missing_sitemap_stops(self):
        self.assertEqual(run(FakeSite(**{"/sitemap.xml": (404, {}, "")})), ["sitemap.xml answers 404"])

    def test_cli_usage_and_banned_file_comments(self):
        self.assertEqual(sc.main([]), 2)
        self.assertEqual(sc.main([BASE, "--bogus"]), 2)
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("# claims\n\ntémoignage\n")
        self.assertEqual(sc.load_banned(f.name), ["témoignage"])


if __name__ == "__main__":
    unittest.main()
