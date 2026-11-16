"""Analyse de sensibilité (révision) : corpus sans les articles portant uniquement sur la Turquie ou l'Iran
et sans trois études multirégionales (Baughn et al., 2007 ; Birindelli et al., 2019 ; Eccles et al., 2017).
Usage : copier le dossier de réplication dans un dossier séparé, exécuter ce script depuis code/ (après
00_restore_abstracts.py), puis 04_analysis.py et 06_extra_stats.py dans ce dossier copié."""
import os, pandas as pd
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "clean", "corpus_screened.csv")
d = pd.read_csv(p, low_memory=False)
geo = [c for c in d.columns if c.startswith("geo_")]
arab = [c for c in geo if c not in ("geo_Turkey", "geo_Iran")]
only_ti = ~d[arab].any(axis=1)
multi = d.doi.str.lower().isin(["10.1002/csr.160", "10.1002/csr.1762", "10.1111/jacf.12267"])
d[~only_ti & ~multi].to_csv(p, index=False)
print("retirés (Turquie/Iran seuls) :", int(only_ti.sum()), "; multirégionaux :", int((multi & ~only_ti).sum()), "; N =", int((~only_ti & ~multi).sum()))
