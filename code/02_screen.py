"""Step 2 - Deduplication and rule-based PRISMA screening.

Input : data/raw/crossref_search/*.jsonl
Output: data/clean/candidates_all.csv (all unique records + screening flags)
        data/clean/corpus_screened.csv (records retained)
        data/clean/prisma_counts.json
Rules (documented in the paper, Annexe A):
  R1 publication year 2000-2026
  R2 title present; language English or French (langdetect on title+abstract)
  R3 MENA geographic marker in title or abstract (country, demonym, market, region)
  R4 topical marker: a corporate-governance / CSR-ESG term from the STRONG list
     (a looser 'governance + firm word' rule was tested and dropped: low precision).
"""
import json, os, re, glob, html
import pandas as pd
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "crossref_search")
CLEAN = os.path.join(ROOT, "data", "clean")
os.makedirs(CLEAN, exist_ok=True)

GEO = {
 "Algeria": r"alger(ia|ian|ie|ien|ienne|iennes|iens)\b|algérie|algérien\w*",
 "Morocco": r"morocc\w*|moroccan|maroc\w*|casablanca",
 "Tunisia": r"tunisi\w*",
 "Libya": r"libya\w*|liby\w*|libye\w*",
 "Egypt": r"egypt\w*|égypt\w*",
 "Mauritania": r"mauritani\w*",
 "Saudi Arabia": r"saudi\w*|tadawul|arabie saoudite",
 "UAE": r"united arab emirates|\buae\b|emirat\w*|dubai|abu dhabi",
 "Qatar": r"qatar\w*",
 "Kuwait": r"kuwait\w*|koweït",
 "Bahrain": r"bahrain\w*",
 "Oman": r"\boman\b|\bomani\b|muscat",
 "Jordan": r"\bjordan(ian)?\b|amman stock|jordanie",
 "Lebanon": r"leban\w*|liban\w*",
 "Iraq": r"\biraq\w*|\birak\w*",
 "Syria": r"\bsyria\w*|\bsyrie\w*",
 "Palestine": r"palestin\w*",
 "Yemen": r"yemen\w*",
 "Iran": r"\biran\w*|tehran|téhéran",
 "Turkey": r"\bturkey\b|türkiye|turkish|istanbul|borsa istanbul|\bturquie\b",
}
REGION = {
 "MENA": r"\bmena\b|middle east and north africa|middle east & north africa|moyen-orient et afrique du nord",
 "GCC": r"\bgcc\b|gulf cooperation council|gulf countries|gulf states|arabian gulf|gulf region|pays du golfe",
 "Arab": r"\barab\b|\barabic\b|arab world|arab countries|pays arabes|monde arabe",
 "Middle East": r"middle east\w*|moyen-orient",
 "North Africa/Maghreb": r"(?<!east and )(?<!east & )north africa\w*|maghreb\w*|(?<!orient et )afrique du nord",
}
STRONG = (r"corporate governance|governance mechanism|board(s)? of directors|"
 r"board (size|independence|composition|diversity|structure|characteristics|gender|members|meetings|effectiveness|attributes)|"
 r"independent directors?|female directors?|women directors?|women on boards?|gender diversity|"
 r"audit committees?|ownership (structure|concentration)|"
 r"(family|state|institutional|foreign|managerial|government|concentrated|insider|blockholder) ownership|"
 r"ceo duality|corporate social responsibility|\bcsr\b|\besg\b|environmental,? social,? and governance|"
 r"sustainability (reporting|disclosure|report|reports|performance|assurance|committee)|corporate sustainability|"
 r"(environmental|social|carbon|csr|voluntary|integrated|non-financial|nonfinancial|esg|governance) (disclosure|reporting)|"
 r"integrated reporting|shari'?a?h? (supervisory )?boards?|shari'?a?h? governance|"
 r"family (firms?|business(es)?|owned)|institutional investors?|shareholder activism|"
 r"minority shareholders?|investor protection|stakeholder theory|agency (theory|costs?)|"
 r"(bank|banks'?|banking|firm|company|corporate|internal|risk|shari'?a?h?|islamic banks?'?) governance|governance (practices|structures?|index|mechanisms?) of (listed|the)? ?(firms?|companies|banks)|"
 r"gouvernance (d'entreprise|des entreprises|d’entreprise|bancaire|des banques)|conseil d'administration|conseil d’administration|"
 r"responsabilit[ée] soci[ae]le|responsabilit[ée] soci[ée]tale|\brse\b")
