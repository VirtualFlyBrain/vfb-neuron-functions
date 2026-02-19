#!/usr/bin/env python3
"""Resolve references in known_types_mapped.tsv to PubMed IDs and DOIs."""

import csv
import re
import json
import time
import sys
import urllib.request
import urllib.parse
from collections import OrderedDict

INPUT = 'known_types_mapped.tsv'
OUTPUT = 'known_types_mapped.tsv'

# Manual citation overrides: (author_as_parsed, year) → PMID
# For cases where the author name in the reference doesn't match PubMed's first-author
CITATION_OVERRIDES = {
    ('Philipsborn', '2011'): '21315261',    # von Philipsborn
    ('Sancer', '2019'): '31811399',          # Gizem Sancer
    ('Gizem', '2019'): '31811399',           # Gizem et al.2019 (first name used)
    ('McKellar', '2019'): '30661796',        # McKellar et al. 2019
    ('Frighetto', '2025'): '41278920',       # Frighetto et al. 2025
    ('Tanaka', '2022'): '35508172',          # Tanaka & Clark 2022
    ('Zacarias', '2021'): '30209268',        # Zacarias et al. (actual pub year 2018)
    ('Erginkaya', '2023'): '37904921',       # Erginkaya et al. 2023
    ('Tuthil', '2013'): '23849200',          # Typo for Tuthill 2013
    ('Fujiwara', '2020'): '35525243',        # Published 2022, cited as 2020
    ('Clowney', '2019'): '26279475',         # Published 2015, cited as 2019
    ('Mollá-Albaladejo', '2024'): '40631860',  # Wrong year in citation
    ('Sten', '2021'): '34234348',            # Wrong year in citation

}

# Overrides for refs without year (keyed on normalised ref text)
TEXT_OVERRIDES = {
    'serbe, et al': '26853306',           # Serbe et al. 2016 medulla neurons
    'christenson, et al': '38755272',     # Christenson et al. 2024 hue selectivity
}

def split_refs(refs_str):
    """Split reference string into individual citations.
    Handles both semicolon and comma separation.
    E.g. 'Bidaye et al. 2020, Braun et al. 2024; Zacarias et al., 2021'
    → ['Bidaye et al. 2020', 'Braun et al. 2024', 'Zacarias et al., 2021']
    """
    # First split on semicolons
    parts = [p.strip() for p in re.split(r';\s*', refs_str) if p.strip()]
    # Then check each part for comma-separated citations
    # A comma separates citations if it's followed by an author-like pattern with a year
    result = []
    for part in parts:
        # Try to split on commas that separate distinct citations
        # Pattern: "Author et al. YEAR, Author et al. YEAR"
        sub_parts = re.split(r',\s*(?=[A-ZÀ-ÖØ-Þ](?:[a-zà-öø-ÿ]+(?:[- ][A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+)*)\s+(?:et\s+al|&|\d{4}))', part)
        result.extend([s.strip() for s in sub_parts if s.strip()])
    return result


# --- Phase 1: URL parsing functions ---

