import requests, json, time, itertools, concurrent.futures as cf, os
TOP = ["gouvernance d'entreprise", "conseil d'administration", "responsabilité sociale des entreprises", "RSE développement durable entreprise",
       "structure de propriété actionnariat", "entreprises familiales", "comité d'audit", "finance islamique gouvernance"]
GEO = ["Algérie", "Maroc", "Tunisie", "Libye", "Mauritanie", "Égypte", "Liban", "Maghreb", "Afrique du Nord", "Moyen-Orient", "pays arabes", "MENA"]
SEL = "DOI,title,abstract,author,container-title,published,issued,type,is-referenced-by-count,publisher"
OUT = "fr_ext"
MAILTO = os.environ.get("CROSSREF_MAILTO")
def call(args):
    t, g, off = args
    fn = f"{OUT}/{TOP.index(t)}_{GEO.index(g)}_{off}.json"
    if os.path.exists(fn): return fn, 'cached'
    p = {"query.bibliographic": f"{t} {g}", "rows": 1000, "offset": off, "sort": "relevance",
         "filter": "type:journal-article,from-pub-date:2000-01-01,until-pub-date:2026-12-31", "select": SEL}
    if MAILTO: p["mailto"] = MAILTO
    for i in range(6):
        try:
            r = requests.get("https://api.crossref.org/works", params=p, timeout=180)
            if r.status_code == 200:
                m = r.json()["message"]; json.dump({"total": m["total-results"], "items": m["items"]}, open(fn, "w")); return fn, len(m["items"])
        except Exception: pass
        time.sleep(5 * (i + 1))
    return fn, 'FAIL'
jobs = [(t, g, o) for t, g in itertools.product(TOP, GEO) for o in range(0, 6000, 1000)]
with cf.ThreadPoolExecutor(4) as ex:
    for k, r in enumerate(ex.map(call, jobs), 1):
        if k % 24 == 0 or r[1] == 'FAIL': print(k, len(jobs), r, flush=True)
print('DONE')
