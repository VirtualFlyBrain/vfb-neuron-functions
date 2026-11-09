#!/usr/bin/env bash
#
# Build vfb-neuron-functions.owl from the annotation sources.
#
# Runs the full pipeline (merge -> FBbt mapping -> reference resolution ->
# function mapping -> ROBOT template -> OWL) and stamps version and
# provenance metadata into the ontology. The version is date-based; the
# provenance pins the exact source revisions used (this repo's commit and the
# connectome-curation commit that built the FBbt anatomy mappings).
#
# Requires: python3, and ROBOT (https://robot.obolibrary.org/) on PATH. To
# rebuild the FBbt table: a connectome-curation checkout (../connectome-curation,
# or set CONNECTOME_CURATION), uv, and NEUPRINT_TOKEN.
# The reference-resolution and function-mapping stages make network calls
# (NCBI E-utilities and the EBI OLS).
#
set -euo pipefail
cd "$(dirname "$0")"

DATE=$(date +%F)
SELF=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
CC="${CONNECTOME_CURATION:-../connectome-curation}"
CCREV=$(git -C "$CC" rev-parse --short HEAD 2>/dev/null || echo unknown)
VERSION_IRI="http://virtualflybrain.org/data/VFB/OWL/releases/${DATE}/vfb-neuron-functions.owl"

# Build the male-CNS FBbt typing table with connectome-curation (from neuPrint
# and its mapping tables) and copy it here. Neither copy is committed.
echo "== 0/5 build FBbt table with connectome-curation =="
FBBT_CACHE="resources/all_male-cns_FBbt.tsv"
FBBT_BUILT="$CC/datasets/male_cns/resources/all_male-cns_FBbt.tsv"
if [ -d "$CC" ] && (cd "$CC" && uv run vfb-curation build-typing male_cns); then
  mkdir -p resources && cp "$FBBT_BUILT" "$FBBT_CACHE"
  echo "   $FBBT_CACHE built from connectome-curation@${CCREV}"
else
  CCREV="${CCREV} (build failed; cached table)"
  echo "   WARNING: could not build the FBbt table in $CC; using existing cache" >&2
fi

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
    --annotation rdfs:comment "Built ${DATE} from vfb-neuron-functions@${SELF} (sources: known-types spreadsheet + BANC_function_supplement.tsv); FBbt anatomy mappings from connectome-curation@${CCREV} (vfb-curation build-typing male_cns)." \
    --link-annotation http://purl.org/dc/terms/source "https://doi.org/10.1038/s41586-026-10735-w" \
    --link-annotation http://purl.org/dc/terms/license "https://creativecommons.org/licenses/by/4.0/" \
    --typed-annotation http://purl.org/dc/terms/modified "${DATE}" xsd:date \
    --output vfb-neuron-functions.owl

echo "Built vfb-neuron-functions.owl  (version ${DATE}; version-iri ${VERSION_IRI})"
