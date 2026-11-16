"""Step 1 - Retrieval of candidate records from the Crossref REST API.

Each query = (thematic block) x (geographic term). Top-ranked records (by Crossref
relevance) are stored raw in data/raw/crossref_search/*.jsonl, one file per query.
Re-running the script reproduces the retrieval (results may drift as Crossref grows).

Usage: python 01_retrieve_crossref.py
Optional: set env CROSSREF_MAILTO to join Crossref's polite pool.
"""
import json, os, time, hashlib, itertools, concurrent.futures as cf
import urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "raw", "crossref_search")
os.makedirs(OUT, exist_ok=True)

THEMES_EN = [
    "corporate governance",
    "board of directors",
    "board gender diversity women directors",
    "ownership structure",
    "corporate social responsibility",
    "ESG environmental social governance performance",
    "sustainability reporting disclosure",
    "Sharia supervisory board Islamic bank governance",
    "family firms governance",
    "audit committee",
    "institutional investors ownership",
]
GEO_EN = ["Algeria", "Morocco", "Tunisia", "Libya", "Egypt", "Mauritania",
          "Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Bahrain", "Oman",
          "Jordan", "Lebanon", "Iraq", "Syria", "Palestine", "Yemen", "Iran", "Turkey",
          "MENA", "GCC", "Gulf", "Arab", "Middle East", "North Africa"]
THEMES_FR = ["gouvernance d'entreprise", "responsabilité sociale des entreprises",
             "conseil d'administration"]
GEO_FR = ["Algérie", "Maroc", "Tunisie", "Liban", "Égypte", "Mauritanie", "MENA"]

FILTER = "from-pub-date:2000-01-01,until-pub-date:2026-12-31,type:journal-article"
SELECT = ("DOI,title,abstract,published,issued,type,container-title,"
          "is-referenced-by-count,author,ISSN,publisher")
ROWS = 1000
DEPTH = int(os.environ.get("CROSSREF_DEPTH", "3"))  # pages of 1000 per query


def queries():
    for t, g in itertools.product(THEMES_EN, GEO_EN):
        yield f"{t} {g}"
    for t, g in itertools.product(THEMES_FR, GEO_FR):
        yield f"{t} {g}"


def fetch(arg):
    q, offset = arg if isinstance(arg, tuple) else (arg, 0)
    key = q if offset == 0 else f"{q}|{offset}"
    fn = os.path.join(OUT, hashlib.md5(key.encode()).hexdigest()[:12] + ".jsonl")
    if os.path.exists(fn):
        return key, "cached"
    params = {"query.bibliographic": q, "filter": FILTER, "select": SELECT,
              "rows": ROWS, "sort": "relevance", "offset": offset}
    if os.environ.get("CROSSREF_MAILTO"):
        params["mailto"] = os.environ["CROSSREF_MAILTO"]
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = json.load(r)
            items = data["message"]["items"]
            with open(fn, "w") as f:
                for it in items:
                    it["_query"] = q; it["_offset"] = offset
                    f.write(json.dumps(it) + "\n")
            return key, len(items)
        except Exception as e:  # retry with back-off
            time.sleep(5 * (attempt + 1))
    return key, "FAILED"


if __name__ == "__main__":
    qs = [(q, p * ROWS) for q in queries() for p in range(DEPTH)]
    log = []
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for q, n in ex.map(fetch, qs):
            log.append({"query": q, "n": n})
            print(q, n, flush=True)
    meta = {"retrieval_date_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime()),
            "filter": FILTER, "rows_per_query": ROWS, "n_queries": len(qs), "log": log}
    with open(os.path.join(ROOT, "data", "raw", "retrieval_log.json"), "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
