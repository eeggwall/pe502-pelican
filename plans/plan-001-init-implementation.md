# Plan 001: Initial PE502 site implementation

## Objective

Build a small, self-contained Pelican website for PE502 research updates and
published documents. Lift the visual design from `single-page-app/index.html`,
but replace its JavaScript routing and embedded content with ordinary static
pages generated at build time.

Keep the maintained source simple. The number of generated pages is not a
constraint: posts, publications, and divisions can grow with the project.

This plan records the architecture agreed in the planning conversation.
`publications.md` supplies publication principles and background, but describes
itself as notes rather than a complete specification. Do not turn its open
questions into implementation requirements without further agreement.

## Agreed decisions

- Keep the Pelican configuration, content, theme, site metadata, and local
  integration code in this repository.
- Use a local theme directory; do not require a separate theme repository or
  a `pelican-themes` installation step.
- Generate ordinary HTML pages with ordinary links. JavaScript is not required
  to read content or navigate the site.
- Use one post stream and one post template for updates, publication
  announcements, and announcements linking to external applications.
- Resolve the publication catalog and local annotations at build time.
- Copy the publication catalog into this repository by hand initially. A future
  synchronization step may fetch the source JSON before building.
- Treat division tags as the site's only post-tag taxonomy. Tags link directly
  to division pages, not to a separate collection of generic tag pages.
- Give categories no public-facing role.
- Host no sidecars in this repository. Their repositories, subdomains, GitHub
  Pages deployments, and application code remain entirely separate.

## Source layout

```text
pelicanconf.py
publishconf.py
requirements.txt
README.md

content/
    posts/
        YYYY-MM-post-title.md
    pages/
        about.md

data/
    published.json
    site.json

plugins/
    pe502_catalog/
        __init__.py

theme/
    templates/
    static/
        css/
            pe502.css

tests/
plans/
    plan-001-init-implementation.md

output/                       # generated; not hand-maintained
```

Keep `single-page-app/index.html` as the design reference during implementation.
Do not overwrite it with generated output. The removed example sites are not
implementation dependencies.

## Content and authority boundaries

### Publication catalog: `data/published.json`

This is an unchanged export or snapshot from the publications repository.
That repository is authoritative for issued documents, accession numbers, and
their archival metadata.

Before implementing the reader, inspect an actual export and its schema. The
prototype's embedded publication records are illustrative, not sufficient
evidence of the authoritative schema or of actual publication status.

The website must not allocate accession numbers, change publication types, or
edit frozen documents. Identifiers remain canonical strings such as `PE502-1`,
without division letters, publication-type codes, or zero-filling.

Catalog synchronization is separate from rendering:

- Initially, manually copy the current JSON export into `data/published.json`.
- Build from the local snapshot without network access.
- Later, optionally add an explicit pre-build fetch of the raw JSON export.
- Do not scrape HTML pages or fetch the catalog in the reader's browser.

### Site-owned metadata: `data/site.json`

This file is owned, versioned, and edited entirely in this repository. It is not
maintained in the publications repository or in another external service.

It contains two groups of information:

1. **Division definitions:** stable URL slugs, canonical readable tag labels,
   badges, descriptive names, blurbs, research interests, and display order.
2. **Publication annotations:** division assignments, summaries, and abstracts
   where those are site-authored, keyed by canonical accession number.

Join annotations to catalog records by accession number. Local annotations
supplement authoritative fields; they do not override them.

Division assignments can change without changing a frozen document or issuing
a new accession number. Publication annotations contain no sidecar registry
or sidecar URL field.

### Posts

Author posts as Markdown files in `content/posts/` using the agreed convention:

```text
YYYY-MM-post-title.md
```

Store the exact date in Pelican metadata, rather than inferring it from the
month-only filename. For example:

```markdown
Title: A new counting approach
Date: 2026-10-04
Slug: a-new-counting-approach
Tags: M Division, B Division, The Phone Company

Post content goes here.
```

The tag names above illustrate the agreed readable-label convention. The
configured division inventory determines which names are valid.

Posts have no accession numbers or bulletin numbers. They have the same
template regardless of whether they announce a report, discuss research in
progress, or link to an external application.

A post with no division tags is a site-wide update. Do not require authors to
write a category in every post; Pelican can use an implicit default category.

Publication announcements remain posts. Do not automatically insert catalog
records into the homepage's news stream. An announcement should carry the same
division memberships as the publication it announces.

### Sidecars and wiki content

Sidecars live in independent repositories on independent subdomains, with
their own deployments. A post can announce and link to one. The publication
catalog and frozen publication remain unaware of it.

Wiki editing and publishing are also outside this site's initial scope. Wiki
pages, posts, and sidecars do not become numbered publications.

## Division tags and URLs

Use Pelican's `Tags` field for division memberships because a post can belong
to several divisions. Pelican's singular `Category` is not the appropriate
field for this relationship.

Resolve canonical readable tag names through `data/site.json` to stable
division slugs. Example mappings:

| Tag label | Division URL |
| --- | --- |
| M Division | `/divisions/m/` |
| B Division | `/divisions/b/` |
| The Phone Company | `/divisions/phone-company/` |

Render readable labels as links to those division pages. The prototype's
badges can remain as decoration, but they do not replace the agreed tag labels.

Use the same mapping when rendering publication division assignments. Do not
maintain a second set of generic tag pages, a generic tag index, or category
pages. Unknown tag labels should fail validation rather than silently create
new divisions or unintended URLs.

## Generated pages

- **Homepage:** brief site introduction and the post stream, newest first,
  with pagination as the content grows.