def extract_doi_from_url(url):
    """Extract DOI from various URL formats."""
    url = url.strip().rstrip('/')

    # Direct DOI URLs (http, https, or bare doi.org)
    m = re.match(r'https?://(?:dx\.)?doi\.org/(10\..+)', url)
    if m:
        return clean_doi(m.group(1))
    m = re.match(r'(?:dx\.)?doi\.org/(10\..+)', url)
    if m:
        return clean_doi(m.group(1))

    # bioRxiv / medRxiv (handle query params, .full.pdf+html, etc.)
    m = re.search(r'(?:bio|med)rxiv\.org/content/(10\.\d+/[\d.]+?)(?:v\d+)?(?:\?|\.full|$)', url)
    if m:
        return clean_doi(m.group(1))

    # Nature
    m = re.search(r'nature\.com/articles/([a-z0-9][\w-]+?)(?:\?|$)', url)
    if m:
        return f'10.1038/{m.group(1)}'

    # eLife articles
    m = re.search(r'elifesciences\.org/articles/(\d+)', url)
    if m:
        return f'10.7554/eLife.{m.group(1)}'

    # eLife reviewed preprints
    m = re.search(r'elifesciences\.org/reviewed-preprints/(\d+)', url)
    if m:
        return f'10.7554/eLife.{m.group(1)}'

    # PNAS
    m = re.search(r'pnas\.org/doi/(?:abs/|full/)?(10\.\d+/[^?]+)', url)
    if m:
        return clean_doi(m.group(1))

    # PLOS
    m = re.search(r'journals\.plos\.org/.+[?&]id=(10\.\d+/[^&]+)', url)
    if m:
        return clean_doi(m.group(1))

    # Frontiers (more flexible pattern)
    m = re.search(r'frontiersin\.org/.+/articles/(10\.\d+/[^/]+)', url)
    if m:
        doi = m.group(1)
        # Remove /full suffix if captured
        doi = doi.rstrip('/')
        return clean_doi(doi)

    # Wiley
    m = re.search(r'onlinelibrary\.wiley\.com/doi/(?:full/)?(10\.\d+/[^?]+)', url)
    if m:
        return clean_doi(m.group(1))

    # SAGE
    m = re.search(r'journals\.sagepub\.com/doi/(10\.\d+/[^?]+)', url)
    if m:
        return clean_doi(m.group(1))

    # JNeurosci
    m = re.search(r'jneurosci\.org/content/(\d+)/(\d+)/(\d+)', url)
    if m:
        # JNeurosci DOI: 10.1523/JNEUROSCI.XXXX-YY.YEAR but we can't reconstruct
        # it from vol/issue/page, so store for PubMed search
        return None

    return None


def extract_pii_from_url(url):
    """Extract PII from Cell Press / ScienceDirect URLs."""
    url = url.strip()

    # ScienceDirect (including abs/pii)
    m = re.search(r'sciencedirect\.com/science/article/(?:abs/)?pii/(\w+)', url)
    if m:
        return m.group(1)

    # Cell Press (cell.com/journal/fulltext/PII or abstract/PII)
    m = re.search(r'cell\.com/.+?/(?:fulltext|abstract)/(S[\w()-]+?)(?:\?|$)', url)
    if m:
        pii = m.group(1)
        # Normalise PII: S0092-8674(23)00472-5 → S0092867423004725
        pii_clean = re.sub(r'[()-]', '', pii)
        return pii_clean

    return None


def extract_pmid_from_url(url):
    m = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
    if m:
        return m.group(1)
    return None


def extract_pmcid_from_url(url):
    # Both old (ncbi.nlm.nih.gov/pmc) and new (pmc.ncbi.nlm.nih.gov) formats
    m = re.search(r'(?:pmc\.ncbi\.nlm\.nih\.gov|ncbi\.nlm\.nih\.gov/pmc)/articles/(PMC\d+)', url)
    if m:
        return m.group(1)
    return None


def clean_doi(doi):
    """Remove trailing punctuation and URL fragments from DOIs."""
    doi = doi.rstrip('/')
    # Remove fragment identifiers
    doi = re.sub(r'#.*$', '', doi)
    # Remove trailing query params that crept in
    doi = re.sub(r'\?.*$', '', doi)
    # Remove via%3Dihub etc
    doi = re.sub(r';.*$', '', doi)
    return doi


# --- Phase 2: NCBI API functions ---

NCBI_BASE = 'https://www.ncbi.nlm.nih.gov'
EUTILS_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
ID_CONVERTER = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/'


def ncbi_get(url, params=None):
    """Make a GET request to NCBI with rate limiting."""
    if params:
        url = url + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'VFB-neuron-functions/1.0')
    time.sleep(0.35)  # rate limit: ~3/sec
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"  API error: {e}", file=sys.stderr)
        return None


