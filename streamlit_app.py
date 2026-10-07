"""Application Streamlit de démonstration du modèle Fourcasters."""

import joblib
import pandas as pd
import streamlit as st

from fourcasters_dbt.ml_incendie import (
    COLONNE_CIBLE,
    FICHIER_PIPELINE,
    VERSION_FEATURES,
    charger_derniere_meteo_complete,
    charger_donnees,
    preparer_donnees,
    preparer_predictions_derniere_meteo,
    separer_dates,
)


st.set_page_config(
    page_title="Fourcasters - danger incendie",
    page_icon=":material/local_fire_department:",
    layout="wide",
)

NOMS_NIVEAUX = {
    1: "Faible",
    2: "Modéré",
    3: "Élevé",
    4: "Très élevé",
}


def libelle_niveau(niveau: int) -> str:
    """Retourne le libellé lisible d'un niveau de danger."""
    return f"Niveau {niveau} - {NOMS_NIVEAUX.get(niveau, 'Inconnu')}"


@st.cache_resource
def charger_pipeline():
    """Charge le pipeline entraîné et vérifie sa version de variables."""
    modele = joblib.load(FICHIER_PIPELINE)
    version = getattr(modele, "fourcasters_feature_version", None)
    if version != VERSION_FEATURES:
        raise ValueError(
            "Le pipeline.pkl ne correspond pas à la version actuelle des variables. "
            "Relance scripts/entrainer_ml_incendie.py après dbt build."
        )
    return modele


@st.cache_data(ttl="1h", max_entries=4)
def calculer_predictions_recentes() -> pd.DataFrame:
    """Prédit J+1 et J+2 depuis la dernière météo complète disponible."""
    donnees = charger_derniere_meteo_complete()
    contexte, x = preparer_predictions_derniere_meteo(donnees)
    modele = charger_pipeline()

    resultats = contexte[
        [
            "meteo_date",
            "date_prevision",
            "numero_departement",
            "departement",
            "region",
            "echeance",
            "temperature_moyenne",
            "humidite_moyenne",
            "precipitations_moyennes",
            "rafale_vent_maximale",
        ]
    ].copy()
    resultats["niveau_predit"] = modele.predict(x).astype(int)
    resultats["confiance"] = modele.predict_proba(x).max(axis=1)
    resultats["niveau"] = resultats["niveau_predit"].map(libelle_niveau)
    return resultats