WEAK = r"governance|gouvernance"
FIRM = r"\bfirms?\b|compan(y|ies)|corporat\w*|\bbanks?\b|banking|listed|enterprises?|entreprises?|\bsmes?\b|board|insurers?|insurance"


def clean_txt(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def year(it):
    for k in ("published", "issued"):
        dp = (it.get(k) or {}).get("date-parts") or [[None]]
        if dp and dp[0] and dp[0][0]:
            return int(dp[0][0])
    return None


def lang(t):
    try:
        return detect(t)
    except Exception:
        return "unk"


if __name__ == "__main__":
    n_hits, recs = 0, {}
    for fn in glob.glob(os.path.join(RAW, "*.jsonl")):
        for line in open(fn):
            it = json.loads(line); n_hits += 1
            doi = (it.get("DOI") or "").lower()
            if not doi:
                continue
            if doi in recs:
                recs[doi]["n_queries"] += 1
                continue
            title = clean_txt(" ".join(it.get("title") or []))
            ab = clean_txt(it.get("abstract"))
            ab = re.sub(r"^(abstract|résumé|summary)\s*:?\s*", "", ab, flags=re.I)
            recs[doi] = dict(doi=doi, title=title, abstract=ab, year=year(it),
                             source=clean_txt(" ".join(it.get("container-title") or [])),
                             publisher=it.get("publisher", ""),
                             cited_by=it.get("is-referenced-by-count", 0),
                             n_authors=len(it.get("author") or []),
                             authors="; ".join(f"{a.get('family','')}, {a.get('given','')}".strip(", ")
                                               for a in (it.get("author") or [])),
                             n_queries=1)
    df = pd.DataFrame(recs.values())
    counts = {"records_identified": n_hits, "unique_records": len(df),
              "duplicates_removed": n_hits - len(df)}
    df["text"] = (df.title + ". " + df.abstract).str.lower()
    df["r1_year"] = df.year.between(2000, 2026)
    df["has_title"] = df.title.str.len() > 5
    df["lang"] = "na"
    m = df.r1_year & df.has_title
    df.loc[m, "lang"] = [lang(t) for t in (df.loc[m, "title"] + ". " + df.loc[m, "abstract"])]
    df["r2_lang"] = df.lang.isin(["en", "fr"])
    for c, p in {**GEO, **REGION}.items():
        df["geo_" + c] = df.text.str.contains(p, regex=True)
    gcols = [c for c in df.columns if c.startswith("geo_")]
    df["r3_geo"] = df[gcols].any(axis=1)
    df["r4_strong"] = df.text.str.contains(STRONG, regex=True)
    df["r4_weak"] = df.text.str.contains(WEAK, regex=True) & df.text.str.contains(FIRM, regex=True)
    df["r4_topic"] = df.r4_strong  # weak rule kept for information only (low precision on a validation sample)
    s = df[df.r1_year]; counts["excluded_out_of_period_or_no_date"] = int((~df.r1_year).sum())
    counts["excluded_no_title"] = int((~s.has_title).sum()); s = s[s.has_title]
    counts["excluded_language"] = int((~s.r2_lang).sum()); s = s[s.r2_lang]
    counts["screened_title_abstract"] = len(s)
    counts["excluded_no_mena_marker"] = int((~s.r3_geo).sum()); s = s[s.r3_geo]
    counts["excluded_off_topic"] = int((~s.r4_topic).sum()); s = s[s.r4_topic]
    counts["retained_after_screening"] = len(s)
    counts["with_abstract"] = int((s.abstract.str.len() > 50).sum())
    df.drop(columns=["text"]).to_csv(os.path.join(CLEAN, "candidates_all.csv"), index=False)
    s.drop(columns=["text"]).to_csv(os.path.join(CLEAN, "corpus_screened.csv"), index=False)
    json.dump(counts, open(os.path.join(CLEAN, "prisma_counts.json"), "w"), indent=1)
    print(json.dumps(counts, indent=1))
    print(s.lang.value_counts())
