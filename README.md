# pe502.com

Pelican source for pe502.com: dated posts, the catalog of numbered publications, and division pages. Everything is generated at build time into plain HTML; the site needs no JavaScript.

## Layout

```
pelicanconf.py           # settings for local builds
publishconf.py           # settings for the deployable build (SITEURL https://pe502.com)
content/posts/           # posts, YYYY-MM-post-title.md
content/pages/           # home.md (homepage intro), about.md, 404.md
content/extra/CNAME      # copied to output/CNAME for GitHub Pages
data/published.json      # catalog export from pe502-pubs, copied in unchanged
data/site.json           # divisions and publication annotations, owned here
plugins/pe502_catalog/   # loads, validates and joins the data; writes catalog and division pages
theme/                   # templates and CSS
tests/                   # make test
single-page-app/         # the original prototype, kept as the design reference
```

## Building

You need Python 3 and the packages in `requirements.txt` (`python3 -m pip install -r requirements.txt`).

```sh
make html       # build into output/
make serve      # build, rebuild on changes, serve at http://127.0.0.1:8000
make test       # validation, join and output tests
make publish    # deployable build into output/, with SITEURL https://pe502.com
make clean      # remove output/
```

A build stops with a list of problems when the data does not fit together: an unknown division tag, a duplicate accession number, an annotation for a publication that is not in the catalog, two pages written to the same path, and so on.

## Adding a post

Create `content/posts/YYYY-MM-post-title.md`:

```markdown
Title: Ridge castles climb the metallic ladder
Date: 2026-10-04
Slug: ridge-castles-climb-the-metallic-ladder
Tags: M Division, N Division

Post content goes here.
```

- `Date` is the exact date; it must fall in the month the file name gives. The post's address is `/posts/YYYY/MM/slug/`, so set `Slug` and leave it alone once the post is up.
- `Tags` takes division labels exactly as `data/site.json` spells them (`M Division`, `The Telephone Company`). A post with no `Tags` is a site-wide update. No `Category` line is needed.
- A post announcing a publication carries the same divisions as the publication, and links to it as `/publications/PE502-N/`. Publications never appear in the post stream on their own.
- A post can announce and link to a sidecar app. Sidecars live in their own repositories and on their own subdomains; nothing about them is recorded here.

## Refreshing the catalog

`data/published.json` is a copy of the catalog in the publications repository, which is written by `make publish` there. Refresh it by copying the current export over it, unchanged:

```sh
curl -fsS https://git.charlesreid1.com/eeggwall/pe502-pubs/raw/branch/main/published.json -o data/published.json
```

Never edit it here: accession numbers, series, titles, dates, hashes and replacement links all come from the publications repository. A new record builds right away, with no divisions or summary until it is annotated.

PDF links point at each publication's tag in the publications repository (`PUBLICATION_FILE_URL` in `pelicanconf.py`), so they always serve the file as it was frozen.

## Annotating publications

Annotations live under `publications` in `data/site.json`, keyed by accession number:

```json
"PE502-2": {
  "divisions": ["M Division", "E Division", "Q Division"],
  "summary": "One or two sentences of HTML for listings.",
  "abstract": "<p>HTML for the publication page.</p>"
}
```

All three fields are optional. They add to the catalog record and cannot repeat one of its fields. Changing a publication's divisions changes nothing in the frozen document and needs no new number.

## Editing divisions

Divisions live under `divisions` in `data/site.json`, in display order:

| Field | Meaning |
|---|---|
| `slug` | URL, `/divisions/<slug>/`; keep it stable |
| `label` | the tag text used in posts and annotations |
| `badge` | short mark on cards and the division page |
| `name` | heading on cards and the division page |
| `blurb` | one line of HTML |
| `interests` | research interests, one HTML string each |

Every division gets a page, with or without posts and publications. Renaming a label means updating the posts and annotations that use it; the build lists any that still use the old one.

## Site copy

`content/pages/home.md` is the introduction at the top of the homepage (a hidden page, not built on its own). `about.md` is `/about/` and `404.md` is the not-found page. In these pages, each `##` heading starts a new window.

## GitHub Pages

`make publish` writes a complete site to `output/`, including `CNAME` for pe502.com. Deploying is publishing the contents of `output/` as the Pages site, for example by pushing them to a `gh-pages` branch or uploading them from a Pages workflow. No deployment is set up in this repository.
