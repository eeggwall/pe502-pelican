This document is collecting ideas and notes about 
potential future publications and forums for
dissemination of research for pe502.com.

This is a solo project. Every publication has a single author. The
focus is the mathematics, the concepts, and the web apps that let a
reader run them.

It is notes, not a spec. Some things below are settled and carry
their reasoning; others are stated as open. Nothing here has been
implemented, and no document has been numbered yet.


## What has to be decided, and in what order

Three questions, and they only work in this order:

1. **The unit.** What set of things gets an identifier.
2. **The string.** What that identifier looks like.
3. **The layer on top.** Pointers, collections, shelf marks - things
   that refer to identified documents without being documents.

A proposal that answers 2 before 1 is not an answer yet. The sections
below are mostly about 2 and 3, because that is where the thinking
started; the unit question is still open and is the one that would
change the most.


## The corpus this has to serve

Facts as of 2026-09-20, so the scheme is sized against the real thing:

* Wiki is 110 pages: 30 Sources, 51 Concepts, 29 Analyses.
* 133 IDEAS items: 76 open, 57 done.
* Nine divisions (listed in `DEPARTMENTS.md`, to be renamed): R E N Z Q S T F X. More expected.
* Twelve seminar arcs

## Laying out the concepts

### Document classes

Each class has to answer the same three questions, recorded in the three columns,
and the blanks are where the thinking stops.

| Class | Mutable | Gets an accession number | Example in the corpus |
|---|---|---|---|
| Wiki pages    | yes, continuously     | no        | all 110 pages |
| Publications  | no, frozen at issue   | yes       | none yet |
| Posts         | no, frozen at issue   | no        | none yet |
| Sidecar apps  | yes, until done       | no        | none yet |

Wiki pages are the "external brain" for the project and are already
typed one level down - Sources, Concepts, Analyses. That is the same
idea as a publication series, running one layer below it. 

The two systems should be built to look alike deliberately, or the 
resemblance will become confusing later.

### No division letters in identifiers

DO NOT put the division name/letter in any document identifier.
This makes the document identifiers too rigid, it gets away from the
intended purpose as canonical identifiers.

The publication itself does not know about divisions. Divisions are a
layer on top, used for filtering (see Divisions below). Moving a
publication to different divisions means editing its tags and
rebuilding the site. The publication does not change, and does not
need an `obsoletes` or a new number.

**Division must stay out of the identifier.**

Furthermore, DO NOT put the publication type in any document identifier
(for example, inserting "TR" into the identifier if it is a technical report).
While the publication type cannot be changed after publication
(since different publication types require different information),
it introduces confusion and makes identifiers unpredictable, in addition
to requiring its users to understand our internal schema.

**Publication type must stay out of the identifier.**

Principle: one canonical identifier, no knowledge of internals needed
to read or compare it.

### Series

Series names the type of publication:
* Technical Report (completed work containing results others can use)
* Working Note (documenting preliminary or failed approach)
* Computational Record (repository with notebook/data/environment details)
* Seminar Notes
* Problem Set
* Errata

(This is a provisional list. Computational Record is the most fuzzy,
since it is most likely to need to evolve. Current plan is to have this
be a record that points to a GitHub repository tag/commit hash.)

**The series is metadata on the record. No metadata appears in the identifier.** 

`PE502-1` is the whole ID, one form only, no ambiguity. Numbers are
the natural numbers in issue order, with no zero-filling: `PE502-1`,
`PE502-2`, `PE502-3`, ...
"Technical Report PE502-1" is ordinary prose, not a second form of the
name. This canonical identifier is the entire, unique, and only ID. 
Documents do not have any "alternative" IDs.

Series never changes for a given document, because documents freeze. A
working note that grows into a report does not get relabelled - a new
report is issued that obsoletes the note, and both stay reachable.

The Working Note is intended to capture results that are not theorems
but deserve publication anyway. These unsuccessful approaches should be 
preserved and have a place to live - hence the Working Note series.

(Frozen-on-publication may not be right for all of these documents.
Problem Set, in particular, should be able to be updated with errata
in the same document, rather than publishing it in a separate document.)

