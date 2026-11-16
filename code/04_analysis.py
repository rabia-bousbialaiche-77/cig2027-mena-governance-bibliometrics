"""Step 4 - Performance analysis and science mapping.

Inputs : data/clean/corpus_screened.csv, references.csv, affiliations.csv
Outputs: figures/*.png (300 dpi), tables/*.csv, data/clean/results.json
"""
import os, re, json, math, itertools, collections
import numpy as np, pandas as pd, networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from thesaurus import CONCEPTS, FR
from adjustText import adjust_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "data", "clean"); F = os.path.join(ROOT, "figures"); T = os.path.join(ROOT, "tables")
for d in (F, T):
    os.makedirs(d, exist_ok=True)
SEED = 42
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.dpi": 100, "savefig.dpi": 300, "savefig.bbox": "tight"})
PERIODS = [("P1 2000–2012", 2000, 2012), ("P2 2013–2019", 2013, 2019), ("P3 2020–2026", 2020, 2026)]
R = {}

df = pd.read_csv(os.path.join(C, "corpus_screened.csv"))
df["abstract"] = df.abstract.fillna(""); df["source"] = df.source.fillna("(n.d.)")
df["text"] = (df.title + ". " + df.abstract).str.lower()
refs = pd.read_csv(os.path.join(C, "references.csv")).fillna("")
affs = pd.read_csv(os.path.join(C, "affiliations.csv")).fillna("")
N = len(df); R["N"] = N
R["n_with_abstract"] = int((df.abstract.str.len() > 50).sum())
R["n_french"] = int((df.lang == "fr").sum())

# ---------------------------------------------------------------- annual production
yr = df.groupby("year").size().reindex(range(2000, 2027), fill_value=0)
yr.to_csv(os.path.join(T, "annual_production.csv"), header=["n"])
cagr = (yr[2025] / yr[2000]) ** (1 / 25) - 1 if yr[2000] else float("nan")
R["annual"] = yr.to_dict(); R["cagr_2000_2025"] = cagr
R["share_2020_2026"] = float(yr.loc[2020:2026].sum() / N)
R["periods_n"] = {p: int(yr.loc[a:b].sum()) for p, a, b in PERIODS}
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.bar(yr.index, yr.values, color=PAL[0], width=0.8)
for x in (2012.5, 2019.5):
    ax.axvline(x, color=MUTED, lw=0.8, ls="--")
ax.set_xlabel("Année de publication"); ax.set_ylabel("Nombre d'articles")
ax.text(2026, yr[2026], "2026*", ha="center", va="bottom", fontsize=7, color=INK2)
ax.set_title("Production annuelle (N = %d) — *année incomplète (extraction au 15/11/2026)" % N, fontsize=9, loc="left", color=INK)
fig.savefig(os.path.join(F, "fig2_production_annuelle.png")); plt.close(fig)

# ---------------------------------------------------------------- study-context countries
gcols = [c for c in df.columns if c.startswith("geo_")]
geo = df[gcols].sum().sort_values(ascending=False); geo.index = [g[4:] for g in geo.index]
geo.to_csv(os.path.join(T, "study_context_countries.csv"), header=["n"])
R["geo"] = geo.to_dict()
geo_p = {}
for p, a, b in PERIODS:
    s = df[df.year.between(a, b)]
    geo_p[p] = (s[gcols].sum() / len(s) * 100).round(1)
gp = pd.DataFrame(geo_p); gp.index = [g[4:] for g in gp.index]
gp.to_csv(os.path.join(T, "study_context_by_period_pct.csv"))
cty = [g for g in geo.index if g not in ("MENA", "GCC", "Arab", "Middle East", "North Africa/Maghreb")]
fig, ax = plt.subplots(figsize=(6.5, 4.2))
g2 = geo[cty].sort_values()
maghreb = {"Algeria", "Morocco", "Tunisia", "Libya", "Mauritania"}
gcc = {"Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman"}
cols = [PAL[1] if c in maghreb else PAL[0] if c in gcc else PAL[2] if c in ("Iran", "Turkey") else PAL[6] for c in g2.index]
ax.barh(g2.index, g2.values, color=cols, height=0.7)
for i, v in enumerate(g2.values):
    ax.text(v + 3, i, str(int(v)), va="center", fontsize=7, color=INK2)
