"""PE502 build-time integration: the publication catalog, divisions, and posts.

Reads the catalog (an unchanged export from the publications repository) and
the site-owned metadata in data/site.json, validates both, joins annotations to
catalog records by accession number, resolves post tags to divisions, and
writes the catalog, publication, division index and division pages.
"""

import datetime
import json
import os
import re

from pelican import signals
from pelican.generators import Generator
from pelican.paginator import Paginator

ID_RE = re.compile(r"PE502-([1-9][0-9]*)")
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ISO_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
POST_NAME_RE = re.compile(r"([0-9]{4})-([0-9]{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md")
H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.S)

# Every field the site reads from a catalog record. Records may carry more.
CATALOG_FIELDS = {
    "id": str,
    "number": int,
    "series": str,
    "title": str,
    "date": str,
    "published": str,
    "pdf": str,
    "sha256": str,
    "obsoletes": list,
    "obsoleted_by": list,
}
DIVISION_FIELDS = {
    "slug": str,
    "label": str,
    "badge": str,
    "name": str,
    "blurb": str,
    "interests": list,
}
ANNOTATION_FIELDS = {"divisions": list, "summary": str, "abstract": str}


class DataError(Exception):
    """The catalog, the site metadata and the posts do not fit together."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("\n  ".join(["PE502 site data is invalid:", *errors]))


class Division:
    def __init__(self, entry, settings):
        self.slug = entry["slug"]
        self.label = entry["label"]
        self.badge = entry["badge"]
        self.name = entry["name"]
        self.blurb = entry["blurb"]
        self.interests = entry["interests"]
        self.url = settings["DIVISION_URL"].format(slug=self.slug)
        self.save_as = settings["DIVISION_SAVE_AS"].format(slug=self.slug)
        self.posts = []
        self.publications = []


class Publication:
    """A catalog record with its site annotation alongside.

    ``record`` is the catalog entry exactly as exported; the catalog fields are
    copied onto the object for templates and never written back.
    """

    def __init__(self, record, annotation, divisions, settings):
        self.record = record
        for field in CATALOG_FIELDS:
            setattr(self, field, record[field])
        self.divisions = divisions
        self.summary = annotation.get("summary")
        self.abstract = annotation.get("abstract")
        self.url = settings["PUBLICATION_URL"].format(id=self.id)
        self.save_as = settings["PUBLICATION_SAVE_AS"].format(id=self.id)
        self.pdf_url = settings["PUBLICATION_FILE_URL"].format(id=self.id, pdf=self.pdf)
        self.replaces = []
        self.replaced_by = []


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key {key!r}")
        obj[key] = value
    return obj


def read_json(path, errors):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=_unique_keys)
    except OSError as e:
        errors.append(f"{path}: cannot read: {e.strerror}")
    except ValueError as e:
        errors.append(f"{path}: {e}")
    return None


def check_fields(where, obj, fields, required, errors, extra_ok=False):
    """Append an error for each missing, mistyped or unknown field of obj."""
    if not isinstance(obj, dict):
        errors.append(f"{where}: expected a JSON object")
        return False
    count = len(errors)
    for name in sorted(set(required) - obj.keys()):
        errors.append(f"{where}: missing field {name!r}")
    if not extra_ok:
        for name in sorted(obj.keys() - fields.keys()):
            errors.append(f"{where}: unknown field {name!r}")
    for name, kind in fields.items():
        if name not in obj:
            continue
        value = obj[name]
        if kind is int:
            good, want = type(value) is int, "an integer"
        elif kind is list:
            good = isinstance(value, list) and all(
                isinstance(v, str) and v.strip() for v in value
            )
            want = "a list of non-empty strings"
        else:
            good, want = isinstance(value, str) and value.strip(), "a non-empty string"
        if not good:
            errors.append(f"{where}: field {name!r} must be {want}")
    return len(errors) == count


def load_catalog(path, errors):
    """Return the valid catalog records, keyed by accession number."""
    data = read_json(path, errors)
    if data is None:
        return {}
    if not isinstance(data, list):
        errors.append(f"{path}: expected a list of publication records")
        return {}
    records = {}
    for i, record in enumerate(data, 1):
        where = f"{path}: record {i}"
        if isinstance(record, dict) and isinstance(record.get("id"), str):
            where += f" ({record['id']})"
        if not check_fields(where, record, CATALOG_FIELDS, CATALOG_FIELDS, errors, True):
            continue
        rid = record["id"]
        m = ID_RE.fullmatch(rid)
        if not m:
            errors.append(f"{where}: id is not a canonical accession number like PE502-1")
            continue
        if int(m.group(1)) != record["number"]:
            errors.append(f"{where}: number {record['number']} does not match the id")
        if not ISO_DATE_RE.fullmatch(record["published"]):
            errors.append(f"{where}: published must be a YYYY-MM-DD date")
        else:
            try:
                datetime.date.fromisoformat(record["published"])
            except ValueError:
                errors.append(f"{where}: published is not a real date")
        if not SHA256_RE.fullmatch(record["sha256"]):
            errors.append(f"{where}: sha256 must be 64 lowercase hex digits")
        if rid in records:
            errors.append(f"{where}: duplicate accession number {rid}")
            continue
        records[rid] = record
    for rid, record in records.items():
        for field, inverse in (("obsoletes", "obsoleted_by"), ("obsoleted_by", "obsoletes")):
            for other in record[field]:
                if other not in records:
                    errors.append(f"{path}: {rid} {field} {other}, which is not in the catalog")
                elif rid not in records[other][inverse]:
                    errors.append(
                        f"{path}: {rid} {field} {other}, but {other} does not list {rid} in {inverse}"
                    )
    return records


def load_site(path, errors):
    """Return the valid division entries and the publication annotations."""
    data = read_json(path, errors)
    if data is None:
        return [], {}
    if not isinstance(data, dict):
        errors.append(f"{path}: expected a JSON object")
        return [], {}
    for name in sorted(data.keys() - {"divisions", "publications"}):
        errors.append(f"{path}: unknown field {name!r}")
    entries = data.get("divisions")
    if not isinstance(entries, list):
        errors.append(f"{path}: 'divisions' must be a list")
        entries = []
    annotations = data.get("publications", {})
    if not isinstance(annotations, dict):
        errors.append(f"{path}: 'publications' must be an object keyed by accession number")
        annotations = {}

    valid, slugs, labels = [], {}, {}
    for i, entry in enumerate(entries, 1):
        where = f"{path}: division {i}"
        if not check_fields(where, entry, DIVISION_FIELDS, DIVISION_FIELDS, errors):
            continue
        slug, label = entry["slug"], entry["label"]
        if not SLUG_RE.fullmatch(slug):
            errors.append(f"{where}: slug {slug!r} must be lowercase letters, digits and hyphens")
            continue
        if slug in slugs:
            errors.append(f"{where}: slug {slug!r} is already used by {slugs[slug]!r}")
            continue
        if label.casefold() in labels:
            errors.append(f"{where}: label {label!r} is already used by {labels[label.casefold()]!r}")
            continue
        slugs[slug] = labels[label.casefold()] = label
        valid.append(entry)
    return valid, annotations


def load(settings, errors):
    """Load, validate and join the catalog and site metadata.

    Returns the divisions in display order and the publications newest first.
    """
    records = load_catalog(settings["PE502_CATALOG"], errors)
    path = settings["PE502_SITE_DATA"]
    entries, annotations = load_site(path, errors)
    divisions = [Division(entry, settings) for entry in entries]
    by_label = {d.label: d for d in divisions}

    for rid, annotation in annotations.items():
        where = f"{path}: publication {rid}"
        if not ID_RE.fullmatch(rid):
            errors.append(f"{where}: not a canonical accession number like PE502-1")
        elif rid not in records:
            errors.append(f"{where}: not in the catalog")
        elif check_fields(where, annotation, ANNOTATION_FIELDS, (), errors):
            for field in sorted(annotation.keys() & records[rid].keys()):
                errors.append(f"{where}: {field!r} is a catalog field; the catalog value stands")
            labels = annotation.get("divisions", [])
            for label in labels:
                if label not in by_label:
                    errors.append(f"{where}: unknown division {label!r}")
            for label in sorted({x for x in labels if labels.count(x) > 1}):
                errors.append(f"{where}: division {label!r} listed more than once")

    publications = {}
    for rid, record in records.items():
        annotation = annotations.get(rid)
        if not isinstance(annotation, dict):
            annotation = {}
        assigned = [by_label[x] for x in annotation.get("divisions", []) if x in by_label]
        publications[rid] = Publication(record, annotation, assigned, settings)
    for pub in publications.values():
        pub.replaces = [publications[x] for x in pub.obsoletes if x in publications]
        pub.replaced_by = [publications[x] for x in pub.obsoleted_by if x in publications]

    ordered = sorted(publications.values(), key=lambda p: p.number, reverse=True)
    for pub in ordered:
        for division in pub.divisions:
            division.publications.append(pub)
    return divisions, ordered


def attach_posts(context, divisions, errors):
    """Resolve each post's tags to divisions and fill the division post lists."""
    by_label = {d.label: d for d in divisions}
    published = context.get("articles", [])
    posts = [*published, *context.get("hidden_articles", []), *context.get("drafts", [])]
    posts += [t for p in list(posts) for t in getattr(p, "translations", [])]
    unknown = False
    for post in posts:
        source = post.relative_source_path
        found = []
        for tag in getattr(post, "tags", []):
            division = by_label.get(tag.name)
            if division is None:
                errors.append(f"{source}: unknown division tag {tag.name!r}")
                unknown = True
            elif division not in found:
                found.append(division)
        post.divisions = found
        m = POST_NAME_RE.fullmatch(os.path.basename(source))
        if not m:
            errors.append(f"{source}: post file names follow YYYY-MM-post-title.md")
        elif "date" in post.metadata and (int(m.group(1)), int(m.group(2))) != (
            post.date.year, post.date.month
        ):
            errors.append(
                f"{source}: Date {post.date:%Y-%m-%d} is not in {m.group(1)}-{m.group(2)}, "
                "the month in the file name"
            )
    if unknown:
        errors.append("known division tags: " + ", ".join(d.label for d in divisions))
    for post in published:
        for division in post.divisions:
            division.posts.append(post)


