"""Tests for the PE502 site: data validation, catalog joins, and generated output.

Run from the repository root with `make test`.
"""

import html.parser
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

from pelican import Pelican
from pelican.settings import read_settings

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "plugins"))

import pe502_catalog  # noqa: E402
from pe502_catalog import DataError  # noqa: E402


def settings_for(path, catalog, site_data, output=None, **overrides):
    return read_settings(
        str(ROOT / "pelicanconf.py"),
        override={
            "PATH": str(path),
            "OUTPUT_PATH": str(output or Path(path).parent / "output"),
            "PE502_CATALOG": str(catalog),
            "PE502_SITE_DATA": str(site_data),
            **overrides,
        },
    )


def record(n, **changes):
    return {
        "id": f"PE502-{n}",
        "number": n,
        "series": "Technical Report",
        "title": f"Report {n}",
        "date": "October 1, 2026",
        "published": f"2026-10-{n:02d}",
        "pdf": f"PE502-{n}.pdf",
        "sha256": "ab" * 32,
        "obsoletes": [],
        "obsoleted_by": [],
        **changes,
    }


def division(slug, label, **changes):
    return {
        "slug": slug,
        "label": label,
        "badge": slug.upper(),
        "name": f"{label} name",
        "blurb": f"About {label}.",
        "interests": [f"An interest of {label}."],
        **changes,
    }


DIVISIONS = [division("a", "A Division"), division("b", "B Division"),
             division("phone", "The Phone Company")]


def post(title, date, tags=None, body="Post body."):
    lines = [f"Title: {title}", f"Date: {date}"]
    if tags:
        lines.append(f"Tags: {tags}")
    return "\n".join(lines) + "\n\n" + body + "\n"


class Fixture:
    """A throwaway site: content, catalog and site data in a temporary directory."""

    def __init__(self, test, catalog=None, site=None, posts=None, pages=None):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.output = self.root / "output"
        self.catalog = self.write("data/published.json", catalog if catalog is not None else [record(1)])
        self.site = self.write("data/site.json", site if site is not None else {"divisions": DIVISIONS})
        for name, text in (posts or {}).items():
            self.write(f"content/posts/{name}", text)
        for name, text in (pages or {}).items():
            self.write(f"content/pages/{name}", text)
        (self.root / "content").mkdir(exist_ok=True)

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return path

    def settings(self, **overrides):
        return settings_for(self.root / "content", self.catalog, self.site, self.output,
                            STATIC_PATHS=[], **overrides)

    def build(self, **overrides):
        Pelican(self.settings(**overrides)).run()
        return self.output

    def load(self):
        errors = []
        divisions, publications = pe502_catalog.load(self.settings(), errors)
        return errors, divisions, publications

    def read(self, name):
        return (self.output / name).read_text(encoding="utf-8")


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("href", "src") and value:
                self.links.append(value)


def links_in(text):
    parser = Links()
    parser.feed(text)
    return parser.links


def target(output, page, link):
    """The output file an internal link points to, or None for external links."""
    if re.match(r"[a-z]+:", link) or link.startswith("#"):
        return None
    link = link.split("#")[0].split("?")[0]
    base = output if link.startswith("/") else page.parent
    path = base / link.lstrip("/")
    return path / "index.html" if link.endswith("/") or path.is_dir() else path