ax.set_xlabel("Nombre d'articles mentionnant le pays (titre/résumé)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=PAL[0], label="CCG"), Patch(color=PAL[1], label="Maghreb"),
                   Patch(color=PAL[6], label="Machrek / Égypte / Yémen"), Patch(color=PAL[2], label="Iran, Turquie")],
          frameon=False, fontsize=7, loc="lower right")
ax.grid(axis="y", visible=False)
fig.savefig(os.path.join(F, "fig3_pays_contexte.png")); plt.close(fig)

# ---------------------------------------------------------------- affiliations (author countries)
dc = affs[affs.country != ""].groupby("doi").country.apply(lambda s: sorted(set(s)))
R["n_docs_with_aff_country"] = int(len(dc)); R["pct_docs_with_aff_country"] = len(dc) / N
cc = collections.Counter(c for l in dc for c in l)
pd.Series(cc).sort_values(ascending=False).to_csv(os.path.join(T, "author_countries.csv"), header=["n_docs"])
R["author_countries_top"] = dict(cc.most_common(15))
R["intl_collab_share"] = float(np.mean([len(l) > 1 for l in dc])) if len(dc) else None
G_c = nx.Graph()
for l in dc:
    for a, b in itertools.combinations(l, 2):
        w = G_c.get_edge_data(a, b, {"weight": 0})["weight"]; G_c.add_edge(a, b, weight=w + 1)
pd.DataFrame([(a, b, d["weight"]) for a, b, d in G_c.edges(data=True)], columns=["a", "b", "w"]) \
  .sort_values("w", ascending=False).to_csv(os.path.join(T, "country_collaboration_edges.csv"), index=False)
R["collab_top_pairs"] = [(a, b, d["weight"]) for a, b, d in sorted(G_c.edges(data=True), key=lambda e: -e[2]["weight"])[:12]]
if G_c.number_of_nodes():
    top = [c for c, _ in cc.most_common(25) if c in G_c]
    H = G_c.subgraph(top).copy(); H.remove_edges_from([(u, v) for u, v, d in list(H.edges(data=True)) if d["weight"] < 2])
    fig, ax = plt.subplots(figsize=(7, 5.5))
    pos = nx.spring_layout(H, seed=SEED, weight="weight", k=0.9)
    ws = [H[u][v]["weight"] for u, v in H.edges()]
    nx.draw_networkx_edges(H, pos, ax=ax, width=[0.4 + 2.5 * w / max(ws) for w in ws], edge_color="#c3c2b7")
    sizes = [40 + 6 * cc[n] for n in H.nodes()]
    ncol = [PAL[1] if n in ("Algeria", "Morocco", "Tunisia", "Libya", "Mauritania") else
            PAL[0] if n in ("Saudi Arabia", "United Arab Emirates", "Qatar", "Kuwait", "Bahrain", "Oman") else
            PAL[2] if n in ("Iran, Islamic Republic of", "Türkiye") else
            PAL[6] if n in ("Egypt", "Jordan", "Lebanon", "Iraq", "Syrian Arab Republic", "Palestine, State of", "Yemen") else "#c3c2b7"
            for n in H.nodes()]
    nx.draw_networkx_nodes(H, pos, ax=ax, node_size=sizes, node_color=ncol, edgecolors="white", linewidths=1)
    lab = {n: n.replace("Iran, Islamic Republic of", "Iran").replace("Palestine, State of", "Palestine")
              .replace("United Arab Emirates", "UAE").replace("United Kingdom", "UK").replace("United States", "USA")
              .replace("Syrian Arab Republic", "Syria") for n in H.nodes()}
    nx.draw_networkx_labels(H, pos, labels=lab, font_size=7, ax=ax, font_color=INK)
    ax.axis("off")
    fig.savefig(os.path.join(F, "fig7_collaboration_pays.png")); plt.close(fig)