def paginated_paths(settings, template, save_as, url, objects):
    """Every output path the writer produces for one, possibly paginated, page."""
    if template not in settings["PAGINATED_TEMPLATES"]:
        return [save_as]
    per_page = settings["PAGINATED_TEMPLATES"][template] or settings["DEFAULT_PAGINATION"]
    paginator = Paginator(save_as, url, objects, settings, per_page)
    return [paginator.page(n).save_as for n in paginator.page_range]


def check_output_paths(context, settings, divisions, publications, errors):
    """Report any two outputs that would be written to the same file."""
    claims = []
    for key in ("articles", "hidden_articles", "drafts", "pages", "hidden_pages", "draft_pages"):
        for content in context.get(key, []):
            for item in (content, *getattr(content, "translations", [])):
                claims.append((item.save_as, item.relative_source_path))
    if "index" in settings["DIRECT_TEMPLATES"]:
        index = paginated_paths(
            settings, "index", settings["INDEX_SAVE_AS"], settings["INDEX_URL"],
            context.get("articles", []),
        )
        claims += [(path, "the homepage") for path in index]
    claims.append((settings["PUBLICATIONS_SAVE_AS"], "the publication catalog"))
    claims += [(p.save_as, f"publication {p.id}") for p in publications]
    claims.append((settings["DIVISIONS_SAVE_AS"], "the division index"))
    for d in divisions:
        paths = paginated_paths(settings, "division", d.save_as, d.url, d.posts)
        claims += [(path, f"division {d.label!r}") for path in paths]

    owners = {}
    for path, owner in claims:
        if not path:
            continue
        key = os.path.normpath(path).casefold()
        if key in owners and owners[key] != owner:
            errors.append(f"output path {path} is claimed by both {owners[key]} and {owner}")
        owners.setdefault(key, owner)


