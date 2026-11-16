"""Step 6 - Additional descriptive statistics quoted in the paper (sub-regions, growth, coverage)."""
import os, json, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(ROOT, "data", "clean"); T = os.path.join(ROOT, "tables")
d = pd.read_csv(os.path.join(C, "corpus_coded.csv"))
X = {}
yr = d.groupby("year").size()
X["cagr_2010_2025"] = (yr[2025] / yr[2010]) ** (1 / 15) - 1
X["cagr_2013_2019"] = (yr[2019] / yr[2013]) ** (1 / 6) - 1
X["cagr_2020_2025"] = (yr[2025] / yr[2020]) ** (1 / 5) - 1
SUB = {"GCC": ["Saudi Arabia", "UAE", "Qatar", "Kuwait", "Bahrain", "Oman", "GCC"],
       "Maghreb": ["Algeria", "Morocco", "Tunisia", "Libya", "Mauritania", "North Africa/Maghreb"],
       "Machrek+Egypte+Yemen": ["Egypt", "Jordan", "Lebanon", "Iraq", "Syria", "Palestine", "Yemen"],
       "Iran": ["Iran"], "Turquie": ["Turkey"], "Regional (MENA/Arab/Middle East)": ["MENA", "Arab", "Middle East"]}
rows = []
for s, cs in SUB.items():
    m = d[["geo_" + c for c in cs]].any(axis=1)
    sub = d[m]
    rows.append(dict(subregion=s, n=int(m.sum()), pct=round(m.mean() * 100, 1),
                     mean_cites=round(sub.cited_by.mean(), 1), median_cites=float(sub.cited_by.median()),
                     pct_P3=round((sub.year >= 2020).mean() * 100, 1), pct_french=round((sub.lang == "fr").mean() * 100, 1),
                     pct_csr_esg=round((sub["k_CSR"] | sub["k_ESG"] | sub["k_sustainability"]).mean() * 100, 1),
                     pct_gender=round(sub["k_board gender diversity"].mean() * 100, 1),
                     pct_sharia=round((sub["k_Sharia governance"] | sub["k_Islamic banks"]).mean() * 100, 1)))
sr = pd.DataFrame(rows); sr.to_csv(os.path.join(T, "subregions.csv"), index=False); X["subregions"] = rows
# French-language sub-corpus
fr = d[d.lang == "fr"]; X["french_n"] = len(fr); X["french_maghreb_share"] = float(fr[["geo_Algeria", "geo_Morocco", "geo_Tunisia", "geo_North Africa/Maghreb"]].any(axis=1).mean())
X["french_mean_cites"] = float(fr.cited_by.mean())
# outcome x mechanism
X["n_esg_or_csr"] = int((d["k_CSR"] | d["k_ESG"] | d["k_CSR disclosure"] | d["k_sustainability reporting"] | d["k_environmental disclosure"]).sum())
X["n_gender"] = int(d["k_board gender diversity"].sum())
X["n_gender_P3_share"] = float((d[d["k_board gender diversity"]].year >= 2020).mean())
X["n_sharia"] = int(d["k_Sharia governance"].sum()); X["n_islamic"] = int(d["k_Islamic banks"].sum())
X["n_employees"] = int(d["k_employees / HRM"].sum()); X["n_inclusion"] = int(d["k_inclusion / diversity"].sum())
X["n_family"] = int(d["k_family ownership / family firms"].sum()); X["n_state"] = int(d["k_state ownership"].sum())
X["n_institutional"] = int(d["k_institutional investors"].sum()); X["n_climate"] = int(d["k_climate / carbon"].sum())
X["n_political"] = int(d["k_political connections"].sum()); X["n_smes"] = int(d["k_SMEs"].sum())
X["n_panel"] = int(d["k_panel data / regression"].sum()); X["n_content"] = int(d["k_content analysis"].sum())
X["n_survey"] = int(d["k_survey / questionnaire"].sum()); X["n_case"] = int(d["k_case study / interviews"].sum())
th = ["agency theory", "stakeholder theory", "legitimacy theory", "institutional theory", "resource dependence theory", "stewardship theory", "signalling theory"]
X["theories"] = {t: int(d["k_" + t].sum()) for t in th}
X["theory_any_share"] = float(d[["k_" + t for t in th]].any(axis=1).mean())
X["theory_any_share_with_abstract"] = float(d[d.abstract.fillna("").str.len() > 50][["k_" + t for t in th]].any(axis=1).mean())
X["abstract_share_by_period"] = {p: float((d[d.year.between(a, b)].abstract.fillna("").str.len() > 50).mean()) for p, a, b in [("P1", 2000, 2012), ("P2", 2013, 2019), ("P3", 2020, 2026)]}
X["publisher_top"] = d.publisher.value_counts().head(8).to_dict()
json.dump(X, open(os.path.join(C, "results_extra.json"), "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(X, indent=1, ensure_ascii=False, default=float))