# ---------------------------------------------------------------- sources, Bradford
src = df.groupby("source").size().sort_values(ascending=False)
src.to_csv(os.path.join(T, "sources.csv"), header=["n"])
R["n_sources"] = int(len(src))
cum = src.cumsum(); third = N / 3
zone = np.where(cum <= third, 1, np.where(cum <= 2 * third, 2, 3))
# assign the source straddling the boundary to the lower zone
zc = pd.Series(zone, index=src.index)
R["bradford"] = {f"zone{z}": {"sources": int((zc == z).sum()), "articles": int(src[zc == z].sum())} for z in (1, 2, 3)}
srccit = df.groupby("source").cited_by.sum()
top_src = pd.DataFrame({"n": src.head(15), "citations": srccit.reindex(src.head(15).index)})
top_src.to_csv(os.path.join(T, "top_sources.csv")); R["top_sources"] = top_src.reset_index().values.tolist()

# ---------------------------------------------------------------- Lotka
def akey(a):
    a = a.strip()
    if "," not in a:
        return a.lower()
    fam, giv = a.split(",", 1)
    return (fam.strip() + " " + (giv.strip()[:1] if giv.strip() else "")).lower()
au = collections.Counter(akey(a) for s in df.authors.fillna("") for a in s.split(";") if a.strip())
R["n_authors_distinct"] = len(au)
dist = collections.Counter(au.values())
lot = pd.DataFrame(sorted(dist.items()), columns=["n_articles", "n_authors"])
lot["pct"] = lot.n_authors / lot.n_authors.sum() * 100
lot.to_csv(os.path.join(T, "lotka.csv"), index=False)
x = np.log(lot.n_articles); y = np.log(lot.n_authors)
mask = lot.n_articles <= 10
beta = np.polyfit(x[mask], y[mask], 1)
R["lotka_exponent"] = float(-beta[0]); R["lotka_single_pct"] = float(lot.pct.iloc[0])
R["top_authors"] = au.most_common(12)
R["mean_authors_per_doc"] = float(df.n_authors.mean())
R["single_author_share"] = float((df.n_authors == 1).mean())

