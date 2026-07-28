"""Generate a ROBOT template from neuron_functions.tsv.

Reads the merged neuron-function data and produces a ROBOT template TSV
that creates SubClassOf axioms: FBbt:X SubClassOf RO:0002216 some GO:Y
with axiom annotations for literature references and a provenance comment.
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = str(ROOT / "neuron_functions.tsv")
OUTPUT = str(ROOT / "robot_template.tsv")

COMMENT = "From known types spreadsheet - https://docs.google.com/spreadsheets/d/1VHCEnurOdb4FDC_NUKZX_BpBckQ9LpKxv0CsK_ObVok/edit"

# A single class term must be a clean CURIE; anything else (blank, compound
# "FBbt:x|FBbt:y" mappings, stray text) would produce an invalid OWL IRI.
CURIE = re.compile(r"[A-Za-z]+:\d+$")

# Only assert functions on exact FBbt matches. Mappings to a broader parent
# ("parent_term") or a general class ("general_term") are kept in
# neuron_functions.tsv but excluded here, to avoid asserting a function on a
# whole anatomy class based on one subtype (and collapsing distinct subtypes
# onto a shared parent).
EXCLUDE_SPECIFICITY = {"parent_term", "general_term"}

def main():
    entries = []   # eligible rows: {fbbt, funcs[], xrefs, source, cell_type}
    skipped = 0
    skipped_broad = 0
    with open(INPUT, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            fbbt = (row.get("FBbt_id") or "").strip()
            funcs = (row.get("function_ont_id") or "").strip()
            xrefs = (row.get("xrefs") or "").strip()
            if not fbbt or not funcs or not xrefs:
                continue
            if not CURIE.match(fbbt):
                print(f"  skipping {row.get('cell_type')}: non-CURIE FBbt_id "
                      f"{fbbt!r}", file=sys.stderr)
                skipped += 1
                continue
            if (row.get("specificity") or "").strip() in EXCLUDE_SPECIFICITY:
                skipped_broad += 1
                continue
            valid_funcs = []
            for func in funcs.split("|"):
                func = func.strip()
                if not func:
                    continue
                if not CURIE.match(func):
                    print(f"  skipping {row.get('cell_type')} func {func!r}: "
                          f"not a CURIE", file=sys.stderr)
                    skipped += 1
                    continue
                valid_funcs.append(func)
            if valid_funcs:
                entries.append({
                    "fbbt": fbbt, "funcs": valid_funcs, "xrefs": xrefs,
                    "source": (row.get("annotation_source") or "").strip(),
                    "cell_type": (row.get("cell_type") or "").strip(),
                })

    # Prefer BANC: where the same FBbt class is annotated from both BANC and
    # known_types, keep only the BANC rows (even if this loses axioms).
    banc_fbbt = {e["fbbt"] for e in entries if e["source"] == "BANC"}
    deduped = 0
    rows = []
    func_terms = set()
    for e in entries:
        if e["fbbt"] in banc_fbbt and e["source"] != "BANC":
            print(f"  dropping {e['cell_type']} ({e['fbbt']}): FBbt class is also "
                  f"BANC-sourced", file=sys.stderr)
            deduped += 1
            continue
        comment = "" if e["source"] == "BANC" else COMMENT
        for func in e["funcs"]:
            rows.append((e["fbbt"], func, e["xrefs"], comment))
            func_terms.add(func)

    if skipped:
        print(f"  ({skipped} row/term(s) skipped as non-CURIE)", file=sys.stderr)
    if skipped_broad:
        print(f"  ({skipped_broad} cell type(s) skipped as parent_term/general_term)",
              file=sys.stderr)
    if deduped:
        print(f"  ({deduped} known_types row(s) dropped; FBbt class is BANC-sourced)",
              file=sys.stderr)

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        # Row 1: human-readable headers
        writer.writerow([
            "ID",
            "TYPE",
            "SC RO:0002216 some %",
            ">A oboInOwl:hasDbXref SPLIT=|",
            ">A rdfs:comment",
        ])
        # Row 2: ROBOT template strings
        writer.writerow([
            "ID",
            "TYPE",
            "SC RO:0002216 some %",
            ">A oboInOwl:hasDbXref SPLIT=|",
            ">A rdfs:comment",
        ])
        # Declare RO:0002216 as an object property
        writer.writerow(["RO:0002216", "owl:ObjectProperty", "", "", ""])
        # Declare each function term as a class
        for func in sorted(func_terms):
            writer.writerow([func, "owl:Class", "", "", ""])
        # Data rows
        for fbbt, func, xrefs, comment in rows:
            writer.writerow([fbbt, "", func, xrefs, comment])

    print(f"Wrote {len(rows)} data rows to {OUTPUT}")


if __name__ == "__main__":
    main()
