#!/usr/bin/env python3
"""Fill in FBbt anatomy mappings for neuron_functions.tsv.

FBbt mappings are not produced by the annotation pipeline; the bulk of them
come from the male-CNS typing table built by VirtualFlyBrain/connectome-curation
(``resources/all_male-cns_FBbt.tsv``), with some added by OLS lookup.

This script re-attempts EVERY row that still has an empty ``FBbt_id`` on each
run, so that cell types gain mappings as new FBbt terms become available. Rows
that are already mapped are left untouched. It looks each cell type up (by its
name and any aliases) in the male-cns FBbt table first, then falls back to a
conservative OLS search, and reports whatever is still unmapped.

``build.sh`` builds the table with connectome-curation
(``vfb-curation build-typing male_cns``); it is not committed. If it is absent,
the script proceeds with the OLS fallback only.
"""

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MERGED = ROOT / 'neuron_functions.tsv'
FBBT_TABLE = ROOT / 'resources' / 'all_male-cns_FBbt.tsv'
# Curated FBbt decisions that override both the carried-over value and the
# male-cns table (e.g. obsolete-term fixes, subtype refinements, corrections).
OVERRIDES = ROOT / 'resources' / 'fbbt_overrides.tsv'

# A clean, single FBbt CURIE (what a class IRI must be built from).
FBBT_CURIE = re.compile(r'FBbt:\d+')

# Columns in all_male-cns_FBbt.tsv whose values name a cell type.
MATCH_COLS = ['type', 'synonyms', 'hemibrainType', 'flywireType', 'mancType']
USE_OLS = True


def _split(value):
    return [v.strip() for v in re.split(r'[|,;]', value or '') if v.strip()]