# ---------------------------------------------------------------- citations
cit = df.cited_by.fillna(0).astype(int)
R["citations_total"] = int(cit.sum()); R["citations_mean"] = float(cit.mean()); R["citations_median"] = float(cit.median())
R["uncited_share"] = float((cit == 0).mean())
s = sorted(cit, reverse=True); R["h_index"] = int(sum(1 for i, c in enumerate(s) if c >= i + 1))
R["top10pct_share_citations"] = float(sum(s[: N // 10]) / max(1, sum(s)))
topc = df.sort_values("cited_by", ascending=False).head(20)[["doi", "authors", "year", "title", "source", "cited_by"]]
topc.to_csv(os.path.join(T, "top_cited.csv"), index=False)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
axs[0].plot(lot.n_articles[mask], lot.n_authors[mask], "o", color=PAL[0], ms=5, label="Observé")
xx = np.arange(1, 11); axs[0].plot(xx, np.exp(beta[1]) * xx ** beta[0], color=PAL[1], lw=2, label=f"Ajustement n = {-beta[0]:.2f}")
axs[0].plot(xx, lot.n_authors.iloc[0] / xx ** 2, color=MUTED, lw=1.5, ls="--", label="Lotka (n = 2)")
axs[0].set_xscale("log"); axs[0].set_yscale("log"); axs[0].set_xlabel("Articles par auteur"); axs[0].set_ylabel("Nombre d'auteurs")
axs[0].legend(frameon=False, fontsize=7); axs[0].set_title("(a) Loi de Lotka", loc="left", fontsize=9)
rank = np.arange(1, len(src) + 1)
axs[1].plot(np.log(rank), src.cumsum().values, color=PAL[0], lw=2)
for z in (1, 2):
    k = int((zc <= z).sum()); axs[1].axvline(np.log(k), color=MUTED, ls="--", lw=0.8)
axs[1].set_xlabel("ln(rang de la revue)"); axs[1].set_ylabel("Articles cumulés")
axs[1].set_title("(b) Courbe de Bradford", loc="left", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(F, "fig4_lotka_bradford.png")); plt.close(fig)

# ---------------------------------------------------------------- concepts
for k, p in CONCEPTS.items():
    df["k_" + k] = df.text.str.contains(p, regex=True)
kcols = [c for c in df.columns if c.startswith("k_")]
kf = df[kcols].sum().sort_values(ascending=False); kf.index = [k[2:] for k in kf.index]
kf.to_csv(os.path.join(T, "concept_frequencies.csv"), header=["n"]); R["concepts"] = kf.to_dict()
kp = {}
for p, a, b in PERIODS:
    s2 = df[df.year.between(a, b)]; kp[p] = (s2[kcols].mean() * 100).round(1)
kpd = pd.DataFrame(kp); kpd.index = [k[2:] for k in kpd.index]; kpd.to_csv(os.path.join(T, "concepts_by_period_pct.csv"))
R["concepts_by_period"] = kpd.to_dict()
METHODS = {"panel data / regression", "content analysis", "survey / questionnaire", "case study / interviews", "literature review / bibliometric"}
GENERIC = {"corporate governance", "board of directors", "panel data / regression", "listed firms", "emerging markets"}


def cooc_graph(sub, min_occ=5):
    M = sub[kcols].astype(int)
    occ = M.sum(); keep = [c for c in kcols if occ[c] >= min_occ]
    M = M[keep]; X = M.T.dot(M)
    G = nx.Graph()
    for c in keep:
        G.add_node(c[2:], occ=int(occ[c]))
    for a, b in itertools.combinations(keep, 2):
        if X.loc[a, b] > 0:
            e = X.loc[a, b] ** 2 / (occ[a] * occ[b])   # equivalence index (Callon; Cobo et al., 2011)
            G.add_edge(a[2:], b[2:], weight=float(X.loc[a, b]), eq=float(e))
    return G


def louvain(G, w="eq", res=1.0):
    comms = nx.community.louvain_communities(G, weight=w, resolution=res, seed=SEED)
    return sorted([sorted(c, key=lambda n: -G.nodes[n]["occ"]) for c in comms], key=lambda c: -sum(G.nodes[n]["occ"] for n in c))


Gall = cooc_graph(df, 10)
comms = louvain(Gall)
R["cooc_nodes"] = Gall.number_of_nodes(); R["cooc_edges"] = Gall.number_of_edges()
R["cooc_clusters"] = [c for c in comms]
R["cooc_modularity"] = nx.community.modularity(Gall, comms, weight="eq")
pd.DataFrame([(i + 1, n, Gall.nodes[n]["occ"]) for i, c in enumerate(comms) for n in c],
             columns=["cluster", "concept", "occurrences"]).to_csv(os.path.join(T, "cooc_clusters.csv"), index=False)
fig, ax = plt.subplots(figsize=(8.5, 7))
H = Gall.copy(); H.remove_nodes_from([n for n in GENERIC if n in H])
keep = set()
for n in H.nodes():
    es = sorted(H.edges(n, data=True), key=lambda e: -e[2]["eq"])[:4]
    keep |= {tuple(sorted((u, v))) for u, v, _ in es}
H.remove_edges_from([(u, v) for u, v in list(H.edges()) if tuple(sorted((u, v))) not in keep])
pos = nx.kamada_kawai_layout(H, weight=None)
pos = nx.spring_layout(H, pos=pos, seed=SEED, weight="eq", k=0.35, iterations=60)
cmap = {n: PAL[i % 8] for i, c in enumerate(comms) for n in c}
ews = [H[u][v]["eq"] for u, v in H.edges()]
nx.draw_networkx_edges(H, pos, ax=ax, width=[0.3 + 2.5 * e / max(ews) for e in ews], edge_color="#d6d5cd", alpha=0.9)
nx.draw_networkx_nodes(H, pos, ax=ax, node_size=[20 + 0.6 * H.nodes[n]["occ"] for n in H.nodes()],
                       node_color=[cmap[n] for n in H.nodes()], edgecolors="white", linewidths=0.8)
texts = [ax.text(pos[n][0], pos[n][1], FR.get(n, n), fontsize=6.5, color=INK) for n in H.nodes()]
adjust_text(texts, ax=ax, expand=(1.15, 1.3), arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.4))
CLN = ["mécanismes, propriété et performance", "RSE, durabilité et divulgation", "conseil d'administration et diversité", "banques islamiques et risque", "autre", "autre"]
ax.legend(handles=[Patch(color=PAL[i % 8], label=f"Cluster {i+1} : {CLN[i]}") for i in range(len(comms))], frameon=False, fontsize=7, loc="upper left")
ax.axis("off")
fig.savefig(os.path.join(F, "fig5_reseau_cooccurrences.png")); plt.close(fig)

# ---------------------------------------------------------------- strategic maps per period (Cobo et al., 2011)
smaps = {}
fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.8))
for (p, a, b), ax in zip(PERIODS, axs):
    sub = df[df.year.between(a, b)]
    G = cooc_graph(sub, max(3, int(len(sub) * 0.01)))
    for n in list(G.nodes()):
        if n in GENERIC:
            G.remove_node(n)
    cs = louvain(G, res=1.4)
    rows = []
    for c in cs:
        if len(c) < 2:
            continue
        cs_ = set(c)
        internal = [d["eq"] for u, v, d in G.edges(data=True) if u in cs_ and v in cs_]
        external = [d["eq"] for u, v, d in G.edges(data=True) if (u in cs_) ^ (v in cs_)]
        cen = 10 * sum(external); den = 100 * sum(internal) / len(c)
        occ = sum(G.nodes[n]["occ"] for n in c)
        rows.append(dict(period=p, label=" / ".join(FR.get(x, x) for x in [m for m in c if m not in METHODS][:2]), members="; ".join(c), centrality=cen, density=den, occ=occ, size=len(c)))
    sm = pd.DataFrame(rows); smaps[p] = sm
    mc, md = sm.centrality.median(), sm.density.median()
    ax.axvline(mc, color=MUTED, lw=0.8); ax.axhline(md, color=MUTED, lw=0.8)
    ax.scatter(sm.centrality, sm.density, s=20 + sm.occ / sm.occ.max() * 600, color=PAL[0], alpha=0.55, edgecolors="white")
    tx = [ax.text(r.centrality, r.density, r.label.replace(" / ", "\n"), fontsize=5.6, ha="center", va="center", color=INK) for _, r in sm.iterrows()]
    adjust_text(tx, ax=ax, expand=(1.1, 1.2))
    ax.set_title(p, fontsize=9, loc="left"); ax.set_xlabel("Centralité (Callon)")
    if ax is axs[0]:
        ax.set_ylabel("Densité (Callon)")
    xr = ax.get_xlim(); yr_ = ax.get_ylim()
    for txt, xx, yy, ha, va in (("Moteurs", xr[1], yr_[1], "right", "top"), ("Spécialisés", xr[0], yr_[1], "left", "top"),
                                ("Émergents/déclinants", xr[0], yr_[0], "left", "bottom"), ("Transversaux", xr[1], yr_[0], "right", "bottom")):
        ax.text(xx, yy, txt, fontsize=6.5, color=MUTED, ha=ha, va=va, style="italic")
