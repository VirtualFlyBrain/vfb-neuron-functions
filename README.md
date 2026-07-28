# VFB Neuron Functions

## Overview

This project maps known *Drosophila* neuron cell types to terms in the Drosophila anatomy ontology (FBbt) and their functions to Gene Ontology (GO) Biological Process terms, maintained by [Virtual Fly Brain](https://virtualflybrain.org).

Annotations are drawn from one or more **source files** (in `sources/`), merged into a single working file `neuron_functions.tsv`, enriched with FBbt anatomy mappings, resolved literature references and function-ontology terms, and finally exported as an OWL ontology.

## Repository layout

```
sources/                        annotation source files (never modified in place)
  known_types.tsv                 legacy set of ~670 cell types with functions
  BANC_function_supplement.tsv    BANC connectome function annotations (preferred)
resources/
  all_male-cns_FBbt.tsv           cached FBbt curation table (git-ignored; see below)
  fbbt_overrides.tsv              curated FBbt mappings that override the table
scripts/
  merge_sources.py                stage 1: merge sources -> neuron_functions.tsv
  map_fbbt.py                     stage 2: fill FBbt anatomy mappings
  resolve_references.py           stage 3: resolve references -> xrefs
  map_functions.py                stage 4: map functions -> GO/NBO
  generate_robot_template.py      stage 5: build the ROBOT template
build.sh                        runs the full pipeline + stamps OWL metadata
reports/                        analysis artifacts (not read by the pipeline)
  ontology-change-report.md       cell-type/function changes from the BANC merge
  fbbt_source_fix_candidates.tsv  upstream FBbt mappings still worth fixing at source
neuron_functions.tsv            merged, enriched working file (basis for the OWL)
robot_template.tsv              generated ROBOT template
vfb-neuron-functions.owl        generated OWL ontology
```

## Sources and precedence

Annotations come from the files in `sources/`, combined by `merge_sources.py`. Each
source has a **priority** (lower = preferred); for a given neuron the most-preferred
source that lists it supplies the *function annotation and its references*, while
*context fields* such as `category` fall back to lower-priority sources.

| Source | Priority | Notes |
|--------|----------|-------|
| `BANC_function_supplement.tsv` | 0 (preferred) | Companion data to the BANC connectome paper; 161 cell types |
| `known_types.tsv` | 100 | Legacy set; used for any neuron not in the BANC file |

So a neuron present in the BANC supplement takes its function and references from
BANC; `known_types` is used only where a neuron is absent from BANC. Every
BANC-sourced annotation additionally carries the BANC paper DOI
(`doi:10.1038/s41586-026-10735-w`) as a reference, in addition to the file's own
citations.

An `annotation_source` column in `neuron_functions.tsv` records which source won for
each row.

### Adding a new source

The merge is built around a per-source **adapter**. To add a source:

1. Add the file to `sources/` (leave it unmodified — loaders do any cleaning).
2. Write a `load_<name>(path)` function in `merge_sources.py` that reads the file
   and yields records in the canonical schema (`CANONICAL_FIELDS`), handling that
   file's particular column names and conventions. Set `extra_xrefs` for any
   reference that should always be attached (e.g. an accompanying paper DOI).
3. Add an entry to `SOURCES` with a `priority`.

Nothing else changes: the FBbt, reference and function stages operate on the merged
file regardless of where each row came from.

## Pipeline

The whole build is wrapped in **`build.sh`** — run it from the repository root:

```bash
./build.sh
```

It runs the five stages in order and then builds the OWL with ROBOT, stamping
version and provenance metadata (see below). It is equivalent to:

```bash
python scripts/merge_sources.py            # sources/ -> neuron_functions.tsv
python scripts/map_fbbt.py                 # add FBbt_id / FBbt_name / specificity
python scripts/resolve_references.py       # add xrefs
python scripts/map_functions.py            # add function_ont_id / function_ont_label
python scripts/generate_robot_template.py  # -> robot_template.tsv
robot template --template robot_template.tsv <prefixes...> annotate <metadata...> \
  --output vfb-neuron-functions.owl
```

`merge_sources.py`, `resolve_references.py`, `map_functions.py` and `map_fbbt.py`
each rebuild their own output columns on every run, so the pipeline is
re-runnable; `neuron_functions.tsv` accumulates the results.

### Ontology metadata / versioning

`build.sh` stamps the OWL's `owl:Ontology` node with a **date-based version**
(`owl:versionInfo`, a dated `owl:versionIRI` under `.../releases/<date>/`, and
`dcterms:modified`), a `dcterms:description`, `dc:creator` "Virtual Fly Brain", a
`dcterms:license` of [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), and
provenance: `dcterms:source` = the BANC paper DOI, plus an `rdfs:comment` recording
the build date and the exact git commits of this repo and of `male-cns_curation`
(the FBbt-mapping source) — so the "data version" is pinned to source revisions, not
just a date. The date and commits are computed at build time.

## Stage 1 — Merge (`merge_sources.py`)

Combines the source files into `neuron_functions.tsv` (690 rows: 161 from BANC,
529 from `known_types`), preferring BANC for shared neurons and appending BANC-only
cell types. Duplicate cell types in a source (which can legitimately carry different
references) are preserved. The `known_types` loader strips the cell-type name that
prefixes its `known_function` values (e.g. "PAM01 appetitive_learning" →
"appetitive_learning"). FBbt anatomy mappings already present are carried over.

## Stage 2 — FBbt anatomy mapping (`map_fbbt.py`)

FBbt mappings are not produced by the annotation pipeline. The bulk were curated in
the [male-cns_curation](https://github.com/VirtualFlyBrain/male-cns_curation) project
(`resources/all_male-cns_FBbt.tsv`), with some added via OLS lookup. This script
re-attempts **every** row that lacks a valid FBbt mapping on each run (so cell types
gain mappings as new FBbt terms are published), matching cell-type names and aliases
against the male-cns table (single, clean FBbt CURIEs only) and falling back to a
conservative OLS search. Matching prefers the table's authoritative `type` column
over secondary columns (synonyms, hemibrain/flywire/manc types), so a name that is
another cell type's cross-referenced ID cannot shadow the correct term. Already-mapped rows are left untouched, except that
curated entries in `resources/fbbt_overrides.tsv` are force-applied last (they win
over both the carried-over value and the male-cns table). Use the overrides file for
deliberate curation decisions — e.g. fixing an obsoleted term, refining a generic
term to a subtype, or correcting a mis-mapping — that should hold even when the
male-cns table disagrees.

When the male-cns table is updated at source, re-fetch it (delete the cached copy or
let `map_fbbt.py` fetch it) and review the differences: newly-covered blanks are
filled automatically, but changes to already-mapped rows are **not** applied
automatically. Note that the male-cns table is male-specific by construction, so it
will map sexually dimorphic neurons (e.g. `pC1a`, `vAB3`) to male terms; this dataset
keeps the curated female/sex-neutral mappings where appropriate, and pins genuine
improvements (obsolete-term fixes, subtype refinements) via the overrides file.

- **630 / 690 mapped**
- **60 unmapped** — BANC-specific connectome IDs and putative types with no FBbt
  term (e.g. `AN09B018_a`–`d`, `SA_VTV_*`, `LgLG*`, `SApp*`, `DProN*`); these stay
  in `neuron_functions.tsv` with their annotations but are excluded from the OWL.

`resources/all_male-cns_FBbt.tsv` comes from a private VFB repository and is **not
committed** (it is git-ignored). If it is absent, `map_fbbt.py` tries to fetch it
with the GitHub CLI (`gh`); otherwise it uses the OLS fallback only.

## Stage 3 — Reference resolution (`resolve_references.py`)

Resolves the `reference` and `link_to_paper` columns to PubMed IDs and DOIs, writing
a pipe-separated, prefixed `xrefs` column (e.g.
`PMID:31182867|doi:10.1101/2024.06.27.601106`). URLs and DOIs are parsed directly;
free-text citations are matched against PubMed by first author and year, with manual
overrides for edge cases. Any `extra_xrefs` set by a source adapter (such as the BANC
paper DOI) are appended verbatim.

- **529 rows resolved**, **157 unique PMIDs**, **46 unique DOIs** (including the BANC
  paper DOI).

## Stage 4 — Function-to-ontology mapping (`map_functions.py`)

Maps `known_function`/`category` to GO Biological Process terms (preferred) or NBO
terms (fallback), adding `function_ont_id` and `function_ont_label`. A curated
dictionary of normalised function terms covers the majority; remaining terms are
searched in OLS with word-overlap filtering. Pure molecular markers and overly broad
descriptors (e.g. `neuromodulatory`, `octopaminergic`) are intentionally excluded.
Context-aware overrides keep biologically accurate (e.g. MBON "aversive" →
associative learning; song-*perception* neurons → sensory perception of sound;
male-specific GO terms only on male-specific FBbt anatomy).

- **667 / 690 rows mapped**, **47 unique ontology terms** (44 GO, 3 NBO).
- 23 rows have no explicit functional information.

## Stage 5 — OWL generation (`generate_robot_template.py` + ROBOT)

`generate_robot_template.py` filters to the **412 rows** where FBbt_id,
function_ont_id and xrefs are all present **and the FBbt mapping is an exact match**
— rows whose `specificity` is `parent_term` or `general_term` are excluded, so a
function is never asserted on a broad anatomy class (and distinct subtypes are not
collapsed onto a shared parent). It expands pipe-separated functions into one row per
(FBbt, function) pair (validating that both are clean CURIEs), and writes
`robot_template.tsv` (509 data rows). ROBOT builds the OWL, asserting for each row
`FBbt:X SubClassOf RO:0002216 ('capable of part of') some GO:Y`, annotated with the
literature references (`oboInOwl:hasDbXref`) and a provenance `rdfs:comment` (the
comment is only added for `known_types`-sourced rows).

- **467 `capable of part of` axioms**; 126 carry the BANC paper DOI.

## Files

| File | Description |
|------|-------------|
| `sources/known_types.tsv` | Legacy cell types with functional annotations |
| `sources/BANC_function_supplement.tsv` | Preferred BANC connectome function annotations |
| `neuron_functions.tsv` | Merged, enriched working file (basis for the OWL) |
| `scripts/merge_sources.py` | Merge source files, preferring higher-priority sources |
| `scripts/map_fbbt.py` | Fill FBbt anatomy mappings from the male-cns table + OLS |
| `resources/fbbt_overrides.tsv` | Curated FBbt mappings force-applied by `map_fbbt.py` |
| `scripts/resolve_references.py` | Resolve references to PubMed IDs and DOIs |
| `scripts/map_functions.py` | Map functions to GO/NBO ontology terms |
| `scripts/generate_robot_template.py` | Generate the ROBOT template |
| `build.sh` | Run the full pipeline and build the OWL with version/provenance metadata |
| `robot_template.tsv` | Generated ROBOT template |
| `vfb-neuron-functions.owl` | Generated OWL ontology with neuron-function axioms |