class ValidationTests(unittest.TestCase):
    def errors(self, catalog=None, site=None):
        return Fixture(self, catalog=catalog, site=site).load()[0]

    def assertError(self, errors, text):
        self.assertTrue(any(text in e for e in errors), f"no error containing {text!r} in {errors}")

    def test_valid_data_has_no_errors(self):
        site = {"divisions": DIVISIONS, "publications": {"PE502-1": {"divisions": ["A Division"]}}}
        self.assertEqual(self.errors([record(1), record(2)], site), [])

    def test_join_keeps_catalog_fields_and_adds_annotations(self):
        catalog = [record(1), record(2, extra_field="kept")]
        site = {"divisions": DIVISIONS, "publications": {
            "PE502-2": {"divisions": ["B Division", "A Division"], "summary": "S.", "abstract": "<p>A.</p>"}}}
        errors, divisions, pubs = Fixture(self, catalog=catalog, site=site).load()
        self.assertEqual(errors, [])
        by_id = {p.id: p for p in pubs}
        self.assertEqual([p.id for p in pubs], ["PE502-2", "PE502-1"])
        self.assertEqual(by_id["PE502-2"].record, catalog[1])
        for field in pe502_catalog.CATALOG_FIELDS:
            self.assertEqual(getattr(by_id["PE502-2"], field), catalog[1][field])
        self.assertEqual([d.label for d in by_id["PE502-2"].divisions], ["B Division", "A Division"])
        self.assertEqual((by_id["PE502-2"].summary, by_id["PE502-2"].abstract), ("S.", "<p>A.</p>"))
        self.assertEqual(by_id["PE502-2"].url, "publications/PE502-2/")
        self.assertEqual(by_id["PE502-2"].pdf_url,
                         "https://git.charlesreid1.com/eeggwall/pe502-pubs/raw/tag/PE502-2/PE502-2.pdf")
        # A record with no annotation still renders, with empty annotations.
        self.assertEqual((by_id["PE502-1"].divisions, by_id["PE502-1"].summary,
                          by_id["PE502-1"].abstract), ([], None, None))
        self.assertEqual([p.id for p in divisions[0].publications], ["PE502-2"])

    def test_malformed_json(self):
        fixture = Fixture(self)
        fixture.write("data/site.json", '{"divisions": [')
        errors, _, _ = fixture.load()
        self.assertError(errors, "site.json")

    def test_duplicate_json_keys(self):
        fixture = Fixture(self)
        fixture.write("data/site.json", '{"divisions": [], "publications": {"PE502-1": {}, "PE502-1": {}}}')
        self.assertError(fixture.load()[0], "duplicate key 'PE502-1'")

    def test_missing_and_mistyped_catalog_fields(self):
        broken = record(1, number="1")
        del broken["sha256"]
        errors = self.errors([broken, record(2, obsoletes="PE502-1"), record(3, sha256="xyz")])
        self.assertError(errors, "record 1 (PE502-1): missing field 'sha256'")
        self.assertError(errors, "field 'number' must be an integer")
        self.assertError(errors, "(PE502-2): field 'obsoletes' must be a list")
        self.assertError(errors, "(PE502-3): sha256 must be 64 lowercase hex digits")

    def test_bad_published_date(self):
        errors = self.errors([record(1, published="October 1, 2026"), record(2, published="2026-02-30")])
        self.assertError(errors, "published must be a YYYY-MM-DD date")
        self.assertError(errors, "published is not a real date")

    def test_noncanonical_accession_numbers(self):
        for rid in ("PE502-01", "pe502-1", "PE502-M-1", "PE502-TR-1", "PE502-0"):
            with self.subTest(rid=rid):
                self.assertError(self.errors([record(1, id=rid)]), "not a canonical accession number")

    def test_duplicate_accession_numbers(self):
        self.assertError(self.errors([record(1), record(1, title="Again")]),
                         "duplicate accession number PE502-1")

    def test_number_must_match_id(self):
        self.assertError(self.errors([record(1, number=2)]), "number 2 does not match the id")

    def test_replacement_links_must_resolve_both_ways(self):
        errors = self.errors([record(1, obsoleted_by=["PE502-2"]), record(2), record(3, obsoletes=["PE502-9"])])
        self.assertError(errors, "PE502-1 obsoleted_by PE502-2, but PE502-2 does not list PE502-1 in obsoletes")
        self.assertError(errors, "PE502-3 obsoletes PE502-9, which is not in the catalog")

    def test_duplicate_division_slug_and_label(self):
        site = {"divisions": [division("a", "A Division"), division("a", "Other"),
                              division("c", "a division")]}
        errors = self.errors(site=site)
        self.assertError(errors, "slug 'a' is already used")
        self.assertError(errors, "label 'a division' is already used")

    def test_bad_division_slug_and_fields(self):
        site = {"divisions": [division("A Div", "A Division"), division("b", "B", sidecar="x"),
                              {"slug": "c", "label": "C"}]}
        errors = self.errors(site=site)
        self.assertError(errors, "slug 'A Div' must be lowercase")
        self.assertError(errors, "division 2: unknown field 'sidecar'")
        self.assertError(errors, "division 3: missing field 'blurb'")

    def test_unknown_division_in_annotation(self):
        site = {"divisions": DIVISIONS, "publications": {
            "PE502-1": {"divisions": ["A Division", "Z Division", "A Division"]}}}
        errors = self.errors(site=site)
        self.assertError(errors, "unknown division 'Z Division'")
        self.assertError(errors, "division 'A Division' listed more than once")

    def test_annotation_for_absent_publication(self):
        site = {"divisions": DIVISIONS, "publications": {"PE502-7": {}, "PE502-07": {}}}
        errors = self.errors(site=site)
        self.assertError(errors, "publication PE502-7: not in the catalog")
        self.assertError(errors, "publication PE502-07: not a canonical accession number")

    def test_annotation_has_no_sidecar_field(self):
        site = {"divisions": DIVISIONS, "publications": {"PE502-1": {"sidecar": "https://1.pe502.com"}}}
        self.assertError(self.errors(site=site), "unknown field 'sidecar'")

    def test_annotation_cannot_override_catalog_field(self):
        site = {"divisions": DIVISIONS, "publications": {"PE502-1": {"title": "Other"}}}
        self.assertError(self.errors(site=site), "unknown field 'title'")
        catalog = [record(1, summary="From the catalog")]
        site = {"divisions": DIVISIONS, "publications": {"PE502-1": {"summary": "Local"}}}
        self.assertError(self.errors(catalog, site), "'summary' is a catalog field")

    def test_unknown_top_level_field(self):
        self.assertError(self.errors(site={"divisions": DIVISIONS, "publication": {}}),
                         "unknown field 'publication'")