def windows(html):
    """Split rendered page HTML at its <h2> headings into (heading, body) pairs.

    The text before the first heading comes back with heading None. Tables are
    wrapped so they scroll sideways on narrow screens.
    """
    html = html.replace("<table>", '<div class="scroll"><table>')
    html = html.replace("</table>", "</table></div>")
    parts = H2_RE.split(html)
    sections = [(None, parts[0]), *zip(parts[1::2], parts[2::2])]
    return [(heading, body) for heading, body in sections if heading or body.strip()]


class CatalogGenerator(Generator):
    """Join the site data, resolve post tags, and write the catalog and division pages."""

    def generate_context(self):
        errors = []
        self.divisions, self.publications = load(self.settings, errors)
        if not errors:
            attach_posts(self.context, self.divisions, errors)
            check_output_paths(
                self.context, self.settings, self.divisions, self.publications, errors
            )
        if errors:
            raise DataError(errors)
        self.context["divisions"] = self.divisions
        self.context["publications"] = self.publications

    def generate_output(self, writer):
        s = self.settings
        rel = s["RELATIVE_URLS"]
        writer.write_file(
            s["PUBLICATIONS_SAVE_AS"], self.get_template("publications"), self.context,
            rel, url=s["PUBLICATIONS_URL"],
        )
        for pub in self.publications:
            writer.write_file(
                pub.save_as, self.get_template("publication"), self.context,
                rel, url=pub.url, publication=pub,
            )
        writer.write_file(
            s["DIVISIONS_SAVE_AS"], self.get_template("divisions"), self.context,
            rel, url=s["DIVISIONS_URL"],
        )
        for division in self.divisions:
            writer.write_file(
                division.save_as, self.get_template("division"), self.context,
                rel, paginated={"articles": division.posts}, template_name="division",
                url=division.url, division=division,
            )


def get_generators(pelican):
    return CatalogGenerator


def add_filters(generator):
    generator.env.filters["windows"] = windows


def register():
    signals.get_generators.connect(get_generators)
    signals.generator_init.connect(add_filters)
