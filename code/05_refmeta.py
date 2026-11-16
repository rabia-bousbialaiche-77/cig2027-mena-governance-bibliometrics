"""Step 5 - Metadata (Crossref) and APA 7 formatting for cited references.
Usage: python 05_refmeta.py            -> co-citation core + most cited corpus docs
       python 05_refmeta.py doi1 doi2  -> specific DOIs (printed in APA)
Output: tables/cocitation_core_labeled.csv, data/clean/apa_cache.json
"""
import os, sys, json, hashlib, re, html, urllib.request, urllib.parse, concurrent.futures as cf
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "data", "raw", "crossref_full"); os.makedirs(FULL, exist_ok=True)
T = os.path.join(ROOT, "tables"); C = os.path.join(ROOT, "data", "clean")


def meta(doi):
    doi = doi.lower()
    fn = os.path.join(FULL, hashlib.md5(doi.encode()).hexdigest()[:16] + ".json")
    if not os.path.exists(fn):
        try:
            url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
            with urllib.request.urlopen(url, timeout=60) as r:
                json.dump(json.load(r)["message"], open(fn, "w"))
        except Exception:
            return None
    return json.load(open(fn))


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def apa(m):
    if m is None:
        return ""
    aus = []
    for a in m.get("author") or []:
        if "family" in a:
            giv = a.get("given", "")
            ini = " ".join(p[0] + "." for p in re.split(r"[\s]+", giv) if p)
            ini = re.sub(r"(\w)\.-", r"\1.-", ini)
            aus.append(f"{a['family']}, {ini}".strip().rstrip(","))
        elif "name" in a:
            aus.append(a["name"])
    if len(aus) == 0:
        au = ""
    elif len(aus) == 1:
        au = aus[0]
    elif len(aus) <= 20:
        au = ", ".join(aus[:-1]) + ", & " + aus[-1]
    else:
        au = ", ".join(aus[:19]) + ", … " + aus[-1]
    dp = (m.get("published-print") or m.get("published") or m.get("issued") or {}).get("date-parts", [[None]])[0]
    yr = dp[0] if dp and dp[0] else "s.d."
    title = clean(" ".join(m.get("title") or []))
    cont = clean(" ".join(m.get("container-title") or []))
    vol, iss, pg = m.get("volume", ""), m.get("issue", ""), m.get("page", "") or m.get("article-number", "")
    s = f"{au} ({yr}). {title}."
    if m.get("type") == "book":
        s = f"{au} ({yr}). *{title}*. {m.get('publisher','')}."
    elif m.get("type") == "book-chapter":
        s += f" In *{cont}*" + (f" (pp. {pg.replace('-', '–')})" if pg else "") + f". {m.get('publisher','')}."
    else:
        s += f" *{cont}*"
        if vol:
            s += f", *{vol}*"
        if iss:
            s += f"({iss})"
        if pg:
            s += f", {pg.replace('-', '–')}"
        s += "."
    s += f" https://doi.org/{m['DOI'].lower()}"
    return s


if __name__ == "__main__":
    cache_fn = os.path.join(C, "apa_cache.json")
    cache = json.load(open(cache_fn)) if os.path.exists(cache_fn) else {}
    if len(sys.argv) > 1:
        dois = [d.lower() for d in sys.argv[1:]]
    else:
        cc = pd.read_csv(os.path.join(T, "cocitation_clusters.csv"))
        dois = list(cc.cited_doi) + list(pd.read_csv(os.path.join(T, "top_cited.csv")).doi)
    with cf.ThreadPoolExecutor(6) as ex:
        ms = list(ex.map(meta, dois))
    for d, m in zip(dois, ms):
        cache[d] = apa(m)
        if len(sys.argv) > 1:
            print(cache[d])
    json.dump(cache, open(cache_fn, "w"), indent=0, ensure_ascii=False)
    if len(sys.argv) == 1:
        cc["apa"] = cc.cited_doi.map(cache)
        cc.to_csv(os.path.join(T, "cocitation_core_labeled.csv"), index=False)
        for k, g in cc.groupby("cluster"):
            print("== cluster", k, len(g))
            for _, r in g.head(30).iterrows():
                print(r.n_citing, r.apa[:170])
