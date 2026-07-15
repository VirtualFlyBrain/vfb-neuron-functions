#!/usr/bin/env python3
"""Merge neuron function-annotation source files into neuron_functions.tsv.

This is the FIRST stage of the pipeline. It combines one or more annotation
source files (each with its own column conventions) into the single merged
file ``neuron_functions.tsv`` that the rest of the pipeline operates on.

Design
------
Each source is described by an entry in ``SOURCES`` with a ``priority`` (lower
== preferred) and a ``loader`` callable. The loader holds ALL of that file's
custom column/convention handling and yields records in one canonical schema
(``CANONICAL_FIELDS``). Adding a new source in future therefore means writing
one loader and adding one ``SOURCES`` entry -- no other stage changes.

Merge rules (per cell type):
  * ANNOTATION bundle (function + references + always-attach extra_xrefs) is
    taken WHOLESALE from the single highest-priority source that has the cell
    type. This gives "preferred source replaces, does not merge, references".
  * CONTEXT fields (category, aliases, ...) fall back field-by-field to
    lower-priority sources, so e.g. a BANC neuron keeps the ``category`` that
    only ``known_types`` records (map_functions.py uses it for context).
  * FBbt anatomy mappings are NOT provided by annotation sources. They are
    carried over from the existing neuron_functions.tsv (accumulated curation);
    new cell types start blank and are filled later by map_fbbt.py.

Row order is kept stable (existing known_types order first, then any brand-new
cell types appended) to keep git diffs readable.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / 'sources'
MERGED = ROOT / 'neuron_functions.tsv'

# DOI of the BANC connectome paper. Attached as a literal xref to every
# annotation sourced from the BANC supplement, in addition to the file's own
# references. Kept as a DOI (not resolved to a PMID) deliberately.
BANC_PAPER_XREF = 'doi:10.1038/s41586-026-10735-w'

# Canonical annotation schema shared by all source loaders.
CANONICAL_FIELDS = [
    'cell_type', 'known_function', 'category', 'experimentally_tested',
    'reference', 'link_to_paper', 'notes', 'contributor', 'also_known_as',
    'extra_xrefs',
]
# Taken as a bundle from the single preferred source (replace semantics).
ANNOTATION_FIELDS = ['known_function', 'reference', 'link_to_paper', 'extra_xrefs']
# Filled field-by-field from the first source (by priority) with a value.
CONTEXT_FIELDS = ['category', 'experimentally_tested', 'notes', 'contributor',
                  'also_known_as']
# Carried over from the existing merged file; filled later by map_fbbt.py.
FBBT_FIELDS = ['FBbt_id', 'FBbt_name', 'specificity']

OUTPUT_FIELDS = CANONICAL_FIELDS + ['annotation_source'] + FBBT_FIELDS


def _blank(d):
    base = {f: '' for f in CANONICAL_FIELDS if f != 'cell_type'}
    base.update(d)
    return base


def load_known_types(path):
    """Legacy source: columns already match the canonical schema.

    In this file ``known_function`` is prefixed with the cell-type name (e.g.
    "PAM01 appetitive_learning"); strip that leading token so the function
    text maps cleanly, reproducing the cleaning previously applied downstream.
    """
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            ct = (row.get('cell_type') or '').strip()
            if not ct:
                continue
            rec = {'cell_type': ct}
            for fld in CANONICAL_FIELDS[1:]:
                rec[fld] = (row.get(fld) or '').strip()
            kf = rec['known_function']
            if kf.startswith(ct):
                rec['known_function'] = kf[len(ct):].strip()
            rec['extra_xrefs'] = ''
            out.append(rec)
    return out


def load_banc(path):
    """BANC supplement -- a companion to the BANC connectome paper.

    Column map: cell_function -> known_function, citations -> reference,
    doi -> link_to_paper (comma-separated bare DOIs -> doi.org URLs),
    other_names -> also_known_as. The BANC paper DOI is added as extra_xrefs.
    Where the row carries precise DOIs we drop the free-text citation so the
    reference resolver does not fuzzy-match it (the DOIs are authoritative);
    rows without a DOI keep the citation text so they can still resolve.
    """
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            ct = (row.get('cell_type') or '').strip()
            if not ct:
                continue
            dois = [d.strip() for d in (row.get('doi') or '').split(',')
                    if d.strip() and d.strip().upper() != 'NA']
            links = '; '.join(f'https://doi.org/{d}' for d in dois)
            citation = (row.get('citations') or '').strip()
            aliases = (row.get('other_names') or '').strip()
            if aliases.upper() == 'NA':
                aliases = ''
            out.append(_blank({
                'cell_type': ct,
                'known_function': (row.get('cell_function') or '').strip(),
                # Trust DOIs when present; keep citation text only as a
                # last-resort resolvable reference when there is no DOI.
                'reference': '' if dois else citation,
                'link_to_paper': links,
                'also_known_as': aliases,
                'extra_xrefs': BANC_PAPER_XREF,
            }))
    return out


# Sources in any order; `priority` decides preference (lower wins).
SOURCES = [
    {'name': 'BANC', 'priority': 0,
     'path': SOURCES_DIR / 'BANC_function_supplement.tsv', 'loader': load_banc},
    {'name': 'known_types', 'priority': 100,
     'path': SOURCES_DIR / 'known_types.tsv', 'loader': load_known_types},
]


def load_fbbt_carryover():
    """cell_type -> {FBbt_id, FBbt_name, specificity} from the existing file."""
    carry = {}
    if not MERGED.exists():
        return carry
    with open(MERGED, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            ct = (row.get('cell_type') or '').strip()
            if ct:
                carry[ct] = {fld: (row.get(fld) or '').strip() for fld in FBBT_FIELDS}
    return carry


def main():
    # loaded: [(source, [records])] in priority order (most preferred first).
    # Records are kept as a list so duplicate cell types (which can legitimately
    # carry different references) are preserved.
    loaded = []
    for src in sorted(SOURCES, key=lambda s: s['priority']):
        records = src['loader'](src['path'])
        loaded.append((src, records))
        print(f"  loaded {len(records):4} records from {src['name']} ({src['path'].name})")

    recs_by_name = {src['name']: recs for src, recs in loaded}

    # First record per cell type per source, for context-field fallback.
    first_rec = {}
    for src, records in loaded:
        d = {}
        for r in records:
            d.setdefault(r['cell_type'], r)
        first_rec[src['name']] = d

    # A cell type is "owned" by the most-preferred source that has it.
    def owner_of(ct):
        return next(src for src, recs in loaded if ct in first_rec[src['name']])

    def context_value(ct, fld, own_row):
        if (own_row.get(fld) or '').strip():
            return own_row[fld]
        for src, _ in loaded:  # priority order
            r = first_rec[src['name']].get(ct)
            if r and (r.get(fld) or '').strip():
                return r[fld]
        return ''

    # Stable order: legacy (lowest-priority) source order first, then cell types
    # introduced only by more-preferred sources. Overrides appear in place.
    order, seen = [], set()
    for src, records in sorted(loaded, key=lambda x: -x[0]['priority']):
        for r in records:
            if r['cell_type'] not in seen:
                seen.add(r['cell_type'])
                order.append(r['cell_type'])

    carry = load_fbbt_carryover()

    out_rows = []
    n_by_source = {}
    for ct in order:
        owner = owner_of(ct)
        owner_rows = [r for r in recs_by_name[owner['name']] if r['cell_type'] == ct]
        for own_row in owner_rows:  # preserves duplicates from the owning source
            n_by_source[owner['name']] = n_by_source.get(owner['name'], 0) + 1
            row = {'cell_type': ct, 'annotation_source': owner['name']}
            for fld in ANNOTATION_FIELDS:
                row[fld] = own_row.get(fld, '')
            for fld in CONTEXT_FIELDS:
                row[fld] = context_value(ct, fld, own_row)
            for fld in FBBT_FIELDS:
                row[fld] = carry.get(ct, {}).get(fld, '')
            out_rows.append(row)

    with open(MERGED, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(out_rows)

    mapped_fbbt = sum(1 for r in out_rows if r['FBbt_id'].strip())
    print(f"\nWrote {len(out_rows)} rows to {MERGED.name}")
    print(f"  annotation source: " +
          ", ".join(f"{k}={v}" for k, v in sorted(n_by_source.items())))
    print(f"  with FBbt mapping carried over: {mapped_fbbt}/{len(out_rows)}")


if __name__ == '__main__':
    main()
