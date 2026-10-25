# Plan, second draft: publications table, OEIS catalog, about page

Three changes to the site built under `plans/plan-001-init-implementation.md`.

## Feedback

- The publications table squeezes the title, the most important column, to
  make room for the ID, type, divisions and date. The divisions column is the
  worst offender: its chips sit side by side and wrap. Divisions should be one
  tag per line, in a much narrower column.
- Add an `oeis` tab: a catalog of the OEIS (On-Line Encyclopedia of Integer
  Sequences) sequences, and how each one ties in with castles. Start with the
  sequences each PE502 report cites, which every report already collects in
  its own "OEIS sequences" reference list.
- On the about page, the "What gets posted" section lists divisions next to
  posts and publications as if they were a kind of content, and tells the
  reader nothing useful. Cut it.

## 1. Publications table

In the 760px layout the table is about 728px wide. The title column gets
about 255px, so "Castle Polyominoes and How to Count Them" wraps onto two
lines, while the divisions column takes about 190px for three chips.

- The title column takes all spare width. ID, Type, Divisions and Published
  shrink to their content.
- Divisions: chips stack one per line in the table cell. The column is as wide
  as an `X Division` chip; a longer label such as `The Telephone Company`
  wraps inside its chip, so the column keeps that width. On publication pages
  and division pages, chips stay in a row.
- Type wraps at spaces, so `Technical Report` takes two short lines.
- ID and Published stay on one line.
- Changes: a class on the divisions cell in `publications.html`, and rules
  scoped to the catalog table in `pe502.css`. The `chips` macro is unchanged.

## 2. OEIS catalog

### What counts as cited

A report's OEIS sequences are the ones it cites with `\oeis{A...}` in the
tagged `.tex`. These are exactly the entries its PDF prints under "OEIS
sequences". The `.bib` file does not tell you this: PE502-2's `.bib` has five
OEIS entries, but the report cites two of them. A000032, A001950 and A003622
appear in neither its text nor its PDF.

At the current tags:

| Report | Cited sequences |
| --- | --- |
| PE502-1 | none |
| PE502-2 | A000045, A003849 |
| PE502-3 | A000045, A000129, A001333, A034182, A094706, A106514, A171842 |

That is eight sequences in all. A000045 is cited by both reports.

### Data handoff

The citation list comes from the publications repository, in the catalog
export, like every other fact about a frozen report. The site still copies
`published.json` in unchanged and builds offline. It never reads `.tex` or
`.bib` files.

- In pe502-pubs, `tools/catalog.py add` writes an `oeis` field on each
  record: the sequences the report cites (skipping commented-out lines),
  sorted by A-number, each with the name from its `.bib` title.

  ```json
  "oeis": [
    {"id": "A000045", "name": "Fibonacci numbers"},
    {"id": "A003849", "name": "The infinite Fibonacci word"}
  ]
  ```

- `name` is plain text, like the catalog's `title`. The tool converts the
  LaTeX the current titles use (`{Pell}` braces, `--`, `$\sqrt{2}$`,
  `$n \times 2$`, `x^2`, `2^n`, `\ldots`) to Unicode (`Pell–Lucas`, `√2`,
  `n × 2`, `x²`, `2ⁿ`, `…`) and stops on anything else.
- A second subcommand backfills PE502-1, PE502-2 and PE502-3 from their tags,
  since `main` can drift from what was frozen. PE502-1 gets an empty list.
- Refresh `data/published.json` here from the new export.

### Site data

- `pe502_catalog` reads `oeis` as a required catalog field and inverts it into
  one sequence per A-number, with the reports that cite it. If two reports
  name a sequence differently, the newest report's name is used.
- Site-authored tie-ins go in `data/site.json`, under a new `oeis` object
  keyed by A-number:

  ```json
  "oeis": {
    "A001333": {
      "castles": [
        "Ridge castles of height 3 number <i>A001333</i>(<i>w</i>+1) &minus; 2 at width <i>w</i> (PE502-3)."
      ]
    }
  }
  ```

  `castles` is a list of HTML strings, one tie-in each, naming the report it
  comes from. It is optional; a sequence renders without it.
- Validation, in the plugin's existing style: an A-number that is not `A`
  followed by six digits, the same A-number twice in one record, a missing or
  empty name, a tie-in for a sequence no report cites, unknown fields, and a
  second output claiming `oeis/index.html`.

### Page

- `/oeis/`, with an `oeis` tab between `publications` and `divisions`.
- One table, sorted by A-number, with three columns:
  - A-number, linked to `https://oeis.org/A...`;
  - Name, with its tie-ins listed under it;
  - Cited in, `PE502-N` links to publication pages, one per line.
- The column rule from the publications table applies: the name takes the
  spare width and the other columns shrink.
- Each row carries `id="A001333"`, so `/oeis/#A001333` lands on it.
- Empty state: "No OEIS sequences are cited yet."
- One page; sequences get no pages of their own.
- Settings: `OEIS_URL`, `OEIS_SAVE_AS`, and
  `OEIS_SEQUENCE_URL = "https://oeis.org/{id}"`.

### Tie-ins for the first eight

Draft the tie-ins from what each report states, and review them before they
go into `site.json`. For example, Table 1 of PE502-3 gives A001333 for smooth
and ridge castles of height 3, and A171842 for returning Pell castles. A
sequence that a report cites only for comparison gets no tie-in from that
report.

### Tests and docs

- Loader: the inversion, the newest-name rule, and each validation error
  above.
- Output: `/oeis/` lists each sequence once with the reports that cite it,
  sorted by A-number, with working links; the top-level output set in
  `tests/test_site.py` gains `oeis`.
- README: the `oeis` catalog field, and the `oeis` annotations in `site.json`.

## 3. About page

- Delete the `## What gets posted` section of `content/pages/about.md`: the
  heading and its three definition entries. The page keeps the introduction,
  Publication types, and Elsewhere.
- The publications page already explains that a publication is frozen and how
  replacement works, so that point is still covered.
- Drop the `.prose dl` selectors from `pe502.css`. After the cut, no page uses
  a definition list. `dl.defs` on publication pages stays.

## Order

1. About page.
2. Publications table.
3. pe502-pubs: the `oeis` export and backfill; refresh `data/published.json`.
4. OEIS loader, page, tab, tests and README.
5. Tie-in drafts, for review.
