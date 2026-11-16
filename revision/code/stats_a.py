import pandas as pd, numpy as np, json, collections
d = pd.read_csv('../../data/clean/corpus_coded.csv', low_memory=False)
O = {}
k = lambda c: d['k_' + c]
GOV = ['corporate governance','board of directors','board independence','board size','CEO duality','board gender diversity','audit committee','external audit / audit quality','ownership structure','ownership concentration','family ownership / family firms','state ownership','institutional investors','foreign ownership','managerial ownership','executive compensation','CEO characteristics','shareholder rights / investor protection','political connections','corporate governance code','Sharia governance']
SUS = ['CSR disclosure','environmental disclosure','sustainability reporting','integrated reporting','CSR','ESG','sustainability','environmental performance','climate / carbon','green finance','SDGs']
g = d[['k_'+c for c in GOV]].any(axis=1); s = d[['k_'+c for c in SUS]].any(axis=1)
d['cat'] = np.select([g & s, g & ~s, ~g & s], ['intersection','gouv_seule','dur_seule'], 'autre')
P = [('2000–2012',2000,2012),('2013–2019',2013,2019),('2020–2026',2020,2026)]
O['A3_total'] = d.cat.value_counts().to_dict()
O['A3_by_period_pct'] = {p: (d[d.year.between(a,b)].cat.value_counts(normalize=True)*100).round(1).to_dict() for p,a,b in P}
O['A3_by_period_n'] = {p: d[d.year.between(a,b)].cat.value_counts().to_dict() for p,a,b in P}
ab = d.abstract.fillna('').str.len() > 50
O['A3_by_period_pct_abstract_only'] = {p: (d[ab & d.year.between(a,b)].cat.value_counts(normalize=True)*100).round(1).to_dict() for p,a,b in P}
# A8 francophone integer counts per subregion
SUB = {"CCG": ["Saudi Arabia","UAE","Qatar","Kuwait","Bahrain","Oman","GCC"],
       "Maghreb": ["Algeria","Morocco","Tunisia","Libya","Mauritania","North Africa/Maghreb"],
       "Machrek": ["Egypt","Jordan","Lebanon","Iraq","Syria","Palestine","Yemen"],
       "Turquie": ["Turkey"], "Iran": ["Iran"], "Regional": ["MENA","Arab","Middle East"]}
fr = d.lang == 'fr'
O['A8_french_total'] = int(fr.sum())
O['A8_french_by_sub'] = {s: int((d[['geo_'+c for c in cs]].any(axis=1) & fr).sum()) for s, cs in SUB.items()}
O['A8_sub_n'] = {s: int(d[['geo_'+c for c in cs]].any(axis=1).sum()) for s, cs in SUB.items()}
O['A8_french_maghreb_def_code'] = int((fr & d[['geo_Algeria','geo_Morocco','geo_Tunisia','geo_North Africa/Maghreb']].any(axis=1)).sum())
O['A8_french_no_sub'] = int((fr & ~d[[ 'geo_'+c for cs in SUB.values() for c in cs]].any(axis=1)).sum())
# figure 3 vs table 2 decomposition
for s, cs in SUB.items():
    cn = [c for c in cs if c not in ('GCC','North Africa/Maghreb','MENA','Arab','Middle East')]
    coll = [c for c in cs if c not in cn]
    only_coll = (d[['geo_'+c for c in coll]].any(axis=1) & ~d[['geo_'+c for c in cn]].any(axis=1)).sum() if coll else 0
    O.setdefault('A8_decomp', {})[s] = dict(sum_country_mentions=int(d[['geo_'+c for c in cn]].sum().sum()), any_country=int(d[['geo_'+c for c in cn]].any(axis=1).sum()), collective_only=int(only_coll), row=O['A8_sub_n'][s])
# A10 Bradford without SSRN
d2 = d[~d.doi.str.startswith('10.2139/ssrn')]
O['A10_ssrn_n'] = int(len(d) - len(d2))
src = d2.groupby(d2.source.fillna('(n.d.)')).size().sort_values(ascending=False); N = len(d2)
cum = src.cumsum(); zone = np.where(cum <= N/3, 1, np.where(cum <= 2*N/3, 2, 3)); zc = pd.Series(zone, index=src.index)
O['A10_bradford'] = {f'zone{z}': dict(sources=int((zc==z).sum()), articles=int(src[zc==z].sum())) for z in (1,2,3)}
O['A10_N'] = N; O['A10_n_sources'] = int(len(src))
O['A10_top10'] = src.head(10).to_dict()
# A13 proportions with abstract denominators
na = int(ab.sum()); O['A13_n_abstract'] = na
for c in ['agency theory','legitimacy theory','institutional theory','stakeholder theory','resource dependence theory','stewardship theory','signalling theory','panel data / regression','survey / questionnaire','case study / interviews','content analysis','climate / carbon','employees / HRM']:
    O.setdefault('A13', {})[c] = dict(n_all=int(k(c).sum()), pct_all=round(k(c).mean()*100,1), n_abs=int(k(c)[ab].sum()), pct_abs=round(k(c)[ab].mean()*100,1), n_title_only=int(k(c)[~ab].sum()), pct_title_only=round(k(c)[~ab].mean()*100,1))
th = ['agency theory','stakeholder theory','legitimacy theory','institutional theory','resource dependence theory','stewardship theory','signalling theory']
O['A13_theory_any_abs'] = round(d.loc[ab, ['k_'+t for t in th]].any(axis=1).mean()*100,1)
O['A13_theory_any_titleonly'] = round(d.loc[~ab, ['k_'+t for t in th]].any(axis=1).mean()*100,1)
O['abstract_share_by_period'] = {p: round(ab[d.year.between(a,b)].mean()*100,1) for p,a,b in P}
json.dump(O, open('../outputs/stats_a.json','w'), indent=1, ensure_ascii=False, default=int)
print(json.dumps(O, indent=1, ensure_ascii=False, default=int))