fig.tight_layout(); fig.savefig(os.path.join(F, "fig6_cartes_strategiques.png")); plt.close(fig)
allsm = pd.concat(smaps.values()); allsm.to_csv(os.path.join(T, "strategic_maps.csv"), index=False)
for p, sm in smaps.items():
    mc, md = sm.centrality.median(), sm.density.median()
    sm["quadrant"] = np.where((sm.centrality >= mc) & (sm.density >= md), "moteur",
                     np.where(sm.centrality >= mc, "transversal", np.where(sm.density >= md, "spécialisé", "émergent/déclinant")))
allsm = pd.concat(smaps.values()); allsm.to_csv(os.path.join(T, "strategic_maps.csv"), index=False)
R["strategic_maps"] = allsm.to_dict(orient="records")
# thematic evolution (inclusion index between clusters of consecutive periods)
evo = []
ps = [p for p, _, _ in PERIODS]
for p1, p2 in zip(ps, ps[1:]):
    for _, r1 in smaps[p1].iterrows():
        for _, r2 in smaps[p2].iterrows():
            A, B = set(r1.members.split("; ")), set(r2.members.split("; "))
            inter = len(A & B)
            if inter:
                evo.append(dict(src=p1, a=r1.label, dst=p2, b=r2.label, shared=inter, inclusion=inter / min(len(A), len(B))))