@st.cache_data(ttl="1h", max_entries=4)
def charger_cas_historiques() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge uniquement la période de test utilisée pour la comparaison."""
    donnees = charger_donnees().reset_index(drop=True)
    x, _ = preparer_donnees(donnees)
    dates_prevision = pd.to_datetime(donnees.loc[x.index, "date_prevision"])
    _, test = separer_dates(dates_prevision)
    indices_test = x.index[test]

    donnees_test = donnees.loc[indices_test].copy()
    donnees_test["date_publication"] = pd.to_datetime(
        donnees_test["date_publication"]
    )
    donnees_test["date_prevision"] = pd.to_datetime(
        donnees_test["date_prevision"]
    )
    return donnees_test, x.loc[indices_test].copy()


def options_departements(donnees: pd.DataFrame) -> dict[str, str]:
    """Construit les libellés de sélection des départements."""
    departements = (
        donnees[["numero_departement", "departement"]]
        .drop_duplicates()
        .sort_values("numero_departement")
    )
    return {
        f"{ligne.numero_departement} - {ligne.departement}": ligne.numero_departement
        for ligne in departements.itertuples()
    }


st.title("Fourcasters", icon=":material/forest:")
st.markdown(
    "Estimer le niveau de danger Météo-France à **J+1** et **J+2** à partir "
    "de la dernière journée météo complète disponible."
)
st.caption(
    "Prototype étudiant. Le modèle reproduit un niveau officiel de danger. "
    "Il ne prévoit ni les départs de feu ni l'évolution de la météo."
)

if not FICHIER_PIPELINE.exists():
    st.error(
        "Le fichier pipeline.pkl est absent. Lance d'abord "
        "`uv run python scripts/entrainer_ml_incendie.py`."
    )
    st.stop()

try:
    modele = charger_pipeline()
    predictions_recentes = calculer_predictions_recentes()
except Exception as erreur:
    st.error(f"Impossible de charger les prédictions : {erreur}")
    st.stop()

date_meteo = predictions_recentes["meteo_date"].iloc[0].date()
dates_prevues = (
    predictions_recentes[["echeance", "date_prevision"]]
    .drop_duplicates()
    .sort_values("echeance")
)
date_j1 = dates_prevues.loc[
    dates_prevues["echeance"] == "J1", "date_prevision"
].iloc[0].date()
date_j2 = dates_prevues.loc[
    dates_prevues["echeance"] == "J2", "date_prevision"
].iloc[0].date()

with st.container(horizontal=True):
    st.metric("Dernière météo complète", date_meteo.strftime("%d/%m/%Y"), border=True)
    st.metric("Prédiction J+1", date_j1.strftime("%d/%m/%Y"), border=True)
    st.metric("Prédiction J+2", date_j2.strftime("%d/%m/%Y"), border=True)

tab_predictions, tab_historique, tab_methode = st.tabs(
    [
        ":material/query_stats: Prédictions",
        ":material/history: Cas historique",
        ":material/info: Méthode et limites",
    ]
)

with tab_predictions:
    st.header("Prédictions depuis la dernière météo disponible")
    st.caption(
        f"Les variables météo couvrent les sept jours du "
        f"{date_meteo - pd.Timedelta(days=6):%d/%m/%Y} au {date_meteo:%d/%m/%Y}. "
        f"Le modèle calcule ensuite les niveaux du {date_j1:%d/%m/%Y} "
        f"et du {date_j2:%d/%m/%Y}."
    )

    libelles = options_departements(predictions_recentes)
    selection_par_defaut = next(
        (index for index, libelle in enumerate(libelles) if libelle.startswith("83 -")),
        0,
    )
    libelle_departement = st.selectbox(
        "Département",
        list(libelles),
        index=selection_par_defaut,
        key="prediction_departement",
    )
    numero_departement = libelles[libelle_departement]
    selection = predictions_recentes[
        predictions_recentes["numero_departement"] == numero_departement
    ].sort_values("echeance")

    colonnes = st.columns(2, gap="large")
    for colonne, ligne in zip(colonnes, selection.itertuples(), strict=True):
        with colonne.container(border=True, height="stretch"):
            st.subheader(
                f"{ligne.echeance} - {ligne.date_prevision:%d/%m/%Y}",
                icon=":material/calendar_today:",
            )
            st.metric("Niveau estimé", libelle_niveau(ligne.niveau_predit))
            st.caption(
                f"Probabilité la plus élevée du modèle : {ligne.confiance:.0%}. "
                "Cette valeur reste indicative."
            )

    with st.expander("Météo utilisée", icon=":material/cloud:"):
        meteo = selection.iloc[0]
        with st.container(horizontal=True):
            st.metric("Température moyenne", f"{meteo['temperature_moyenne']:.1f} °C")
            st.metric("Humidité moyenne", f"{meteo['humidite_moyenne']:.0f} %")
            st.metric(
                "Précipitations moyennes",
                f"{meteo['precipitations_moyennes']:.2f} mm",
            )
            st.metric("Rafale maximale", f"{meteo['rafale_vent_maximale']:.1f} km/h")

    st.subheader("Ensemble des départements")
    tableau_predictions = predictions_recentes[
        [
            "date_prevision",
            "numero_departement",
            "departement",
            "echeance",
            "niveau_predit",
            "confiance",
        ]
    ].sort_values(
        ["niveau_predit", "confiance", "numero_departement"],
        ascending=[False, False, True],
    )
    st.dataframe(
        tableau_predictions,
        hide_index=True,
        column_config={
            "date_prevision": st.column_config.DateColumn(
                "Date prévue", format="DD/MM/YYYY"
            ),
            "numero_departement": st.column_config.TextColumn("Dépt."),
            "departement": st.column_config.TextColumn("Département"),
            "echeance": st.column_config.TextColumn("Horizon"),
            "niveau_predit": st.column_config.NumberColumn(
                "Niveau estimé", format="%d"
            ),
            "confiance": st.column_config.NumberColumn(
                "Probabilité max.", format="percent"
            ),
        },
    )

with tab_historique:
    st.header("Comparer une prédiction passée au niveau officiel")
    st.caption(
        "Cette vue sert à vérifier le comportement du prototype sur la période "
        "de test 2026."
    )

    try:
        donnees_test, x_test = charger_cas_historiques()
    except Exception as erreur:
        st.error(f"Impossible de charger les cas historiques : {erreur}")
    else:
        dates = sorted(donnees_test["date_prevision"].dt.date.unique(), reverse=True)
        col_date, col_departement, col_echeance = st.columns([1, 1.6, 0.8])
        date_choisie = col_date.selectbox("Date prévue", dates, key="historique_date")
        selection_date = donnees_test[
            donnees_test["date_prevision"].dt.date == date_choisie
        ]
        libelles_historiques = options_departements(selection_date)
        libelle_historique = col_departement.selectbox(
            "Département",
            list(libelles_historiques),
            key="historique_departement",
        )
        numero_historique = libelles_historiques[libelle_historique]
        echeances = sorted(
            selection_date.loc[
                selection_date["numero_departement"] == numero_historique,
                "echeance",
            ].unique()
        )
        echeance = col_echeance.selectbox(
            "Horizon", echeances, key="historique_echeance"
        )

        ligne = selection_date[
            (selection_date["numero_departement"] == numero_historique)
            & (selection_date["echeance"] == echeance)
        ].iloc[0]
        prediction = int(modele.predict(x_test.loc[[ligne.name]])[0])
        officiel = int(ligne[COLONNE_CIBLE])

        col_modele, col_officiel = st.columns(2, gap="large")
        col_modele.metric("Modèle", libelle_niveau(prediction), border=True)
        col_officiel.metric("Météo-France", libelle_niveau(officiel), border=True)
        if prediction == officiel:
            st.success("Le modèle retrouve le niveau officiel.")
        else:
            st.warning(
                f"Le modèle s'écarte de {prediction - officiel:+d} niveau par "
                "rapport à la référence officielle."
            )

with tab_methode:
    st.header("Méthode et limites")
    st.markdown(
        """
        - Le Random Forest utilise 14 variables météo, dont des indicateurs calculés sur sept jours.
        - L'apprentissage porte sur les cibles 2024 et 2025. L'évaluation finale porte sur 2026 jusqu'au 2 octobre.
        - La date de départ est toujours la dernière météo complète disponible, jamais la date civile du jour.
        - Les niveaux 3 et 4 restent difficiles à reconnaître. Les résultats ne doivent pas guider une décision opérationnelle.
        """
    )
    st.info(
        "Les niveaux officiels publiés par Météo-France restent la référence.",
        icon=":material/verified:",
    )
