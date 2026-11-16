import json, glob, re, importlib.util, pandas as pd, sys
spec = importlib.util.spec_from_file_location("scr", "../../code/02_screen.py"); S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
recs = {}; nhits = 0; totals = []
for fn in glob.glob(os.environ.get("FR_EXT_DIR", "fr_ext") + "/*.json"):
    j = json.load(open(fn))
    if fn.endswith('_0.json'): totals.append(j['total'])
    for it in j['items']:
        nhits += 1; doi = (it.get('DOI') or '').lower()
        if not doi or doi in recs: continue
        ab = re.sub(r"^(abstract|résumé|summary)\s*:?\s*", "", S.clean_txt(it.get('abstract')), flags=re.I)
        recs[doi] = dict(doi=doi, title=S.clean_txt(' '.join(it.get('title') or [])), abstract=ab, year=S.year(it),
                         source=S.clean_txt(' '.join(it.get('container-title') or [])), cited_by=it.get('is-referenced-by-count', 0))
d = pd.DataFrame(recs.values())
d['text'] = (d.title + '. ' + d.abstract).str.lower()
d = d[d.year.between(2000, 2026) & (d.title.str.len() > 5)]
corpus = set(pd.read_csv('../../data/clean/corpus_screened.csv', usecols=['doi']).doi.str.lower())
cand = set(pd.read_csv('../../data/raw/candidates_identification.csv.gz', usecols=['doi']).doi.str.lower())
d['geo'] = d.text.str.contains('|'.join(list(S.GEO.values()) + list(S.REGION.values())), regex=True)
d['r4'] = d.text.str.contains(S.STRONG, regex=True)
FR_EXTRA = r"structure (de propriété|de l.actionnariat)|actionnariat (familial|public|étranger|institutionnel)|entreprises? familiales?|comité d.audit|administrateurs? indépendants?|développement durable|finance islamique|banques? islamiques?|gouvernance charaïque|divulgation (sociétale|environnementale|volontaire)|reporting (extra-financier|intégré|de durabilité)"
d['r4x'] = d.r4 | d.text.str.contains(FR_EXTRA, regex=True)
new = d[~d.doi.isin(corpus)]
cand_geo = new[new.geo]
lang = lambda t: S.lang(t)
sel = cand_geo[cand_geo.r4x].copy(); sel['lang'] = [lang(t) for t in sel.title + '. ' + sel.abstract]
out = dict(queries=96, calls=576, min_total=min(totals), records=nhits, unique=len(recs), unique_in_period=len(d),
           already_in_corpus=int(d.doi.isin(corpus).sum()), already_in_initial_candidates=int(d.doi.isin(cand).sum()),
           new_with_geo=int(len(cand_geo)), new_retained_same_rules=int(((sel.r4) & sel.lang.isin(['en','fr'])).sum()),
           new_retained_same_rules_fr=int(((sel.r4) & (sel.lang=='fr')).sum()),
           new_retained_extended_r4=int(sel.lang.isin(['en','fr']).sum()), new_retained_extended_r4_fr=int((sel.lang=='fr').sum()),
           corpus_fr_found=int(d[d.doi.isin(corpus)].shape[0]))
sel.drop(columns=['text']).to_csv('a9_new_candidates.csv', index=False)
json.dump(out, open('a9.json','w'), indent=1); print(json.dumps(out, indent=1))
print(sel[sel.lang=='fr'][['year','title','source']].head(40).to_string())
