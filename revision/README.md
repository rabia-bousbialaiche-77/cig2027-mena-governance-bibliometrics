# Analyses complémentaires de la révision (novembre 2026)

Ces scripts et sorties répondent au rapport d'évaluation de la communication (CIG 2027). Exécuter les scripts depuis `revision/code/`, après `code/00_restore_abstracts.py` lorsque les résumés sont nécessaires.

| Script | Objet | Sorties (`outputs/`) |
|---|---|---|
| `a1a2_sample.py` | Part des notices examinées disposant d'un résumé (échantillon de 2 000) ; échantillons aléatoires d'exclus (R3, R4) | `a1_echantillon_resumes.csv` |
| `a2b.py` | Échantillons des strates d'exclusion à risque (R3 sur sujet ; R4 avec signal « governance ») | `audit_rappel_codage.csv` (codage des 200 notices) |
| `stats_a.py` | Réunion / intersection gouvernance–durabilité par sous-période ; effectifs francophones ; Bradford sans SSRN ; fréquences rapportées aux articles avec résumé | `stats_a.json` |
| `sensibilite_pays_arabes.py` | Corpus sans articles portant uniquement sur la Turquie ou l'Iran et sans trois études multirégionales | `sensibilite_pays_arabes_*.json/csv` |
| `a5_coupling.py` | Couplage bibliographique : cohorte 2020–2026 et classement par citations annuelles | `a5.json` |
| `a9_harvest.py`, `a9_screen.py` | Extraction complémentaire avec une matrice française élargie (96 requêtes, 16 novembre 2026) | `a9.json`, `a9_nouveaux_candidats_fr.csv` |

Les figures 3, 5, 6, 7, 8 et 9 ont été régénérées (`code/04_analysis.py`) : étiquettes rattachées aux points, noms de pays en français, légendes complétées. Les résultats numériques sont identiques à la version 1.0.0.

Le codage du rappel (`audit_rappel_codage.csv`) repose sur un codeur unique, à partir du titre et du résumé.
