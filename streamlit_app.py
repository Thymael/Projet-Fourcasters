"""Petite application Streamlit pour tester le modèle Fourcasters."""

import joblib
import pandas as pd
import streamlit as st

from fourcasters_dbt.ml_incendie import (
    COLONNE_CIBLE,
    FICHIER_PIPELINE,
    charger_donnees,
    preparer_donnees,
    separer_dates,
)


st.set_page_config(page_title="Fourcasters - Machine Learning", page_icon="🌲")
st.title("Fourcasters - test du modèle incendie")
st.write(
    "Cette page teste le modèle sur la période réservée à l'évaluation. "
    "Le niveau officiel Météo-France reste la référence."
)


@st.cache_resource
def charger_pipeline():
    return joblib.load(FICHIER_PIPELINE)


@st.cache_data(ttl=3600)
def charger_periode_test():
    donnees = charger_donnees().reset_index(drop=True)
    x, _ = preparer_donnees(donnees)
    dates = pd.to_datetime(donnees.loc[x.index, "date_publication"])
    _, test = separer_dates(dates)

    indices_test = x.index[test]
    donnees_test = donnees.loc[indices_test].copy()
    x_test = x.loc[indices_test].copy()
    donnees_test["date_publication"] = pd.to_datetime(donnees_test["date_publication"])
    return donnees_test, x_test


if not FICHIER_PIPELINE.exists():
    st.error(
        "Le fichier pipeline.pkl est absent. Lance d'abord : "
        "uv run python scripts/entrainer_ml_incendie.py"
    )
    st.stop()

try:
    modele = charger_pipeline()
    donnees_test, x_test = charger_periode_test()
except Exception as erreur:
    st.error(f"Impossible de charger les données : {erreur}")
    st.stop()


dates = sorted(donnees_test["date_publication"].dt.date.unique(), reverse=True)
date_choisie = st.selectbox("Date de publication", dates)

selection_date = donnees_test[
    donnees_test["date_publication"].dt.date == date_choisie
]

departements = (
    selection_date[["numero_departement", "departement"]]
    .drop_duplicates()
    .sort_values("numero_departement")
)
libelles = {
    f"{ligne.numero_departement} - {ligne.departement}": ligne.numero_departement
    for ligne in departements.itertuples()
}

libelle_departement = st.selectbox("Département", list(libelles))
numero_departement = libelles[libelle_departement]

echeances_disponibles = sorted(
    selection_date.loc[
        selection_date["numero_departement"] == numero_departement,
        "echeance",
    ].unique()
)
echeance = st.selectbox("Échéance", echeances_disponibles)

ligne = selection_date[
    (selection_date["numero_departement"] == numero_departement)
    & (selection_date["echeance"] == echeance)
].iloc[0]

if st.button("Lancer la prédiction"):
    index = ligne.name
    entree = x_test.loc[[index]]

    prediction = int(modele.predict(entree)[0])
    niveau_officiel = int(ligne[COLONNE_CIBLE])

    col1, col2 = st.columns(2)
    col1.metric("Prédiction du modèle", f"Niveau {prediction}")
    col2.metric("Météo-France", f"Niveau {niveau_officiel}")

    if prediction == niveau_officiel:
        st.success("Le modèle retrouve le niveau officiel pour cette observation.")
    else:
        st.warning("Le modèle ne retrouve pas le niveau officiel pour cette observation.")

    probabilites = pd.DataFrame(
        {
            "Niveau": [f"Niveau {int(classe)}" for classe in modele.classes_],
            "Probabilité": modele.predict_proba(entree)[0],
        }
    ).set_index("Niveau")

    st.subheader("Probabilités du modèle")
    st.bar_chart(probabilites)

    st.subheader("Quelques données météo utilisées")
    st.write(
        {
            "Température moyenne": round(float(ligne["temperature_moyenne"]), 1),
            "Humidité moyenne": round(float(ligne["humidite_moyenne"]), 1),
            "Précipitations moyennes": round(float(ligne["precipitations_moyennes"]), 2),
            "Rafale maximale": round(float(ligne["rafale_vent_maximale"]), 1),
        }
    )

st.caption(
    "Prototype étudiant : le modèle cherche à reproduire un niveau de danger, "
    "il ne prédit pas les départs de feu réels."
)