**Obsoletes/updates.** Metadata field `obsoletes` and `obsoleted by`
allow documents to remain published and reachable forever, but also
allows one document to render another obsolete. This preserves the
documents as they were when published (errors get erratum, not silent
fixes). This characteristic makes the series archival.

To replace a document with a new version, you publish a new document with
a new identifier, and add `obsoletes` to its metadata (and update the 
`obsoleted by` metadata of the obsolete document).

One report can carry multiple take-homes (proofs, conjectures, observations),
so we DO NOT attempt to classify documents according to a
"this is a proof" or "this is a conjecture" system.

### Divisions

Topics are grouped into divisions (Q Division, X Division, ...), each
covering a cluster of related topics. A division is a tag, not a
container: a publication or a post can carry more than one.

Division tags are metadata in the site's markdown, not part of any
frozen document, so they can change at any time.

Each division page shows the posts tagged with that division, plus the
publications tagged with it.

### Posts

Site news is one stream of posts. There is no separate channel for
site-wide news: a post with no division tag is a site-wide post.

* The landing page shows every post, newest first.
* Each division's page filters that stream by its tag, so it works as
  the division's blog.
* A post announcing `PE502-7` carries the same division tags as
  `PE502-7`, so it appears on each of those divisions' pages.

Posts are news, so they are treated differently from published
documents: they get no accession number, they are not in the catalog,
and they are not subject to the same restrictions. A post is
identified by its date and title, and has no number.

In Pelican, divisions are tags because a post can have several.

There is one post type, with one category and one template. Posts are
not split by kind. The announcement for each new `PE502-X` is
generated from that template.

**Posts are not in the unit set of published documents.**

Principle: do not treat posts like other published documents.

### Seminars

Seminars can be thought of as a "story arc" covering concepts in a particular
order, plus whatever the delivery is intended to produce. It is a curated
path through a body of material.

A delivered arc emits a Seminar Notes document, which is frozen and
given an accession number.

## Wiki pages

The wiki is the project's "external brain".
They change quickly, are under version control, and should never receive
an accession number. The wiki page editing and publishing process is
completely and totally separate.

**Wiki pages are not in the unit set of published documents.**

## Sidecar apps

Nearly every publication will have a sidecar: a small standalone web app
in its own git repo, on its own subdomain. The publication describes the
concepts with mathematics; the sidecar lets the reader run them.

**The link runs one way: the sidecar links to its publication.** The
publication never mentions its sidecar, the catalog does not record it,
and it is not hosted on the Pelican site. Its subdomain has its own DNS
entry pointing at its own host (GitHub Pages or another static host),
separate from the Pelican site at pe502.com. A post may announce a
sidecar and link to it; posts are not publications, so the one-way rule
still holds. The publication stands alone.

**A sidecar is not a Computational Record.** A Computational Record is a
numbered publication pointing at a repo tag, and a result can rest on it.
No result rests on a sidecar. Git is its only provenance.

Naming: `1.pe502.com` for `PE502-1`. The domain already carries the
`PE502` part, so the number is the only unique part left and is the
whole subdomain. The publication never knows this name, so it is an
address, not a second identifier.

One sidecar per publication. When a publication is obsoleted, the new
one gets a new sidecar, and the old sidecar becomes a meta-refresh
`index.html` pointing to it.

Flat HTML + CSS + JS, one repo, minimal or zero dependencies. Copy
patterns forward; when the app is built, move on.

**Sidecar apps are not in the unit set of published documents.**

Principle: the sidecar knows its publication; the publication never knows its sidecar.

## Summary

In summary:
* The unit of publication is frozen documents written for a reader.
* Wiki pages, posts, and sidecar apps are not in the unit set of published documents.
* Published documents should be thought of as documents that stand on their own 
  content and references, they should not lean on the wiki. The wiki content
  is the constantly-changing body of knowledge. Publications draw from that
  to produce standalone publications.
* Posts and wiki pages are for anyone following the project.
* The published documents are intended to stand on their own, be something that
  could actually be citable (like Dijkstra's EWD memos), and contain real math
  that is understandable on its own.
* Constraints: static GH Pages site (pelican to generate site, 
  JSON for catalog).