pd.DataFrame(evo).to_csv(os.path.join(T, "thematic_evolution.csv"), index=False)
# evolution figure
fig, ax = plt.subplots(figsize=(10, 5.6))
ypos = {}; XS = [0, 4.2, 8.4]; W = 1.9
for i, p in enumerate(ps):
    sm = smaps[p].sort_values("occ", ascending=False).reset_index(drop=True)
    hs = np.maximum(sm.occ / sm.occ.sum(), 0.085); hs = hs / hs.sum(); y = 0
    for (_, r), h in zip(sm.iterrows(), hs):
        ax.add_patch(plt.Rectangle((XS[i], y), W, h * 0.94, color=PAL[0], alpha=0.25 + 0.55 * (r.quadrant == "moteur"), lw=0))
        ax.text(XS[i] + W / 2, y + h * 0.47, r.label.replace(" / ", "\n", 1) + f"\n({r.quadrant})", fontsize=5.6, ha="center", va="center", color=INK)
        ypos[(p, r.label)] = y + h * 0.47; y += h
for e in evo:
    if e["inclusion"] >= 0.3:
        y1, y2 = ypos[(e["src"], e["a"])], ypos[(e["dst"], e["b"])]
        x1 = XS[ps.index(e["src"])] + W; x2 = XS[ps.index(e["dst"])]
        t = np.linspace(0, 1, 30); yy = y1 + (y2 - y1) * (3 * t ** 2 - 2 * t ** 3)
        ax.plot(x1 + (x2 - x1) * t, yy, color=PAL[1], lw=0.5 + 3 * e["inclusion"], alpha=0.5)
for i, p in enumerate(ps):
    ax.text(XS[i] + W / 2, 1.02, p, ha="center", fontsize=8, color=INK, weight="bold")
ax.set_xlim(-0.2, XS[-1] + W + 0.2); ax.set_ylim(0, 1.06); ax.axis("off")
fig.savefig(os.path.join(F, "fig8_evolution_thematique.png")); plt.close(fig)

# ---------------------------------------------------------------- references: coverage, co-citation, coupling
refs_d = refs[refs.cited_doi != ""]
R["n_refs_total"] = int(len(refs)); R["n_refs_with_doi"] = int(len(refs_d))
R["n_docs_with_refs"] = int(refs.citing_doi.nunique())
R["pct_docs_with_refs"] = refs.citing_doi.nunique() / N
cited_counts = refs_d.groupby("cited_doi").citing_doi.nunique().sort_values(ascending=False)
cited_counts.head(200).to_csv(os.path.join(T, "most_cited_references_doi.csv"), header=["n_citing"])
# co-citation network on references cited >= threshold
thr = max(15, int(cited_counts.iloc[min(80, len(cited_counts) - 1)]))
core = sorted(cited_counts[cited_counts >= thr].index)
R["cocit_threshold"] = thr; R["cocit_nodes"] = len(core)
bydoc = refs_d[refs_d.cited_doi.isin(set(core))].groupby("citing_doi").cited_doi.apply(lambda s: sorted(set(s)))
Gcc = nx.Graph()
for d in core:
    Gcc.add_node(d, occ=int(cited_counts[d]))
for l in bydoc:
    for a, b in itertools.combinations(l, 2):
        w = Gcc.get_edge_data(a, b, {"weight": 0})["weight"]; Gcc.add_edge(a, b, weight=w + 1)
for u, v, d in Gcc.edges(data=True):
    d["eq"] = d["weight"] ** 2 / (Gcc.nodes[u]["occ"] * Gcc.nodes[v]["occ"])
cc_comms = louvain(Gcc, w="weight")
R["cocit_clusters"] = cc_comms
R["cocit_modularity"] = nx.community.modularity(Gcc, cc_comms, weight="weight")
pd.DataFrame([(i + 1, n, Gcc.nodes[n]["occ"]) for i, c in enumerate(cc_comms) for n in c],
             columns=["cluster", "cited_doi", "n_citing"]).to_csv(os.path.join(T, "cocitation_clusters.csv"), index=False)