- **Post pages:** complete dated posts, using the tractor-feed visual treatment.
- **About page:** project context, the distinction between posts and
  publications, and relevant external links.
- **Publication catalog:** all issued publications with accession numbers,
  titles, series, dates, and local division assignments.
- **Publication detail pages:** authoritative metadata, available site-authored
  summaries or abstracts, document links, and replacement relationships where
  supplied by the catalog.
- **Division index:** division cards with descriptions and content counts.
- **Division pages:** description, research interests, tagged posts, and tagged
  publications. Keep posts and publications clearly distinguished.

Generate every configured division page even when it has no posts or
publications. Do not depend exclusively on Pelican's automatic tag-page
generation, which is driven by article tags.

Initially keep research interests and content on the same division page;
separate interest pages or division subnavigation are unnecessary.

Use stable, directory-style URLs, for example:

```text
/
/posts/2026/10/a-new-counting-approach/
/publications/
/publications/PE502-1/
/divisions/
/divisions/m/
/about/
```

An optional separate posts index should reuse the same stream and rendering,
not introduce a second news channel.

## Build-time integration

Implement one small local Pelican plugin for the project-specific work:

1. Read the local catalog and site metadata.
2. Validate their structure and the fields required by the actual catalog
   schema.
3. Join catalog records and site annotations by accession number.
4. Resolve article tag names to configured divisions.
5. Make the joined records and division definitions available to templates.
6. Generate catalog, publication-detail, division-index, and division pages.

Pelican handles Markdown reading, ordinary article pages, informational pages,
the homepage post stream, and pagination. Publications are catalog records,
not disguised blog articles.

Validation should catch at least:

- duplicate accession numbers;
- duplicate division slugs or tag labels;
- unknown division assignments in posts or publication annotations;
- local annotations referring to publications absent from the catalog;
- missing required authoritative fields;
- conflicting output paths.

New catalog records should remain renderable before local annotations are
written. Use sensible empty annotations rather than omitting those documents
or fabricating summaries and division memberships.

## Theme and dependencies

Extract the prototype's visual language into a small local theme:

- sand, paper, blue, and rust palette;
- narrow centered layout;
- beveled window panels and title bars;
- castle seal, masthead, navigation, and footer;
- tractor-feed post sheets;
- publication tables and metadata panels;
- division cards and badges;
- responsive layout, horizontal table scrolling, skip link, and visible focus.

Use a small set of shared Jinja templates. Prefer reusable post and publication
rendering over duplicated markup, but do not build a generalized theme framework.

Remove the need for the prototype's browser-side content arrays, HTML-string
renderers, hash router, and JavaScript-only page loading. Do not import the
removed example sites' dependencies or unrelated functionality.

Use Pelican, its Markdown support, and standard Python facilities where
possible. Choose JSON rather than YAML initially to avoid an extra parser
dependency. No frontend framework, Node build pipeline, or external theme
installation is needed.

## Implementation sequence

1. **Confirm the catalog handoff.** Inspect the real `published.json` schema
   and establish where authoritative document files are served.
2. **Add the Pelican skeleton.** Local theme configuration, dependencies,
   development and production settings, generated-output exclusions, and
   straightforward build/preview commands.
3. **Lift the design.** Extract CSS and shared markup from the prototype;
   preserve its visual character and accessibility features.
4. **Define local metadata.** Add division definitions and publication
   annotations in `data/site.json`, using the agreed readable tag names.
5. **Add the catalog integration.** Implement loading, joining, validation,
   division resolution, and custom page generation.
6. **Add editorial content.** Convert reviewed prototype copy to Markdown
   posts and informational content. Do not present unverified sample records
   as actual issued publications.
7. **Test the generated site.** Validate content relationships, output paths,
   links, ordering, pagination, empty states, and no-JavaScript navigation.
8. **Document maintenance.** Explain adding posts, refreshing the catalog,
   annotating publications, editing divisions, and building for GitHub Pages.

Produce deploy-ready static output without enabling or performing a live
deployment as part of this initial implementation unless separately requested.

## Acceptance criteria

- A clean local build generates a navigable static website from repository
  content and data, without browser-time catalog requests.
- The theme lives entirely in this repository and needs no installation step.
- New Markdown posts generate normal permanent pages and appear newest first
  in the homepage stream.
- Posts support multiple readable division tags; untagged posts remain
  site-wide updates.
- Every rendered division tag links to its corresponding division page.
- There are no generic `/tags/` pages or category pages.
- All configured divisions have pages, including divisions with no content.
- A division shows the posts and publications assigned to it, without placing
  publications in the general news stream as independent posts.
- Catalog records retain canonical accession numbers and authoritative fields.
- Local annotations are maintained solely in `data/site.json` and joined at
  build time.
- Catalog refreshes do not allocate identifiers or alter frozen documents.
- Superseded documents remain reachable when present in the catalog.
- Sidecars remain entirely external; posts may link to them, but publication
  records contain no sidecar registry.
- The generated site retains the prototype's visual character and works with
  JavaScript disabled and at narrow viewport widths.
- Tests cover malformed metadata, unknown divisions, catalog joins, empty
  divisions, output links, and the separation of posts from publications.

## Details to verify before coding

- The actual publications-repository export schema and current catalog contents.
- The document-file hosting location and URL construction rules.
- The final initial division inventory and canonical readable tag labels,
  including naming differences between the prototype and the conversation.
- Which summaries, abstracts, and prototype posts are approved editorial
  content rather than illustrative placeholders.

These are data and integration handoff details, not reasons to reopen the
agreed single-repository, build-time, static-site architecture.