class BuildTests(unittest.TestCase):
    def test_pagination_newest_first(self):
        posts = {f"2026-10-post-{n}.md": post(f"Post {n}", f"2026-10-{n:02d}", "A Division")
                 for n in range(1, 6)}
        fixture = Fixture(self, posts=posts)
        out = fixture.build(DEFAULT_PAGINATION=2)
        pages = ["index.html", "page/2/index.html", "page/3/index.html"]
        dates = [re.findall(r'<time datetime="([^"]+)"', fixture.read(p)) for p in pages]
        self.assertEqual(dates, [["2026-10-05", "2026-10-04"], ["2026-10-03", "2026-10-02"],
                                 ["2026-10-01"]])
        self.assertFalse((out / "page/4").exists())
        self.assertIn('href="/page/2/" rel="next"', fixture.read("index.html"))
        self.assertIn('href="/" rel="prev"', fixture.read("page/2/index.html"))
        # Division pages paginate their posts the same way.
        self.assertTrue((out / "divisions/a/page/3/index.html").exists())
        self.assertIn('href="/divisions/a/page/2/" rel="next"', fixture.read("divisions/a/index.html"))

    def test_empty_division_page(self):
        fixture = Fixture(self)
        fixture.build()
        page = fixture.read("divisions/phone/index.html")
        self.assertIn("No posts are tagged with this division yet.", page)
        self.assertIn("No publications are tagged with this division yet.", page)
        self.assertIn("An interest of The Phone Company.", page)
        self.assertIn("nothing posted yet", fixture.read("divisions/index.html"))

    def test_posts_and_publications_stay_separate(self):
        site = {"divisions": DIVISIONS, "publications": {
            "PE502-1": {"divisions": ["A Division"], "summary": "Summary of one."}}}
        posts = {"2026-10-news.md": post("News", "2026-10-02", "A Division, The Phone Company"),
                 "2026-10-site.md": post("Site update", "2026-10-03")}
        fixture = Fixture(self, site=site, posts=posts)
        fixture.build()
        home = fixture.read("index.html")
        self.assertEqual(home.count('class="printout"'), 2)
        self.assertNotIn('class="entry"', home)
        self.assertNotIn("Report 1", home)
        division_a = fixture.read("divisions/a/index.html")
        self.assertIn("Summary of one.", division_a)
        self.assertIn(">News<", division_a)
        self.assertNotIn("Site update", division_a)
        self.assertLess(division_a.index("Publications"), division_a.index("Posts"))
        # Tags render as readable labels linking to division pages.
        news = fixture.read("posts/2026/10/news/index.html")
        self.assertIn('Filed under <a href="/divisions/a/">A Division</a>, '
                      '<a href="/divisions/phone/">The Phone Company</a>', news)
        # An untagged post is a site-wide update on no division page.
        self.assertNotIn("Filed under", fixture.read("posts/2026/10/site-update/index.html"))
        for slug in ("a", "b", "phone"):
            self.assertNotIn("Site update", fixture.read(f"divisions/{slug}/index.html"))

    def test_unannotated_publication_renders(self):
        fixture = Fixture(self, catalog=[record(1, title="Fresh Report")])
        fixture.build()
        page = fixture.read("publications/PE502-1/index.html")
        self.assertIn("Fresh Report", page)
        self.assertNotIn("<dt>Divisions</dt>", page)
        self.assertNotIn("Abstract", page)
        self.assertIn("Fresh Report", fixture.read("publications/index.html"))

    def test_superseded_publication_stays_reachable(self):
        catalog = [record(1, obsoleted_by=["PE502-2"]), record(2, series="Errata", obsoletes=["PE502-1"])]
        fixture = Fixture(self, catalog=catalog)
        fixture.build()
        old = fixture.read("publications/PE502-1/index.html")
        self.assertIn('replaced by <a href="/publications/PE502-2/">PE502-2</a>', old)
        self.assertIn("<dt>Replaced by</dt>", old)
        self.assertIn('<dt>Replaces</dt><dd><a href="/publications/PE502-1/">PE502-1</a>',
                      fixture.read("publications/PE502-2/index.html"))
        self.assertIn('href="/publications/PE502-1/">PE502-1</a>', fixture.read("publications/index.html"))

    def test_unknown_post_tag_fails(self):
        fixture = Fixture(self, posts={"2026-10-x.md": post("X", "2026-10-01", "A Division, Q Division")})
        with self.assertRaises(DataError) as caught:
            fixture.build()
        self.assertIn("unknown division tag 'Q Division'", str(caught.exception))
        self.assertIn("known division tags: A Division, B Division, The Phone Company",
                      str(caught.exception))

    def test_post_file_name_and_date(self):
        posts = {"2026-10-late.md": post("Late", "2026-11-01"), "Notes.md": post("Notes", "2026-10-01")}
        with self.assertRaises(DataError) as caught:
            Fixture(self, posts=posts).build()
        self.assertIn("Date 2026-11-01 is not in 2026-10", str(caught.exception))
        self.assertIn("Notes.md: post file names follow YYYY-MM-post-title.md", str(caught.exception))

    def test_conflicting_output_paths_fail(self):
        pages = {"catalog.md": "Title: Catalog\nSlug: publications\n\nText.\n"}
        with self.assertRaises(DataError) as caught:
            Fixture(self, pages=pages).build()
        self.assertIn("output path publications/index.html is claimed by both", str(caught.exception))

    def test_bad_data_fails_the_build(self):
        with self.assertRaises(DataError):
            Fixture(self, catalog=[record(1), record(1)]).build()