def batch_convert_ids(ids, id_type='doi'):
    """Convert a batch of DOIs or PMCIDs to PMIDs using NCBI ID Converter.
    Returns dict: input_id → pmid (or None).
    Processes in batches of 50.
    """
    results = {}
    id_list = list(ids)
    for i in range(0, len(id_list), 50):
        batch = id_list[i:i+50]
        ids_str = ','.join(batch)
        params = {'ids': ids_str, 'format': 'json'}
        if id_type == 'doi':
            params['idtype'] = 'doi'
        resp = ncbi_get(ID_CONVERTER, params)
        if resp:
            try:
                data = json.loads(resp)
                for rec in data.get('records', []):
                    key = rec.get('doi', rec.get('pmcid', '')).lower()
                    pmid = rec.get('pmid')
                    # Match back to input
                    for orig in batch:
                        if orig.lower() == key or orig.upper() == rec.get('pmcid', ''):
                            if pmid:
                                results[orig] = pmid
                            break
            except json.JSONDecodeError:
                pass
        print(f"  Converted batch {i+1}-{i+len(batch)} of {len(id_list)}", file=sys.stderr)
    return results


def search_pmid_by_pii(pii):
    """Search PubMed for an article by PII (article ID).
    Tries the clean PII and also reconstructed hyphenated format.
    """
    # Try clean PII first
    for search_pii in _pii_variants(pii):
        params = {
            'db': 'pubmed',
            'term': f'{search_pii}[aid]',
            'retmode': 'json',
            'retmax': 1,
        }
        resp = ncbi_get(EUTILS_BASE + '/esearch.fcgi', params)
        if resp:
            try:
                data = json.loads(resp)
                ids = data.get('esearchresult', {}).get('idlist', [])
                if ids:
                    return ids[0]
            except json.JSONDecodeError:
                pass
    return None


def _pii_variants(pii):
    """Generate search variants for a PII.
    E.g. S0960982224000150 → ['S0960982224000150', 'S0960-9822(24)00015-0']
    """
    variants = [pii]
    # Try to reconstruct hyphenated format: S0960-9822(24)00015-0
    # Pattern: S + 4digits + hyphen + 4digits + (2digits) + 5digits + hyphen + 1digit
    m = re.match(r'^S(\d{4})(\d{4})(\d{2})(\d{5})(\d)$', pii)
    if m:
        hyphenated = f'S{m.group(1)}-{m.group(2)}({m.group(3)}){m.group(4)}-{m.group(5)}'
        variants.append(hyphenated)
    return variants


def search_pmid_by_jneurosci(vol, issue, page):
    """Search PubMed for a JNeurosci article."""
    params = {
        'db': 'pubmed',
        'term': f'J Neurosci[journal] AND {vol}[vi] AND {page}[pg]',
        'retmode': 'json',
        'retmax': 1,
    }
    resp = ncbi_get(EUTILS_BASE + '/esearch.fcgi', params)
    if resp:
        try:
            data = json.loads(resp)
            ids = data.get('esearchresult', {}).get('idlist', [])
            if ids:
                return ids[0]
        except json.JSONDecodeError:
            pass
    return None


def parse_author_year(ref_text):
    """Parse 'Author et al. YEAR' or 'Author & Author YEAR' from reference text.
    Returns (first_author_surname, year) or None.
    """
    ref_text = ref_text.strip()
    # Remove parenthetical notes like "(valence)", "(immuno)", "(walking)"
    cleaned = re.sub(r'\([^)]*\)', '', ref_text).strip()

    # Unicode-aware author pattern: handles González, Nässel, Mollá, etc.
    # Also handles hyphenated names and "von Philipsborn" etc.
    author_pat = r'((?:von\s+|de\s+)?[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:[- ][A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+)*)'

    # Pattern 1: "Author et al. YEAR" or "Author et al., YEAR" (with optional missing space)
    m = re.match(author_pat + r'[,.]?\s*et\s+al\.?[,\s]*(\d{4})', cleaned)
    if m:
        return m.group(1), m.group(2)

    # Pattern 2: "Author & Author YEAR" or "Author and Author YEAR"
    m = re.match(author_pat + r'\s+(?:&|and)\s+\w+\.?\s+(\d{4})', cleaned)
    if m:
        return m.group(1), m.group(2)

    # Pattern 3: "Author YEAR"
    m = re.match(author_pat + r'\s+(\d{4})', cleaned)
    if m:
        return m.group(1), m.group(2)

    # Pattern 4: year anywhere in string after an author-like word
    m = re.search(author_pat + r'.*?(\d{4})', cleaned)
    if m:
        return m.group(1), m.group(2)

    return None


