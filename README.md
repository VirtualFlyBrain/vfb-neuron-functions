# VFB Neuron Functions

## Overview

This project maps known Drosophila neuron cell types to terms in the Drosophila anatomy ontology (FBbt) and their functions to Gene Ontology (GO) Biological Process terms, maintained by [Virtual Fly Brain](https://virtualflybrain.org).

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

### Reference resolution

We resolved the literature references in the `reference` and `link_to_paper` columns to PubMed IDs and DOIs, adding an `xrefs` column to `known_types_mapped.tsv`.

#### Approach

1. **URL parsing** -- Extracted identifiers directly from `link_to_paper` URLs:
   - PubMed and PMC links → PMIDs
   - DOI links (doi.org, bioRxiv, Nature, eLife, PLOS, Frontiers, Wiley, SAGE, PNAS) → DOIs
   - Cell Press and ScienceDirect URLs → PIIs (Publisher Item Identifiers)

2. **ID conversion** -- Batch-converted extracted DOIs, PMC IDs, and PIIs to PMIDs using the NCBI ID Converter API and PubMed E-utilities. DOIs that could not be converted (mostly bioRxiv preprints without a published journal version) were retained as `doi:` entries.

3. **Citation search** -- For references given only as text (e.g. "Ache et al. 2019"), parsed author surname and year and searched PubMed by first author and publication date. Manual overrides were added for edge cases such as typos, first-name-as-author, "von" prefixes, and preprint years differing from publication years.

#### Reference resolution results

- **510 / 517 rows with references resolved** (99%)
- **169 unique PMIDs**, 25 unique DOIs (no PMID available)
- The unmatched rows have vague references ("classic (70's Roger Hardie work)", "many paper...") that do not identify a specific publication
- IDs are pipe-separated and prefixed (`PMID:`, `doi:`), e.g. `PMID:31182867|doi:10.1101/2024.06.27.601106`

#### Reference validation

For the 127 rows where references were resolved from citation text alone (no URL), we fetched article abstracts from PubMed and assessed whether each paper plausibly studied the annotated cell types and functions. This identified 18 incorrect PMIDs where the automated citation search had matched unrelated papers (e.g. "Wang et al 2020" matching a neural network model paper instead of the oviposition circuits paper). All 18 were corrected by adding manual overrides in `resolve_references.py` with the correct PMIDs, found by targeted PubMed searches using author names, years, and topic-specific keywords. All corrected mappings were verified against the paper abstracts.

### Function-to-ontology mapping

We mapped the `known_function` and `category` columns to Gene Ontology (GO) Biological Process terms (preferred) or Neuro Behavior Ontology (NBO) terms (fallback), adding `function_ont_id` and `function_ont_label` columns to `known_types_mapped.tsv`.

#### Approach

1. **Curated dictionary** -- A manually curated mapping of ~330 normalised function terms to ontology terms covers the vast majority of annotations. Terms representing pure molecular markers (e.g. Gr5a, Ir94e) or overly broad descriptors (e.g. "behavior", "neuromodulatory") are excluded.

2. **OLS fallback** -- Any remaining unmapped terms are searched against GO and NBO in the [EMBL-EBI Ontology Lookup Service](https://www.ebi.ac.uk/ols4/), with word-overlap filtering to avoid spurious matches.

3. **Context-aware overrides** -- Several cell-type-specific adjustments ensure biological accuracy:
   - **Mushroom body output neurons (MBONs)**: "aversive" is mapped to `associative learning` rather than `olfactory behavior`, since the stimulus modality is not specified in the annotations. MBONs with `learning_and_memory` category receive learning/memory terms.
   - **Song perception vs production**: pC1a--e (female neurons responding to male courtship song) and JO-A (auditory sensory neurons) are mapped to `sensory perception of sound` rather than male song production terms.
   - **Sex-specific behavior terms**: Male-specific GO terms (`male courtship behavior, veined wing generated song production`, `male courtship behavior, veined wing vibration`) are only used when the FBbt anatomy term is itself male-specific (e.g. pIP10 (male), P1 (male)). For fruitless neurons without male-specific FBbt subclasses, the sex-neutral parent term `courtship behavior` is used instead.
   - **Egg-laying on sex-neutral anatomy**: `egg-laying behavior` is not mapped to sex-neutral descending neurons (DNa12, DNg14) or interneurons (SMP550) that lack female-specific FBbt subclasses.

#### Function mapping results

- **651 / 672 rows mapped** (97%)
- **46 unique ontology terms** used (44 GO, 2 NBO)
- 21 unmapped rows have no explicit functional information in the annotations

## Files

| File | Description |
|------|-------------|
| `known_types.tsv` | Input: cell types with functional annotations |
| `known_types_mapped.tsv` | Output: cell types with FBbt mappings, xrefs and function ontology terms added |
| `map_functions.py` | Script to map functions to GO/NBO ontology terms |
| `resolve_references.py` | Script to resolve references to PubMed IDs and DOIs |