class RealSiteTests(unittest.TestCase):
    """Builds this repository's own content and data."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name)
        settings = settings_for(ROOT / "content", ROOT / "data/published.json",
                                ROOT / "data/site.json", cls.output)
        Pelican(settings).run()
        cls.catalog = json.loads((ROOT / "data/published.json").read_text(encoding="utf-8"))
        cls.site = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
        cls.posts = sorted((ROOT / "content/posts").glob("*.md"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, name):
        return (self.output / name).read_text(encoding="utf-8")

    def html_files(self):
        return sorted(self.output.rglob("*.html"))

    def test_expected_pages_exist(self):
        names = ["index.html", "404.html", "about/index.html", "publications/index.html",
                 "divisions/index.html"]
        names += [f"publications/{r['id']}/index.html" for r in self.catalog]
        names += [f"divisions/{d['slug']}/index.html" for d in self.site["divisions"]]
        for name in names:
            self.assertTrue((self.output / name).is_file(), name)

    def test_no_tag_category_or_author_pages(self):
        top = {p.name for p in self.output.iterdir()}
        self.assertEqual(top, {"index.html", "404.html", "CNAME", "about", "divisions", "posts",
                               "publications", "theme"})
        self.assertEqual(len(list((self.output / "divisions").iterdir())),
                         len(self.site["divisions"]) + 1)

    def test_internal_links_resolve(self):
        for page in self.html_files():
            for link in links_in(page.read_text(encoding="utf-8")):
                path = target(self.output, page, link)
                if path is not None:
                    self.assertTrue(path.is_file(), f"{page.relative_to(self.output)}: {link}")

    def test_no_javascript(self):
        for page in self.html_files():
            text = page.read_text(encoding="utf-8")
            self.assertNotIn("<script", text, page)
            self.assertNotRegex(text, r"<[^>]*\son[a-z]+=", page)

    def test_homepage_is_the_post_stream(self):
        home = self.read("index.html")
        self.assertEqual(home.count('class="printout"'), len(self.posts))
        self.assertNotIn('class="entry"', home)
        dates = re.findall(r'<time datetime="([^"]+)"', home)
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_tags_link_to_division_pages(self):
        for page in (self.output / "posts").rglob("index.html"):
            sig = re.search(r'<p class="sig">(.*?)</p>', page.read_text(encoding="utf-8"))
            if sig:
                for link in links_in(sig.group(1)):
                    self.assertRegex(link, r"^/divisions/[a-z0-9-]+/$")
                    self.assertTrue(target(self.output, page, link).is_file(), link)

    def test_catalog_fields_rendered_unchanged(self):
        catalog_page = self.read("publications/index.html")
        for r in self.catalog:
            page = self.read(f"publications/{r['id']}/index.html")
            for field in ("id", "series", "title", "date", "published", "pdf", "sha256"):
                self.assertIn(str(r[field]), page, f"{r['id']} {field}")
            self.assertIn(r["id"], catalog_page)
        ids = re.findall(r'<td class="id"><a href="/publications/([^/]+)/">', catalog_page)
        self.assertEqual(ids, [r["id"] for r in sorted(self.catalog, key=lambda r: -r["number"])])


if __name__ == "__main__":
    unittest.main()