def search_pmid_by_citation(author, year):
    """Search PubMed by first author surname and year."""
    params = {
        'db': 'pubmed',
        'term': f'{author}[1au] AND {year}[pdat] AND drosophila',
        'retmode': 'json',
        'retmax': 5,
    }
    resp = ncbi_get(EUTILS_BASE + '/esearch.fcgi', params)
    if resp:
        try:
            data = json.loads(resp)
            ids = data.get('esearchresult', {}).get('idlist', [])
            if len(ids) == 1:
                return ids[0]
            elif len(ids) > 1:
                # Try narrower search without drosophila
                params2 = {
                    'db': 'pubmed',
                    'term': f'{author}[1au] AND {year}[pdat]',
                    'retmode': 'json',
                    'retmax': 5,
                }
                resp2 = ncbi_get(EUTILS_BASE + '/esearch.fcgi', params2)
                if resp2:
                    data2 = json.loads(resp2)
                    ids2 = data2.get('esearchresult', {}).get('idlist', [])
                    if len(ids2) == 1:
                        return ids2[0]
                # Return first hit from drosophila-scoped search
                return ids[0]
        except json.JSONDecodeError:
            pass
    return None


# --- Main ---

def main():
    # Read input
    with open(INPUT, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        fieldnames = reader.fieldnames
        rows = list(reader)
    # Strip any existing xrefs/flags columns from previous runs
    fieldnames = [f for f in fieldnames if f not in ('xrefs', 'flags')]
    for row in rows:
        row.pop('xrefs', None)
        row.pop('flags', None)
        row.pop('', None)
    print(f"Read {len(rows)} rows", file=sys.stderr)

    # --- Phase 1: Parse all unique URLs ---
    print("\n=== Phase 1: Parsing URLs ===", file=sys.stderr)

    # Collect all unique individual URLs and ref texts
    all_urls = set()
    all_ref_texts = set()
    for row in rows:
        links = row.get('link_to_paper', '').strip()
        refs = row.get('reference', '').strip()
        if links:
            for link in re.split(r';\s*', links):
                link = link.strip()
                if link and (link.startswith('http') or link.startswith('doi.org')):
                    all_urls.add(link)
        if refs:
            for ref in split_refs(refs):
                ref = ref.strip()
                if ref and len(ref) > 3:
                    all_ref_texts.add(ref)

    print(f"Unique URLs: {len(all_urls)}", file=sys.stderr)
    print(f"Unique ref texts: {len(all_ref_texts)}", file=sys.stderr)

    # Parse URLs → IDs
    url_to_pmid = {}
    url_to_doi = {}
    url_to_pmcid = {}
    url_to_pii = {}
    jneurosci_urls = {}

    for url in all_urls:
        pmid = extract_pmid_from_url(url)
        if pmid:
            url_to_pmid[url] = pmid
            continue

        pmcid = extract_pmcid_from_url(url)
        if pmcid:
            url_to_pmcid[url] = pmcid
            continue

        doi = extract_doi_from_url(url)
        if doi:
            url_to_doi[url] = doi
            continue

        pii = extract_pii_from_url(url)
        if pii:
            url_to_pii[url] = pii
            continue

        # JNeurosci special case
        m = re.search(r'jneurosci\.org/content/(\d+)/(\d+)/(\d+)', url)
        if m:
            jneurosci_urls[url] = (m.group(1), m.group(2), m.group(3))
            continue

        # ScienceDirect with via%3Dihub or other query params that blocked DOI extraction
        # Try one more time with cleaned URL
        clean_url = re.sub(r'[?;].*$', '', url)
        doi = extract_doi_from_url(clean_url)
        if doi:
            url_to_doi[url] = doi
            continue

        print(f"  Could not parse URL: {url}", file=sys.stderr)

    print(f"  Direct PMIDs from URLs: {len(url_to_pmid)}", file=sys.stderr)
    print(f"  PMCIDs from URLs: {len(url_to_pmcid)}", file=sys.stderr)
    print(f"  DOIs from URLs: {len(url_to_doi)}", file=sys.stderr)
    print(f"  PIIs from URLs: {len(url_to_pii)}", file=sys.stderr)
    print(f"  JNeurosci URLs: {len(jneurosci_urls)}", file=sys.stderr)

    # --- Phase 2: Batch convert DOIs → PMIDs ---
    print("\n=== Phase 2: Converting DOIs to PMIDs ===", file=sys.stderr)

    unique_dois = set(url_to_doi.values())
    print(f"Unique DOIs to convert: {len(unique_dois)}", file=sys.stderr)
    doi_to_pmid = batch_convert_ids(unique_dois, id_type='doi')
    print(f"  DOIs resolved to PMIDs: {len(doi_to_pmid)}", file=sys.stderr)

    # Convert PMCIDs → PMIDs
    unique_pmcids = set(url_to_pmcid.values())
    if unique_pmcids:
        print(f"PMCIDs to convert: {len(unique_pmcids)}", file=sys.stderr)
        pmcid_to_pmid = batch_convert_ids(unique_pmcids, id_type='pmcid')
        print(f"  PMCIDs resolved to PMIDs: {len(pmcid_to_pmid)}", file=sys.stderr)
    else:
        pmcid_to_pmid = {}

    # --- Phase 2b: Resolve PIIs ---
    print("\n=== Phase 2b: Resolving PIIs ===", file=sys.stderr)
    pii_to_pmid = {}
    unique_piis = set(url_to_pii.values())
    for i, pii in enumerate(unique_piis):
        pmid = search_pmid_by_pii(pii)
        if pmid:
            pii_to_pmid[pii] = pmid
        if (i + 1) % 10 == 0:
            print(f"  Resolved {i+1}/{len(unique_piis)} PIIs", file=sys.stderr)
    print(f"  PIIs resolved to PMIDs: {len(pii_to_pmid)}", file=sys.stderr)

    # --- Phase 2c: Resolve JNeurosci URLs ---
    print("\n=== Phase 2c: Resolving JNeurosci URLs ===", file=sys.stderr)
    for url, (vol, issue, page) in jneurosci_urls.items():
        pmid = search_pmid_by_jneurosci(vol, issue, page)
        if pmid:
            url_to_pmid[url] = pmid
            print(f"  JNeurosci {vol}/{issue}/{page} → PMID:{pmid}", file=sys.stderr)

    # --- Build master URL → resolved ID lookup ---
    # Priority: PMID > DOI
    url_resolved = {}  # url → ('PMID', id) or ('doi', doi)

    for url, pmid in url_to_pmid.items():
        url_resolved[url] = ('PMID', pmid)

    for url, pmcid in url_to_pmcid.items():
        pmid = pmcid_to_pmid.get(pmcid)
        if pmid:
            url_resolved[url] = ('PMID', pmid)
        # else: couldn't resolve PMCID

    for url, doi in url_to_doi.items():
        if url in url_resolved:
            continue  # already have PMID
        pmid = doi_to_pmid.get(doi)
        if pmid:
            url_resolved[url] = ('PMID', pmid)
        else:
            url_resolved[url] = ('doi', doi)

    for url, pii in url_to_pii.items():
        if url in url_resolved:
            continue
        pmid = pii_to_pmid.get(pii)
        if pmid:
            url_resolved[url] = ('PMID', pmid)
        # else: PII couldn't be resolved, URL remains unresolved

    resolved_count = sum(1 for v in url_resolved.values() if v[0] == 'PMID')
    doi_only_count = sum(1 for v in url_resolved.values() if v[0] == 'doi')
    print(f"\nURL resolution summary:", file=sys.stderr)
    print(f"  Resolved to PMID: {resolved_count}", file=sys.stderr)
    print(f"  DOI only (no PMID): {doi_only_count}", file=sys.stderr)
    print(f"  Unresolved URLs: {len(all_urls) - len(url_resolved)}", file=sys.stderr)

    # --- Phase 3: Search PubMed for text-only references ---
    print("\n=== Phase 3: Searching for text-only references ===", file=sys.stderr)

    # Figure out which ref texts still need resolution
    # A ref text needs resolution if it doesn't have a corresponding URL that resolved
    # We'll do this per-row later, but first let's pre-resolve all unique author+year combos
    citation_cache = {}  # (author, year) → pmid or None
    for ref_text in sorted(all_ref_texts):
        parsed = parse_author_year(ref_text)
        if parsed and parsed not in citation_cache:
            citation_cache[parsed] = None  # placeholder

    print(f"Unique author+year citations to search: {len(citation_cache)}", file=sys.stderr)

    for i, (author, year) in enumerate(sorted(citation_cache.keys())):
        # Check manual overrides first
        if (author, year) in CITATION_OVERRIDES:
            pmid = CITATION_OVERRIDES[(author, year)]
            citation_cache[(author, year)] = pmid
            print(f"  {author} {year} → PMID:{pmid} (override)", file=sys.stderr)
            continue
        pmid = search_pmid_by_citation(author, year)
        citation_cache[(author, year)] = pmid
        if pmid:
            print(f"  {author} {year} → PMID:{pmid}", file=sys.stderr)
        if (i + 1) % 20 == 0:
            print(f"  Searched {i+1}/{len(citation_cache)} citations", file=sys.stderr)

    found_citations = sum(1 for v in citation_cache.values() if v)
    print(f"  Citations resolved: {found_citations}/{len(citation_cache)}", file=sys.stderr)

    # --- Phase 4: Assemble per-row xrefs and flags ---
    print("\n=== Phase 4: Assembling xrefs ===", file=sys.stderr)

    for row in rows:
        refs_raw = row.get('reference', '').strip()
        links_raw = row.get('link_to_paper', '').strip()

        if not refs_raw and not links_raw:
            row['xrefs'] = ''
            row['flags'] = ''
            continue

        # Split references and links
        ref_parts = split_refs(refs_raw) if refs_raw else []
        link_parts = [l.strip() for l in re.split(r';\s*', links_raw)] if links_raw else []

        # Remove empty parts
        ref_parts = [r for r in ref_parts if r]
        link_parts = [l for l in link_parts if l and (l.startswith('http') or l.startswith('doi.org'))]

        # Resolve citations from text refs (in order)
        seen_ids = set()
        xref_ids = []
        n_resolved_citations = 0

        for ref_text in ref_parts:
            # Check text overrides first
            text_key = ref_text.strip().lower().rstrip('.')
            # Try matching with trailing period stripped and whitespace normalised
            text_key_norm = ' '.join(text_key.split())
            text_override = TEXT_OVERRIDES.get(text_key_norm)
            if text_override:
                xref = f'PMID:{text_override}'
                if xref not in seen_ids:
                    xref_ids.append(xref)
                    seen_ids.add(xref)
                n_resolved_citations += 1
                continue

            parsed = parse_author_year(ref_text)
            if parsed:
                pmid = citation_cache.get(parsed)
                if pmid:
                    xref = f'PMID:{pmid}'
                    if xref not in seen_ids:
                        xref_ids.append(xref)
                        seen_ids.add(xref)
                    n_resolved_citations += 1
                    continue
            # Citation didn't resolve - will be counted as unresolved
            pass

        # Resolve URLs and add any IDs not already found via citations
        for url in link_parts:
            if url in url_resolved:
                id_type, id_val = url_resolved[url]
                xref = f'{id_type}:{id_val}'
                if xref not in seen_ids:
                    xref_ids.append(xref)
                    seen_ids.add(xref)

        row['xrefs'] = '|'.join(xref_ids)

    # --- Write output ---
    print("\n=== Writing output ===", file=sys.stderr)
    out_fieldnames = list(fieldnames) + ['xrefs']

    with open(OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames, delimiter='\t',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Stats
    has_xrefs = sum(1 for r in rows if r.get('xrefs', '').strip())
    print(f"\nFinal stats:", file=sys.stderr)
    print(f"  Rows with xrefs: {has_xrefs}/{len(rows)}", file=sys.stderr)


if __name__ == '__main__':
    main()
