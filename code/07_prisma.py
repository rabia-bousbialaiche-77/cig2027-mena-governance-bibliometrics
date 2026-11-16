"""Step 7 - PRISMA 2020 flow diagram and retrieval-saturation curve."""
import os, json, glob, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "data", "clean"); F = os.path.join(ROOT, "figures"); T = os.path.join(ROOT, "tables")
P = json.load(open(os.path.join(C, "prisma_counts.json")))
L = json.load(open(os.path.join(ROOT, "data", "raw", "retrieval_log.json")))
val = pd.read_csv(os.path.join(C, "validation_sample.csv"))
f = lambda n: f"{n:,}".replace(",", " ")
fig, ax = plt.subplots(figsize=(7.2, 7.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 12)
def box(x, y, w, h, t, fc="#eef4fc"):
    ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec="#2a78d6", lw=0.9))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=7.3, wrap=True)
def arr(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#52514e", lw=0.8))
for y, lab in ((10.4, "Identification"), (6.6, "Sélection"), (1.6, "Inclusion")):
    ax.text(0.15, y, lab, rotation=90, fontsize=8, weight="bold", color="#52514e", va="center")
box(0.7, 10.0, 4.6, 1.7, f"Enregistrements identifiés via l'API Crossref\n({L['n_queries'] // 6} requêtes × 6 pages de 1 000 = {f(L['n_queries'])} appels)\nn = {f(P['records_identified'])}")
box(5.9, 10.0, 3.9, 1.7, f"Doublons retirés (DOI identiques)\nn = {f(P['duplicates_removed'])}", "#fdf1ec")
box(0.7, 7.7, 4.6, 1.5, f"Enregistrements uniques (2000–2026)\nn = {f(P['unique_records'])}")
box(5.9, 7.7, 3.9, 1.5, f"Exclus : titre absent n = {f(P['excluded_no_title'])}\nlangue ≠ anglais/français n = {f(P['excluded_language'])}", "#fdf1ec")
box(0.7, 5.3, 4.6, 1.6, f"Titres et résumés examinés\n(règles R3–R4, annexe A)\nn = {f(P['screened_title_abstract'])}")
box(5.9, 5.3, 3.9, 1.6, f"Exclus : aucun marqueur MENA n = {f(P['excluded_no_mena_marker'])}\nhors sujet (gouvernance/RSE-ESG)\nn = {f(P['excluded_off_topic'])}", "#fdf1ec")
box(0.7, 2.9, 4.6, 1.6, f"Contrôle manuel d'un échantillon aléatoire\n(n = {len(val)}) : précision = {val.relevant.mean():.0%}\nEnrichissement (références, affiliations)")
box(0.7, 0.4, 4.6, 1.7, f"Corpus final analysé\nn = {f(P['retained_after_screening'])} articles\n(dont {f(P['with_abstract'])} avec résumé)", "#e6f6ef")
for y1, y2 in ((10.0, 9.2), (7.7, 6.9), (5.3, 4.5), (2.9, 2.1)):
    arr(3.0, y1, 3.0, y2)
for y in (10.85, 8.45, 6.1):
    arr(5.3, y, 5.9, y)
fig.savefig(os.path.join(F, "fig1_prisma.png"), dpi=300, bbox_inches="tight"); plt.close(fig)
# saturation: new retained records contributed by each result page
ret = set(pd.read_csv(os.path.join(C, "corpus_screened.csv")).doi); first = {}
for fn in glob.glob(os.path.join(ROOT, "data", "raw", "crossref_search", "*.jsonl")):
    for l in open(fn):
        it = json.loads(l); d = it["DOI"].lower()
        if d in ret:
            first[d] = min(first.get(d, 9e9), it.get("_offset", 0))
sat = pd.Series(first).value_counts().sort_index(); sat.index = [f"{i+1}–{i+1000}" for i in sat.index]
sat.to_csv(os.path.join(T, "saturation.csv"), header=["new_retained"]); print(sat)
