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

def main():
    rows = []
    func_terms = set()
    skipped = 0
    with open(INPUT, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
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

            # The provenance comment only applies to the known-types
            # spreadsheet; BANC-sourced rows carry no comment.
            comment = "" if (row.get("annotation_source") or "").strip() == "BANC" else COMMENT

            for func in funcs.split("|"):
                func = func.strip()
                if not func:
                    continue
                if not CURIE.match(func):
                    print(f"  skipping {row.get('cell_type')} func {func!r}: "
                          f"not a CURIE", file=sys.stderr)
                    skipped += 1
                    continue
                rows.append((fbbt, func, xrefs, comment))
                func_terms.add(func)
    if skipped:
        print(f"  ({skipped} row/term(s) skipped as non-CURIE)", file=sys.stderr)

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
