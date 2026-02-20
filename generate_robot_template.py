"""Generate a ROBOT template from known_types_mapped.tsv.

Reads the mapped neuron-function data and produces a ROBOT template TSV
that creates SubClassOf axioms: FBbt:X SubClassOf RO:0002216 some GO:Y
with axiom annotations for literature references and a provenance comment.
"""

import csv

INPUT = "known_types_mapped.tsv"
OUTPUT = "robot_template.tsv"

COMMENT = "From known types spreadsheet - https://docs.google.com/spreadsheets/d/1VHCEnurOdb4FDC_NUKZX_BpBckQ9LpKxv0CsK_ObVok/edit"

def main():
    rows = []
    func_terms = set()
    with open(INPUT, newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            fbbt = (row.get("FBbt_id") or "").strip()
            funcs = (row.get("function_ont_id") or "").strip()
            xrefs = (row.get("xrefs") or "").strip()
            if not fbbt or not funcs or not xrefs:
                continue

            for func in funcs.split("|"):
                func = func.strip()
                if func:
                    rows.append((fbbt, func, xrefs))
                    func_terms.add(func)

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
        for fbbt, func, xrefs in rows:
            writer.writerow([fbbt, "", func, xrefs, COMMENT])

    print(f"Wrote {len(rows)} data rows to {OUTPUT}")


if __name__ == "__main__":
    main()
