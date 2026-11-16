import pandas as pd
from fetch_lib import fetch_many, clean
c = pd.read_csv('../../data/raw/candidates_identification.csv.gz', low_memory=False)
scr = c[c.r1_year & c.has_title & c.r2_lang]
a = scr[~scr.r3_geo & scr.r4_topic]; b = scr[scr.r3_geo & ~scr.r4_topic & scr.r4_weak]
print('R3-excl on-topic', len(a), '| R4-excl with weak governance signal', len(b))
sa = a.sample(50, random_state=11); sb = b.sample(50, random_state=11)
res = fetch_many(list(sa.doi)+list(sb.doi), 40)
for n, s in (('A', sa), ('B', sb)):
    s = s.assign(abstract=s.doi.map(lambda d: clean(res.get(d, {}).get('abstract'))))
    s.to_csv(f'a2_hr_{n}.csv', index=False)
    print('=====', n, s.abstract.str.len().gt(50).sum())
    for i, r in enumerate(s.itertuples()): print(f'{n}{i:02d} | {str(r.title)[:140]} || {str(r.abstract)[:230]}')