def build_fbbt_index():
    """Return (type_index, general_index), each value -> (FBbt_id, FBbt_name,
    specificity) for unambiguous matches only.

    ``type_index`` is built from the authoritative ``type`` column alone;
    ``general_index`` also uses synonyms and the hemibrain/flywire/manc type
    columns. The type index is consulted first at lookup time, so a name that
    is some other cell type's cross-referenced hemibrain/flywire ID cannot
    shadow the row whose primary ``type`` is that name (e.g. DNp71 lists DNp09
    as its hemibrainType; DNp09 must still resolve to the DNp09 term)."""
    if not FBBT_TABLE.exists():
        print(f"  {FBBT_TABLE.name} not found (run build.sh to build it); "
              "OLS fallback only", file=sys.stderr)
        return {}, {}
    type_cand, gen_cand = {}, {}
    with open(FBBT_TABLE, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            fid = (row.get('FBbt_id') or '').strip()
            # Only single, clean FBbt CURIEs. The table also holds compound
            # "general_term"/"parent_term" mappings (pipe-separated pairs) that
            # would produce invalid IRIs downstream -- skip those.
            if not FBBT_CURIE.fullmatch(fid):
                continue
            info = (fid, (row.get('FBbt_name') or '').strip(),
                    (row.get('specificity') or '').strip())
            for val in _split(row.get('type')):
                type_cand.setdefault(val, {})[fid] = info
            for col in MATCH_COLS:
                for val in _split(row.get(col)):
                    gen_cand.setdefault(val, {})[fid] = info

    def unambiguous(cand):
        return {v: next(iter(d.values())) for v, d in cand.items() if len(d) == 1}
    type_index, gen_index = unambiguous(type_cand), unambiguous(gen_cand)
    ambiguous = sum(1 for d in gen_cand.values() if len(d) > 1)
    print(f"  male-cns FBbt index: {len(gen_index)} unambiguous names "
          f"({len(type_index)} via authoritative type column; "
          f"{ambiguous} names skipped as ambiguous)", file=sys.stderr)
    return type_index, gen_index


def ols_lookup(name):
    """Conservative OLS FBbt lookup: accept only when the query appears as a
    whole token in the returned label (avoids spurious connectome-ID matches)."""
    if not USE_OLS:
        return None
    q = urllib.parse.quote(name)
    url = (f'https://www.ebi.ac.uk/ols4/api/search?q={q}&ontology=fbbt'
           f'&type=class&exact=false&rows=5&fieldList=obo_id,label')
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            docs = json.load(r).get('response', {}).get('docs', [])
    except Exception:  # noqa: BLE001
        return None
    tokens = set(re.findall(r'\w+', name.lower()))
    for d in docs:
        label = (d.get('label') or '')
        obo = (d.get('obo_id') or '')
        if obo.startswith('FBbt') and tokens and tokens <= set(re.findall(r'\w+', label.lower())):
            return (obo.replace('FBbt:', 'FBbt:'), label, 'exact')
    return None


def main():
    with open(MERGED, newline='', encoding='utf-8') as f:
        fieldnames = list(csv.DictReader(f, delimiter='\t').fieldnames)
        f.seek(0)
        rows = list(csv.DictReader(f, delimiter='\t'))

    type_index, gen_index = build_fbbt_index()
    n_source = n_carry = n_gen = n_ols = 0
    still_unmapped = []

    for row in rows:
        ct = row['cell_type'].strip()
        names = [ct] + _split(row.get('also_known_as'))
        cur = (row.get('FBbt_id') or '').strip()

        # 1. The male-cns table is authoritative: an unambiguous match on its
        #    'type' column wins over any carried-over / previously-curated
        #    value, so fixes made at source propagate. (Deliberate exceptions
        #    are pinned in fbbt_overrides.tsv, applied last.)
        if ct in type_index:
            row['FBbt_id'], row['FBbt_name'], row['specificity'] = type_index[ct]
            n_source += 1
            continue

        # 2. No authoritative source match: keep a valid carried-over mapping
        #    (e.g. an OLS/manual mapping not present in the male-cns table).
        if FBBT_CURIE.fullmatch(cur):
            n_carry += 1
            continue

        # 3. Still unmapped/invalid: try secondary columns, then OLS.
        hit = next((gen_index[n] for n in names if n in gen_index), None)
        source = 'male-cns'
        if not hit:
            for n in names:
                hit = ols_lookup(n)
                if hit:
                    source = 'OLS'
                    break
                time.sleep(0.2)
        if hit:
            row['FBbt_id'], row['FBbt_name'], row['specificity'] = hit
            if source == 'male-cns':
                n_gen += 1
            else:
                n_ols += 1
        else:
            # Clear any invalid carried-over value so it can't reach the OWL.
            row['FBbt_id'] = row['FBbt_name'] = row['specificity'] = ''
            still_unmapped.append(ct)

    print(f"FBbt mapping: {n_source} from male-cns type column (authoritative), "
          f"{n_carry} kept from prior curation, {n_gen} via secondary columns, "
          f"{n_ols} via OLS.", file=sys.stderr)

    # Force curated overrides last, so they win over both the carried-over
    # value and the male-cns table.
    overrides = {}
    if OVERRIDES.exists():
        with open(OVERRIDES, newline='', encoding='utf-8') as f:
            for o in csv.DictReader(f, delimiter='\t'):
                overrides[o['cell_type'].strip()] = (
                    o['FBbt_id'].strip(), o['FBbt_name'].strip(),
                    (o.get('specificity') or '').strip())
    applied = 0
    for row in rows:
        ov = overrides.get(row['cell_type'].strip())
        if ov and (row['FBbt_id'], row['FBbt_name'], row['specificity']) != ov:
            row['FBbt_id'], row['FBbt_name'], row['specificity'] = ov
            applied += 1

    with open(MERGED, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nApplied {applied} curated override(s) from {OVERRIDES.name}.")
    print(f"Still unmapped ({len(still_unmapped)}): {', '.join(still_unmapped)}")


if __name__ == '__main__':
    main()
