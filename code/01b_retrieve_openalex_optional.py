"""Optional - Cross-check of the corpus with OpenAlex (not used for the paper's results).

On the retrieval day (15/11/2026) the OpenAlex API refused unauthenticated requests
(daily budget exhausted for the network). With a personal key, this script retrieves
articles/reviews 2000-2026 matching the same thematic blocks x geographic terms and
reports the overlap (by DOI) with the Crossref corpus.

Usage:  export OPENALEX_API_KEY=...   (and optionally OPENALEX_MAILTO=you@example.org)
        python 01b_retrieve_openalex_optional.py
Output: data/raw/openalex/*.jsonl, data/clean/openalex_overlap.json
"""
import os, json, time, hashlib, itertools, urllib.parse, urllib.request
import pandas as pd
import importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "openalex"); os.makedirs(OUT, exist_ok=True)
spec = importlib.util.spec_from_file_location("r", os.path.join(os.path.dirname(__file__), "01_retrieve_crossref.py"))
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
FILTER = "from_publication_date:2000-01-01,to_publication_date:2026-12-31,type:article|review"
SELECT = "id,doi,title,publication_year,type,cited_by_count,primary_location,authorships,referenced_works"


def fetch(q, max_pages=10):
    fn = os.path.join(OUT, hashlib.md5(q.encode()).hexdigest()[:12] + ".jsonl")
    if os.path.exists(fn):
        return fn
    cursor, n = "*", 0
    with open(fn, "w") as f:
        while cursor and n < max_pages:
            p = {"search": q, "filter": FILTER, "select": SELECT, "per-page": 200, "cursor": cursor}
            if os.environ.get("OPENALEX_API_KEY"):
                p["api_key"] = os.environ["OPENALEX_API_KEY"]
            if os.environ.get("OPENALEX_MAILTO"):
                p["mailto"] = os.environ["OPENALEX_MAILTO"]
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(p)
            with urllib.request.urlopen(url, timeout=120) as resp:
                d = json.load(resp)
            for w in d["results"]:
                w["_query"] = q; f.write(json.dumps(w) + "\n")
            cursor = d["meta"].get("next_cursor"); n += 1
            time.sleep(0.2)
    return fn


if __name__ == "__main__":
    dois = set()
    for q in r.queries():
        fn = fetch(q)
        for l in open(fn):
            w = json.loads(l)
            if w.get("doi"):
                dois.add(w["doi"].replace("https://doi.org/", "").lower())
    cr = set(pd.read_csv(os.path.join(ROOT, "data", "clean", "corpus_screened.csv")).doi)
    res = {"openalex_unique_dois": len(dois), "crossref_corpus": len(cr),
           "crossref_corpus_found_in_openalex_results": len(cr & dois)}
    json.dump(res, open(os.path.join(ROOT, "data", "clean", "openalex_overlap.json"), "w"), indent=1)
    print(res)
