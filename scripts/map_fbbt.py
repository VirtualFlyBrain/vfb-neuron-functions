#!/usr/bin/env python3
"""Fill in FBbt anatomy mappings for neuron_functions.tsv.

FBbt mappings are not produced by the annotation pipeline; the bulk of them
were curated in the VirtualFlyBrain male-cns_curation project (the file
``resources/all_male-cns_FBbt.tsv``) with some added by OLS lookup.

This script re-attempts EVERY row that still has an empty ``FBbt_id`` on each
run, so that cell types gain mappings as new FBbt terms become available. Rows
that are already mapped are left untouched. It looks each cell type up (by its
name and any aliases) in the male-cns FBbt table first, then falls back to a
conservative OLS search, and reports whatever is still unmapped.

The male-cns table lives in the private VirtualFlyBrain/male-cns_curation repo.
If ``resources/all_male-cns_FBbt.tsv`` is absent, the script tries to fetch it
with the GitHub CLI (`gh`); failing that it proceeds with the OLS fallback only.
"""

import csv
import json
import re
import subprocess
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

FBBT_REPO = 'VirtualFlyBrain/male-cns_curation'
FBBT_PATH = 'resources/all_male-cns_FBbt.tsv'

# A clean, single FBbt CURIE (what a class IRI must be built from).
FBBT_CURIE = re.compile(r'FBbt:\d+')

# Columns in all_male-cns_FBbt.tsv whose values name a cell type.
MATCH_COLS = ['type', 'synonyms', 'hemibrainType', 'flywireType', 'mancType']
USE_OLS = True


def _fetch_fbbt_table():
    """Try to download the male-cns FBbt table via the GitHub CLI."""
    FBBT_TABLE.parent.mkdir(exist_ok=True)
    try:
        out = subprocess.run(
            ['gh', 'api', f'repos/{FBBT_REPO}/contents/{FBBT_PATH}',
             '-H', 'Accept: application/vnd.github.raw'],
            capture_output=True, check=True)
        FBBT_TABLE.write_bytes(out.stdout)
        print(f"  fetched {FBBT_PATH} via gh", file=sys.stderr)
        return True
    except Exception as e:  # noqa: BLE001 - best effort
        print(f"  could not fetch FBbt table ({e}); OLS fallback only", file=sys.stderr)
        return False


def _split(value):
    return [v.strip() for v in re.split(r'[|,;]', value or '') if v.strip()]


def build_fbbt_index():
    """value -> (FBbt_id, FBbt_name, specificity), unambiguous matches only."""
    if not FBBT_TABLE.exists() and not _fetch_fbbt_table():
        return {}
    # value -> {fbbt_id: (fbbt_name, specificity)}
    candidates = {}
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
            for col in MATCH_COLS:
                for val in _split(row.get(col)):
                    candidates.setdefault(val, {})[fid] = info
    # Keep only values that map to exactly one FBbt term.
    index = {v: next(iter(d.values())) for v, d in candidates.items() if len(d) == 1}
    ambiguous = sum(1 for d in candidates.values() if len(d) > 1)
    print(f"  male-cns FBbt index: {len(index)} unambiguous names "
          f"({ambiguous} names skipped as ambiguous)", file=sys.stderr)
    return index


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

    # Re-attempt rows that are unmapped OR carry an invalid (e.g. compound)
    # FBbt_id, so bad values that were carried over get cleaned up.
    blanks = [r for r in rows if not FBBT_CURIE.fullmatch((r.get('FBbt_id') or '').strip())]
    print(f"{len(blanks)}/{len(rows)} rows need an FBbt mapping; re-attempting.",
          file=sys.stderr)

    index = build_fbbt_index()
    filled_file = filled_ols = 0
    still_unmapped = []

    for row in blanks:
        names = [row['cell_type'].strip()] + _split(row.get('also_known_as'))
        hit = next((index[n] for n in names if n in index), None)
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
                filled_file += 1
            else:
                filled_ols += 1
        else:
            # Clear any invalid carried-over value so it can't reach the OWL.
            row['FBbt_id'] = row['FBbt_name'] = row['specificity'] = ''
            still_unmapped.append(row['cell_type'])

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

    print(f"\nFilled {filled_file} from male-cns table, {filled_ols} from OLS.")
    print(f"Applied {applied} curated override(s) from {OVERRIDES.name}.")
    print(f"Still unmapped ({len(still_unmapped)}): {', '.join(still_unmapped)}")


if __name__ == '__main__':
    main()