json.dump({"pos_seed": SEED}, open(os.path.join(C, "_cocit_meta.json"), "w"))
nx.write_gexf(Gcc, os.path.join(T, "cocitation.gexf"))

# bibliographic coupling among corpus documents with >= 10 DOI references, top 400 most cited
dref = refs_d.groupby("citing_doi").cited_doi.apply(set)
eligible = df[df.doi.isin(dref.index)].copy()
eligible["nref"] = eligible.doi.map(lambda d: len(dref[d]))
eligible = eligible[eligible.nref >= 10].sort_values("cited_by", ascending=False).head(400)
Gbc = nx.Graph()
for d in eligible.doi:
    Gbc.add_node(d, occ=1)
for a, b in itertools.combinations(eligible.doi, 2):
    sh = len(dref[a] & dref[b])
    if sh >= 3:
        Gbc.add_edge(a, b, weight=sh / math.sqrt(len(dref[a]) * len(dref[b])))   # Salton cosine
Gbc.remove_nodes_from([n for n in list(Gbc.nodes()) if Gbc.degree(n) == 0])
bc_comms = sorted(nx.community.louvain_communities(Gbc, weight="weight", seed=SEED, resolution=1.0), key=len, reverse=True)
R["bc_nodes"] = Gbc.number_of_nodes(); R["bc_edges"] = Gbc.number_of_edges()
R["bc_modularity"] = nx.community.modularity(Gbc, bc_comms, weight="weight")
rows = []
for i, c in enumerate(bc_comms):
    sub = df[df.doi.isin(c)]
    lift = (sub[kcols].mean() + 1e-9) / (df[kcols].mean() + 1e-9)
    freq = sub[kcols].mean()
    score = (lift * (freq >= 0.15)).sort_values(ascending=False)
    labs = [k[2:] for k in score.index[:5]]
    tops = sub.sort_values("cited_by", ascending=False).head(5)
    rows.append(dict(cluster=i + 1, n_docs=len(c), mean_year=round(sub.year.mean(), 1), mean_cites=round(sub.cited_by.mean(), 1),
                     distinctive_concepts="; ".join(labs), top_docs=" | ".join(tops.doi)))
bct = pd.DataFrame(rows); bct.to_csv(os.path.join(T, "coupling_clusters.csv"), index=False)
R["bc_clusters"] = rows
fig, ax = plt.subplots(figsize=(7.5, 6))
pos = nx.spring_layout(Gbc, seed=SEED, weight="weight", k=0.12, iterations=150)
cm = {n: PAL[i % 8] if i < 8 else "#c3c2b7" for i, c in enumerate(bc_comms) for n in c}
nx.draw_networkx_edges(Gbc, pos, ax=ax, width=0.2, edge_color="#e1e0d9", alpha=0.5)
cit_map = df.set_index("doi").cited_by
nx.draw_networkx_nodes(Gbc, pos, ax=ax, node_size=[8 + 0.25 * cit_map.get(n, 0) for n in Gbc.nodes()],
                       node_color=[cm[n] for n in Gbc.nodes()], edgecolors="white", linewidths=0.4)
ax.legend(handles=[Patch(color=PAL[i], label=f"C{i+1} ({r['n_docs']}) : " + "; ".join(FR.get(x, x) for x in r["distinctive_concepts"].split("; ")[:2]))
                   for i, r in enumerate(rows[:8])], frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 0.02), ncol=2)
ax.axis("off")
fig.savefig(os.path.join(F, "fig9_couplage_bibliographique.png")); plt.close(fig)

df.drop(columns=["text"]).to_csv(os.path.join(C, "corpus_coded.csv"), index=False)
json.dump(R, open(os.path.join(C, "results.json"), "w"), indent=1, ensure_ascii=False, default=str)
print(json.dumps({k: v for k, v in R.items() if k not in ("annual", "concepts", "concepts_by_period", "strategic_maps", "cooc_clusters", "cocit_clusters", "bc_clusters")}, indent=1, default=str, ensure_ascii=False))
