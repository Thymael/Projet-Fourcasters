# Documentation Fourcasters

Ce dossier regroupe les documents utiles pour comprendre, utiliser et présenter le projet.

## Données et restitution

- `SCHEMA_DONNEES.md` : relations entre les principales tables dbt.
- `DICTIONNAIRE_DONNEES.md` : grain, type et rôle des colonnes finales.
- `GUIDE_POWER_BI.md` : contenu du rapport et ordre conseillé pour la démonstration.
- `CONTROLES_BIGQUERY_FOURCASTERS.sql` : requêtes de contrôle manuel.
- `Fourcasters - Modèle Open-Meteo et danger incendie Météo-France.pbix` : rapport Power BI.
- `Fourcasters_Soutenance_15min.pptx` : présentation finale de 14 diapositives, avec notes orateur.

## Risques et responsabilité

- `Matrice courte_des_risques.xlsx` : risques principaux, gravité, probabilité et mesures prévues.
- `La note de vigilance éthique.md` : limites des données et du modèle.
- `L'audit de sobriété.md` : choix retenus pour limiter les traitements inutiles.
- `Dépendance technologique.md` : dépendances externes et solutions de repli.
- `Face à l'IA Act.md` : positionnement prudent du prototype dans son usage pédagogique.

## Repères communs

- Les 360 points Open-Meteo ne représentent pas toutes les communes françaises.
- Le niveau cible vient de la Météo des forêts de Météo-France. Il ne correspond pas à un incendie observé.
- Le Machine Learning utilise la météo de J-6 à J pour estimer les niveaux de J+1 et J+2.
- J correspond à la dernière date météo complète disponible, pas à la date civile du jour.
- Power BI présente les données historiques et officielles. Streamlit présente les estimations du modèle.
