import pandas as pd, numpy as np, json, concurrent.futures as cf
from fetch_lib import fetch_many, clean
c = pd.read_csv('../../data/raw/candidates_identification.csv.gz', low_memory=False)
scr = c[c.r1_year & c.has_title & c.r2_lang]
print('screened', len(scr), 'r3 excl', (~scr.r3_geo).sum(), 'r4 excl', (scr.r3_geo & ~scr.r4_topic).sum(), 'kept', (scr.r3_geo & scr.r4_topic).sum())
rng = np.random.default_rng(2026)
S = scr.sample(2000, random_state=2026)
ex3 = scr[~scr.r3_geo].sample(50, random_state=7); ex4 = scr[scr.r3_geo & ~scr.r4_topic].sample(50, random_state=7)
alld = list(S.doi) + list(ex3.doi) + list(ex4.doi)
chunks = [alld[i:i+200] for i in range(0, len(alld), 200)]
res = {}
with cf.ThreadPoolExecutor(3) as ex:
    for r in ex.map(fetch_many, chunks): res.update(r)
print('fetched', len(res), 'of', len(set(alld)))
def ab(d): return clean(res.get(d, {}).get('abstract'))
S = S.assign(abstract=S.doi.map(ab), found=S.doi.isin(res.keys()))
S.to_csv('a1_sample.csv', index=False)
for name, e in (('R3', ex3), ('R4', ex4)):
    e = e.assign(abstract=e.doi.map(ab), stratum=name); e[['doi','year','title','source','abstract','stratum','r3_geo','r4_topic','r4_weak']].to_csv(f'a2_{name}.csv', index=False)
f = S[S.found]; s = (f.abstract.str.len() > 50).mean()
print('found', len(f), 'share with abstract', round(s,4))
for g, sub in f.groupby(np.where(f.r3_geo & f.r4_topic, 'kept', 'excluded')): print(g, len(sub), (sub.abstract.str.len()>50).mean())
