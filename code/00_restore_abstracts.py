"""Restore publisher abstracts removed from the public package.

Abstracts deposited in Crossref belong to their publishers and are not
redistributed here. This script fetches them again from the Crossref API
(by DOI) and re-inserts an `abstract` column in the clean CSV files, so that
04_analysis.py and 06_extra_stats.py run exactly as in the paper.
Usage: python3 00_restore_abstracts.py [--limit N]
"""
import os, re, sys, time, json, concurrent.futures as cf
import pandas as pd, requests

C = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "clean")
MAILTO = os.environ.get("CROSSREF_MAILTO", "")
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
CACHE = os.path.join(C, "abstracts_cache.json")

def fetch(doi):
    url = "https://api.crossref.org/works/" + requests.utils.quote(doi, safe="")
    params = {"mailto": MAILTO} if MAILTO else {}
    for i in range(4):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                a = r.json()["message"].get("abstract")
                return doi, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", a)).strip() if a else None
            if r.status_code == 404:
                return doi, None
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    return doi, None

cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
base = pd.read_csv(os.path.join(C, "corpus_screened.csv"), low_memory=False)
todo = [d for d in base.loc[base.has_abstract == 1, "doi"] if d not in cache]
if LIMIT: todo = todo[:LIMIT]
with cf.ThreadPoolExecutor(4) as ex:
    for k, (doi, a) in enumerate(ex.map(fetch, todo), 1):
        cache[doi] = a
        if k % 200 == 0:
            print(k, "/", len(todo), flush=True); json.dump(cache, open(CACHE, "w"))
json.dump(cache, open(CACHE, "w"))

for f in ["corpus_screened.csv", "corpus_coded.csv", "synthesis_selection.csv"]:
    p = os.path.join(C, f); d = pd.read_csv(p, low_memory=False)
    if "has_abstract" not in d.columns:
        continue
    i = d.columns.get_loc("has_abstract")
    d.insert(i, "abstract", d.doi.map(cache))
    d.drop(columns=["has_abstract"]).to_csv(p, index=False)
    print(f, "abstracts restored:", int(d.abstract.notna().sum()))
