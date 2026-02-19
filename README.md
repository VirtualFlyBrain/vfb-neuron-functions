# VFB Neuron Functions

## Overview

This project maps known Drosophila neuron cell types and their functions to terms in the Drosophila anatomy ontology (FBbt), maintained by [Virtual Fly Brain](https://virtualflybrain.org).

## What we have done

The input file `known_types.tsv` contains 672 cell types with annotations of known functions, categories, experimental evidence and references, primarily from the BANC (Brain And Nerve Cord) connectome project.

We mapped these cell types to FBbt ontology terms, producing `known_types_mapped.tsv` with three additional columns: `FBbt_id`, `FBbt_name`, and `specificity`.

### Mapping approach

1. **Existing curated mappings** -- The majority of matches (542) came from an existing curated mapping file (`all_male-cns_FBbt.tsv` from the male-cns_curation project), matching on cell type name, FlyWire type, hemibrain type, MANC type and synonyms.

2. **OLS ontology search** -- Remaining unmatched types were searched against FBbt in the [EMBL-EBI Ontology Lookup Service](https://www.ebi.ac.uk/ols4/). This added a further 24 matches, including:
   - Johnston's organ neuron subtypes (JO-C, JO-DA, JO-EVM, etc.)
   - Vertical system neurons (VS1--VS6)
   - Oviposition descending neurons (oviDNa, oviDNb)
   - Doublesex pC1 neurons (pC1a--pC1e)
   - Lateral horn neuron types (LHAD, LHAV, LHPV subtypes)
   - Neck motor neurons (CvN1--CvN8, CvN_A1, CvN_A2, VCvN)
   - Crop-innervating enteric motor neuron (CEM)
   - Circular muscle of uterus motor neuron (CMU)
   - Protocerebral bridge--ellipsoid body--nodulus neurons (PEN)
   - Dopaminergic PAM neurons, lobula plate tangential neurons (FD1, FD3), and others

### Mapping results

- **566 / 672 types mapped (84%)**
- **106 types unmapped** -- these are mostly BANC-specific names for which no FBbt term currently exists (e.g. SApp, SA_VTV, PhG, LB, LgLG subtypes, DProN, putative types)
- Where a mapping is to a parent class rather than an exact type match, `specificity` is set to `parent_term`

## Files

| File | Description |
|------|-------------|
| `known_types.tsv` | Input: cell types with functional annotations |
| `known_types_mapped.tsv` | Output: cell types with FBbt mappings added |
