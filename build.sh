#!/usr/bin/env bash
#
# Build vfb-neuron-functions.owl from the annotation sources.
#
# Runs the full pipeline (merge -> FBbt mapping -> reference resolution ->
# function mapping -> ROBOT template -> OWL) and stamps version and
# provenance metadata into the ontology. The version is date-based; the
# provenance pins the exact source revisions used (this repo's commit and the
# male-cns_curation commit that the FBbt anatomy mappings came from).
#
# Requires: python3, and ROBOT (https://robot.obolibrary.org/) on PATH.
# The reference-resolution and function-mapping stages make network calls
# (NCBI E-utilities and the EBI OLS).
#
set -euo pipefail
cd "$(dirname "$0")"

DATE=$(date +%F)
SELF=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
MCNS=$(git -C ../male-cns_curation rev-parse --short HEAD 2>/dev/null || echo unknown)
VERSION_IRI="http://virtualflybrain.org/data/VFB/OWL/releases/${DATE}/vfb-neuron-functions.owl"

# Sync the FBbt anatomy-mapping table from the (committed) male-cns_curation
# source, updating the local cache only when it actually differs.
echo "== 0/5 sync FBbt table from source =="
FBBT_CACHE="resources/all_male-cns_FBbt.tsv"
FBBT_REMOTE="repos/VirtualFlyBrain/male-cns_curation/contents/resources/all_male-cns_FBbt.tsv"
TMP=$(mktemp)
if gh api "$FBBT_REMOTE" -H "Accept: application/vnd.github.raw" > "$TMP" 2>/dev/null && [ -s "$TMP" ]; then
  if [ ! -f "$FBBT_CACHE" ] || ! cmp -s "$TMP" "$FBBT_CACHE"; then
    mkdir -p resources && cp "$TMP" "$FBBT_CACHE"
    echo "   updated $FBBT_CACHE from source"
  else
    echo "   $FBBT_CACHE already up to date"
  fi
else
  echo "   WARNING: could not fetch FBbt table; using existing cache" >&2
fi
rm -f "$TMP"

echo "== 1/5 merge sources =="            ; python3 scripts/merge_sources.py
echo "== 2/5 FBbt anatomy mapping =="      ; python3 scripts/map_fbbt.py
echo "== 3/5 resolve references =="        ; python3 scripts/resolve_references.py
echo "== 4/5 map functions =="             ; python3 scripts/map_functions.py
echo "== 5/5 ROBOT template + OWL =="      ; python3 scripts/generate_robot_template.py

robot template --template robot_template.tsv \
  --prefix "FBbt: http://purl.obolibrary.org/obo/FBbt_" \
  --prefix "GO: http://purl.obolibrary.org/obo/GO_" \
  --prefix "NBO: http://purl.obolibrary.org/obo/NBO_" \
  --prefix "RO: http://purl.obolibrary.org/obo/RO_" \
  --prefix "oboInOwl: http://www.geneontology.org/formats/oboInOwl#" \
  annotate \
    --ontology-iri "http://virtualflybrain.org/data/VFB/OWL/vfb-neuron-functions.owl" \
    --version-iri  "${VERSION_IRI}" \
    --annotation owl:versionInfo "${DATE}" \
    --annotation http://purl.org/dc/elements/1.1/creator "Virtual Fly Brain" \
    --annotation http://purl.org/dc/terms/description "capable_of_part_of (RO:0002216) relationships between adult Drosophila neuron types (FBbt) and their functions (GO Biological Process / NBO), curated by Virtual Fly Brain from the known-types spreadsheet and the BANC connectome function supplement." \
    --annotation rdfs:comment "Built ${DATE} from vfb-neuron-functions@${SELF} (sources: known-types spreadsheet + BANC_function_supplement.tsv); FBbt anatomy mappings from male-cns_curation@${MCNS} (all_male-cns_FBbt.tsv)." \
    --link-annotation http://purl.org/dc/terms/source "https://doi.org/10.1038/s41586-026-10735-w" \
    --link-annotation http://purl.org/dc/terms/license "https://creativecommons.org/licenses/by/4.0/" \
    --typed-annotation http://purl.org/dc/terms/modified "${DATE}" xsd:date \
    --output vfb-neuron-functions.owl

echo "Built vfb-neuron-functions.owl  (version ${DATE}; version-iri ${VERSION_IRI})"
