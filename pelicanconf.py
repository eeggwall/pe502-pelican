"""Pelican settings for local builds. publishconf.py extends these."""

import os

here = os.path.dirname(os.path.abspath(__file__))

AUTHOR = "Charles Reid"
SITENAME = "PE502"
SITESUBTITLE = "Castle polyominoes, after Project Euler problem 502"
SITE_DESCRIPTION = (
    "Posts and numbered publications on castle polyominoes, "
    "after Project Euler problem 502."
)
SITEURL = ""
RELATIVE_URLS = False

PATH = "content"
ARTICLE_PATHS = ["posts"]
PAGE_PATHS = ["pages"]
STATIC_PATHS = ["extra/CNAME"]
EXTRA_PATH_METADATA = {"extra/CNAME": {"path": "CNAME"}}
THEME = "theme"

TIMEZONE = "America/Los_Angeles"
DEFAULT_LANG = "en"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

MARKDOWN = {
    "extension_configs": {"markdown.extensions.extra": {}},
    "output_format": "html5",
}
JINJA_ENVIRONMENT = {"autoescape": True}

# Posts need no Category line; categories have no public role.
USE_FOLDER_AS_CATEGORY = False
DEFAULT_CATEGORY = "posts"

ARTICLE_URL = "posts/{date:%Y}/{date:%m}/{slug}/"
ARTICLE_SAVE_AS = "posts/{date:%Y}/{date:%m}/{slug}/index.html"
DRAFT_URL = "drafts/{slug}/"
DRAFT_SAVE_AS = "drafts/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
INDEX_URL = ""

# Division tags link to division pages; no tag, category, author or archive pages.
DIRECT_TEMPLATES = ["index"]
TAG_SAVE_AS = ""
TAGS_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
AUTHOR_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
ARCHIVES_SAVE_AS = ""

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DEFAULT_PAGINATION = 10
PAGINATED_TEMPLATES = {"index": None, "division": None}
PAGINATION_PATTERNS = (
    (1, "{url}", "{save_as}"),
    (2, "{base_name}/page/{number}/", "{base_name}/page/{number}/index.html"),
)

PLUGIN_PATHS = ["plugins"]
PLUGINS = ["pe502_catalog"]

# Catalog export from the publications repository, copied in unchanged.
PE502_CATALOG = os.path.join(here, "data", "published.json")
# Divisions and publication annotations, owned by this repository.
PE502_SITE_DATA = os.path.join(here, "data", "site.json")

# Frozen documents, served from the publications repository at their tags.
PUBLICATION_FILE_URL = (
    "https://git.charlesreid1.com/eeggwall/pe502-pubs/raw/tag/{id}/{pdf}"
)
PUBLICATIONS_URL = "publications/"
PUBLICATIONS_SAVE_AS = "publications/index.html"
PUBLICATION_URL = "publications/{id}/"
PUBLICATION_SAVE_AS = "publications/{id}/index.html"
DIVISIONS_URL = "divisions/"
DIVISIONS_SAVE_AS = "divisions/index.html"
DIVISION_URL = "divisions/{slug}/"
DIVISION_SAVE_AS = "divisions/{slug}/index.html"
