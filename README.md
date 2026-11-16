# Dossier de réplication – CIG 2027

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24290468.svg)](https://doi.org/10.5281/zenodo.24290468)

**Gouvernance d'entreprise et durabilité dans la région MENA : cartographie bibliométrique, dynamiques thématiques et agenda de recherche (2000–2026)**

Ce dossier permet de reproduire toutes les données, tableaux et figures de la communication.
Date d'extraction des données : 15 novembre 2026 (API publique Crossref).

## Contenu

| Dossier / fichier | Description |
|---|---|
| `Fiche_descriptive_CIG2027.pdf` | Fiche descriptive d'une page |
| `code/00_restore_abstracts.py` | Restaure les résumés (retirés de la version publique) depuis l'API Crossref |
| `code/01_retrieve_crossref.py` | Extraction : 307 requêtes × 6 pages de 1 000 résultats (API Crossref) |
| `code/01b_retrieve_openalex_optional.py` | Contrôle facultatif avec OpenAlex (clé d'API requise) |
| `code/02_screen.py` | Déduplication et filtrage PRISMA (règles R1–R4) |
| `code/03_enrich.py` | Enrichissement : références citées, affiliations (Crossref) |
| `code/thesaurus.py` | Thésaurus contrôlé de 69 concepts (expressions régulières EN/FR) et libellés français |
| `code/04_analysis.py` | Analyses de performance et cartographie (figures 2 à 9, tableaux) |
| `code/05_refmeta.py` | Métadonnées et format APA 7 des références citées |
| `code/06_extra_stats.py` | Statistiques complémentaires (sous-régions, théories, méthodes) |
| `code/07_prisma.py` | Diagramme PRISMA (figure 1) et courbe de saturation |
| `code/run_all.sh` | Exécution complète |
| `data/raw/candidates_identification.csv.gz` | 176 937 notices uniques identifiées, avec indicateurs de filtrage (sans résumés) |
| `data/raw/crossref_full_retained.zip` | Métadonnées Crossref (JSON) des 4 272 articles retenus, sans résumés |
| `data/raw/retrieval_log.json` | Journal d'extraction (requêtes, date, nombre de résultats) |
| `data/clean/corpus_screened.csv` | Corpus final (4 272 articles ; colonne `has_abstract` à la place des résumés) |
| `data/clean/corpus_coded.csv` | Corpus final avec codage des 69 concepts et marqueurs géographiques |
| `data/clean/references.csv` | 154 402 références citées (dont 114 718 avec DOI) |
| `data/clean/affiliations.csv` | Affiliations et pays d'affiliation détectés |
| `data/clean/validation_sample.csv` | Échantillon de validation manuelle (n = 100 ; précision 93 %) |
| `data/clean/prisma_counts.json`, `results.json`, `results_extra.json` | Chiffres cités dans le texte |
| `revision/` | Analyses complémentaires de la révision (rappel, sensibilité, couplage, extraction française) |
| `tables/`, `figures/` | Tableaux intermédiaires (CSV) et figures (PNG 300 dpi) |

## Reproduire

```bash
pip install pandas networkx matplotlib langdetect pycountry adjustText
export PYTHONHASHSEED=0          # ordre déterministe
# export CROSSREF_MAILTO=vous@exemple.org   (facultatif : « polite pool » Crossref)
bash code/run_all.sh
```

Le téléchargement brut (≈ 3 Go de JSON) n'est pas inclus ; il est recréé par `01_retrieve_crossref.py`.
Les résumés déposés dans Crossref appartiennent à leurs éditeurs et ne sont pas redistribués : la colonne `has_abstract` indique les 2 951 articles qui en ont un. Avant toute analyse, lancer `python3 code/00_restore_abstracts.py` pour les récupérer à nouveau (environ 3 000 requêtes Crossref). Le codage des 69 concepts (`corpus_coded.csv`) est fourni tel qu'il a été calculé sur les titres et résumés.

Pour repartir des données fournies sans nouvelle extraction, lancer `00_restore_abstracts.py`, puis directement `04_analysis.py`, `06_extra_stats.py` et `07_prisma.py`
(les étapes 02–03 nécessitent les fichiers bruts). Crossref évoluant en continu, une nouvelle extraction peut produire des effectifs légèrement différents.

## Choix méthodologiques principaux

- Source : Crossref (OpenAlex indisponible sans clé le jour de l'extraction).
- Période : 2000–2026 ; articles de revues ; anglais et français.
- Pays : Algérie, Maroc, Tunisie, Libye, Mauritanie, Égypte, Arabie saoudite, Émirats arabes unis, Qatar, Koweït, Bahreïn, Oman, Jordanie, Liban, Irak, Syrie, Palestine, Yémen, Iran, Turquie (+ désignations régionales).
- Communautés : Louvain (networkx), graine 42 ; cartes stratégiques : indices de centralité et de densité de Callon sur l'indice d'équivalence.

## Limites

Résumés absents pour 31 % des notices ; affiliations disponibles pour 21,7 % des articles ; références déposées pour 54,2 %.
Comptage des auteurs par nom + initiale (homonymies possibles). Articles en arabe non couverts.

## Licence

- Code (`code/`) : licence MIT (voir `LICENSE`).
- Données dérivées, tableaux, figures et documentation : CC BY 4.0. Les métadonnées bibliographiques proviennent de Crossref et restent soumises aux conditions de leurs déposants.

## Citer

Bousbia Laiche, R. (2026). *Dossier de réplication – Gouvernance d'entreprise et durabilité dans la région MENA : cartographie bibliométrique (CIG 2027)* [Jeu de données et code]. Zenodo. https://doi.org/10.5281/zenodo.24290468 (toutes versions)

Auteur : Rabia Bousbia Laiche, Université d'El Oued (Echahid Hamma Lakhdar), Algérie. ORCID [0000-0002-0150-4310](https://orcid.org/0000-0002-0150-4310).
