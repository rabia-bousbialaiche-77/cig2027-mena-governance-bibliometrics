import pandas as pd, numpy as np, networkx as nx, itertools, math, json
d = pd.read_csv('../../data/clean/corpus_coded.csv', low_memory=False)
refs = pd.read_csv('../../data/clean/references.csv').fillna('')
rd = refs[refs.cited_doi != '']; dref = rd.groupby('citing_doi').cited_doi.apply(set)
kcols = [c for c in d.columns if c.startswith('k_')]
def run(sample, name):
    G = nx.Graph(); G.add_nodes_from(sample.doi)
    for a, b in itertools.combinations(sample.doi, 2):
        sh = len(dref[a] & dref[b])
        if sh >= 3: G.add_edge(a, b, weight=sh / math.sqrt(len(dref[a]) * len(dref[b])))
    G.remove_nodes_from([n for n in list(G) if G.degree(n) == 0])
    cs = sorted(nx.community.louvain_communities(G, weight='weight', seed=42), key=len, reverse=True)
    rows = []
    for i, c in enumerate(cs):
        sub = d[d.doi.isin(c)]
        lift = (sub[kcols].mean() + 1e-9) / (d[kcols].mean() + 1e-9); freq = sub[kcols].mean()
        labs = [k[2:] for k in (lift * (freq >= 0.15)).sort_values(ascending=False).index[:4]]
        rows.append(dict(cluster=i+1, n=len(c), mean_year=round(sub.year.mean(),1), concepts='; '.join(labs)))
    return dict(name=name, nodes=G.number_of_nodes(), edges=G.number_of_edges(), modularity=round(nx.community.modularity(G, cs, weight='weight'),3), clusters=[r for r in rows if r['n'] >= 10], n_small=sum(r['n'] < 10 for r in rows))
el = d[d.doi.isin(dref.index)].copy(); el['nref'] = el.doi.map(lambda x: len(dref[x])); el = el[el.nref >= 10]
el['cpy'] = el.cited_by / (2027 - el.year).clip(lower=1)
out = [run(el[el.year >= 2020].sort_values('cited_by', ascending=False).head(400), 'cohorte 2020-2026, 400 plus cités'),
       run(el.sort_values('cpy', ascending=False).head(400), 'corpus entier, 400 premiers en citations par an')]
s2 = el.sort_values('cpy', ascending=False).head(400)
out[1]['share_2020_plus'] = round((s2.year >= 2020).mean()*100,1)
out.append(dict(name='baseline share 2020+ in top400 cited', v=round((el.sort_values('cited_by',ascending=False).head(400).year>=2020).mean()*100,1)))
json.dump(out, open('../outputs/a5.json','w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
