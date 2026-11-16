"""Step 3 - Enrichment of retained records with full Crossref metadata
(reference lists, author affiliations, subjects).

Input : data/clean/corpus_screened.csv
Output: data/raw/crossref_full/*.json, data/clean/references.csv (citing_doi, cited_doi, cited_label),
        data/clean/affiliations.csv (doi, author_pos, affiliation, country)
"""
import json, os, hashlib, time, re, urllib.request, urllib.parse, concurrent.futures as cf
import pandas as pd, pycountry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL = os.path.join(ROOT, "data", "raw", "crossref_full"); os.makedirs(FULL, exist_ok=True)
CLEAN = os.path.join(ROOT, "data", "clean")


def get(doi):
    fn = os.path.join(FULL, hashlib.md5(doi.encode()).hexdigest()[:16] + ".json")
    if os.path.exists(fn):
        return doi, True
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    if os.environ.get("CROSSREF_MAILTO"):
        url += "?mailto=" + os.environ["CROSSREF_MAILTO"]
    for a in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                json.dump(json.load(r)["message"], open(fn, "w"))
            return doi, True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return doi, False
            time.sleep(3 * (a + 1))
        except Exception:
            time.sleep(3 * (a + 1))
    return doi, False


# country names + frequent variants for affiliation parsing
NAMES = {c.name: c.name for c in pycountry.countries}
for c in pycountry.countries:
    for att in ("common_name", "official_name"):
        if hasattr(c, att):
            NAMES[getattr(c, att)] = c.name
NAMES.update({"USA": "United States", "U.S.A": "United States", "UK": "United Kingdom",
              "England": "United Kingdom", "Scotland": "United Kingdom", "Wales": "United Kingdom",
              "UAE": "United Arab Emirates", "U.A.E": "United Arab Emirates", "Turkey": "Türkiye",
              "Iran": "Iran, Islamic Republic of", "Korea": "Korea, Republic of",
              "Palestine": "Palestine, State of", "Syria": "Syrian Arab Republic",
              "Vietnam": "Viet Nam", "Russia": "Russian Federation", "Algérie": "Algeria",
              "Maroc": "Morocco", "Tunisie": "Tunisia", "Liban": "Lebanon", "France": "France",
              "Saudi": "Saudi Arabia", "KSA": "Saudi Arabia", "Dubai": "United Arab Emirates",
              "Abu Dhabi": "United Arab Emirates", "Sharjah": "United Arab Emirates",
              "Riyadh": "Saudi Arabia", "Jeddah": "Saudi Arabia", "Cairo": "Egypt", "Amman": "Jordan",
              "Tehran": "Iran, Islamic Republic of", "Istanbul": "Türkiye", "Ankara": "Türkiye",
              "Tunis": "Tunisia", "Sfax": "Tunisia", "Sousse": "Tunisia", "Doha": "Qatar",
              "Muscat": "Oman", "Beirut": "Lebanon", "Baghdad": "Iraq", "Casablanca": "Morocco",
              "Rabat": "Morocco", "Algiers": "Algeria", "Alger": "Algeria", "Malaysia": "Malaysia"})
PAT = sorted(NAMES, key=len, reverse=True)
RX = re.compile(r"\b(" + "|".join(re.escape(p) for p in PAT) + r")\b")


def country_of(aff):
    hits = RX.findall(aff or "")
    return NAMES[hits[-1]] if hits else ""


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(CLEAN, "corpus_screened.csv"))
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(get, df.doi))
    print("fetched", sum(ok for _, ok in res), "of", len(res))
    refs, affs, subj = [], [], {}
    for doi in df.doi:
        fn = os.path.join(FULL, hashlib.md5(doi.encode()).hexdigest()[:16] + ".json")
        if not os.path.exists(fn):
            continue
        m = json.load(open(fn))
        subj[doi] = "; ".join(m.get("subject") or [])
        for r in m.get("reference") or []:
            cd = (r.get("DOI") or "").lower()
            lab = r.get("unstructured") or " ".join(str(r.get(k, "")) for k in ("author", "year", "article-title", "journal-title"))
            refs.append(dict(citing_doi=doi, cited_doi=cd, cited_label=lab[:300]))
        for i, a in enumerate(m.get("author") or []):
            for af in a.get("affiliation") or []:
                nm = af.get("name", "")
                affs.append(dict(doi=doi, author_pos=i, affiliation=nm, country=country_of(nm)))
        df.loc[df.doi == doi, "n_refs_deposited"] = len(m.get("reference") or [])
        df.loc[df.doi == doi, "reference_count"] = m.get("reference-count", 0)
    df["subjects"] = df.doi.map(subj)
    pd.DataFrame(refs).to_csv(os.path.join(CLEAN, "references.csv"), index=False)
    pd.DataFrame(affs).to_csv(os.path.join(CLEAN, "affiliations.csv"), index=False)
    df.to_csv(os.path.join(CLEAN, "corpus_screened.csv"), index=False)
    print("refs", len(refs), "with DOI", sum(1 for r in refs if r["cited_doi"]), "affs", len(affs))
