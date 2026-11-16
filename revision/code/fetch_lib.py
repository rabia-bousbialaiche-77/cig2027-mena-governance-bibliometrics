import os
import requests, time, re, html, json
def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or "")); s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"^(abstract|résumé|summary)\s*:?\s*", "", s, flags=re.I)
def fetch_batch(dois, select="DOI,title,abstract,container-title,published,issued"):
    q = ",".join("doi:" + d for d in dois)
    for i in range(5):
        try:
            r = requests.get("https://api.crossref.org/works", params={"filter": q, "rows": len(dois), "select": select,
                             **({"mailto": os.environ["CROSSREF_MAILTO"]} if os.environ.get("CROSSREF_MAILTO") else {})}, timeout=90)
            if r.status_code == 200:
                return {it["DOI"].lower(): it for it in r.json()["message"]["items"]}
        except requests.RequestException:
            pass
        time.sleep(3 * (i + 1))
    return {}
def fetch_many(dois, size=40):
    out = {}
    for k in range(0, len(dois), size):
        out.update(fetch_batch(dois[k:k + size]))
    return out
