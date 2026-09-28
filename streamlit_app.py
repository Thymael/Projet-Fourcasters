"""Application Streamlit de démonstration du modèle Fourcasters."""

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


st.set_page_config(
    page_title="Fourcasters | Machine Learning",
    page_icon="🔥",
    layout="wide",
)

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(34, 139, 94, 0.10), transparent 28%),
                radial-gradient(circle at 95% 5%, rgba(245, 124, 0, 0.08), transparent 25%),
                #0e1117;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.6rem 1.8rem;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 20px;
            background: linear-gradient(
                135deg,
                rgba(26, 89, 65, 0.38),
                rgba(18, 25, 35, 0.88)
            );
            margin-bottom: 1.4rem;
        }

        .hero-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            opacity: 0.72;
            margin-bottom: 0.35rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
        }

        .hero p {
            margin: 0.55rem 0 0 0;
            max-width: 850px;
            opacity: 0.84;
            line-height: 1.55;
        }

        .section-title {
            margin-top: 0.2rem;
            margin-bottom: 0.8rem;
            font-size: 1.18rem;
            font-weight: 700;
        }

        .result-card {
            padding: 1.15rem 1.2rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.035);
            min-height: 150px;
        }

        .result-label {
            font-size: 0.84rem;
            opacity: 0.72;
            margin-bottom: 0.55rem;
        }

        .result-level {
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .result-name {
            margin-top: 0.35rem;
            font-size: 1rem;
            font-weight: 600;
        }

        .result-card.level-1 { border-top: 4px solid #2e7d32; }
        .result-card.level-2 { border-top: 4px solid #fbc02d; }
        .result-card.level-3 { border-top: 4px solid #f57c00; }
        .result-card.level-4 { border-top: 4px solid #c62828; }

        .match-ok {
            padding: 0.85rem 1rem;
            border-radius: 12px;
            background: rgba(46, 125, 50, 0.14);
            border: 1px solid rgba(46, 125, 50, 0.35);
        }

        .match-ko {
            padding: 0.85rem 1rem;
            border-radius: 12px;
            background: rgba(245, 124, 0, 0.12);
            border: 1px solid rgba(245, 124, 0, 0.35);
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            background: rgba(255,255,255,0.025);
        }

        div[data-testid="stMetricLabel"] {
            opacity: 0.72;
        }

        div[data-testid="stButton"] button {
            border-radius: 12px;
            min-height: 3rem;
            font-weight: 700;
        }

        div[data-testid="stSelectbox"] > div > div {
            border-radius: 10px;
        }

        .small-note {
            opacity: 0.66;
            font-size: 0.85rem;
            line-height: 1.45;
        }

        .footer-note {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,0.08);
            opacity: 0.65;
            font-size: 0.84rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


NOMS_NIVEAUX = {
    1: "Faible",
    2: "Modéré",
    3: "Élevé",
    4: "Très élevé",
}


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
    donnees_test["date_publication"] = pd.to_datetime(
        donnees_test["date_publication"]
    )
    return donnees_test, x_test


def carte_niveau(titre: str, niveau: int) -> None:
    nom = NOMS_NIVEAUX.get(niveau, "Inconnu")
    st.markdown(
        f"""
        <div class="result-card level-{niveau}">
            <div class="result-label">{titre}</div>
            <div class="result-level">Niveau {niveau}</div>
            <div class="result-name">{nom}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Fourcasters · Prototype Machine Learning</div>
        <h1>🔥 Danger incendie & météo</h1>
        <p>
            Test du modèle sur la période réservée à l'évaluation.
            On compare la prédiction du Random Forest au niveau officiel publié
            par Météo-France.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not FICHIER_PIPELINE.exists():
    st.error(
        "Le fichier pipeline.pkl est absent. Lance d'abord : "
        "`uv run python scripts/entrainer_ml_incendie.py`"
    )
    st.stop()

try:
    modele = charger_pipeline()
    donnees_test, x_test = charger_periode_test()
except Exception as erreur:
    st.error(f"Impossible de charger les données : {erreur}")
    st.stop()


st.markdown(
    '<div class="section-title">1. Choisir une observation</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    col_date, col_departement, col_echeance = st.columns([1, 1.6, 0.8])

    dates = sorted(
        donnees_test["date_publication"].dt.date.unique(),
        reverse=True,
    )
    date_choisie = col_date.selectbox(
        "Date de publication",
        dates,
        help="Date du bulletin Météo-France utilisé pour la comparaison.",
    )

    selection_date = donnees_test[
        donnees_test["date_publication"].dt.date == date_choisie
    ]

    departements = (
        selection_date[["numero_departement", "departement"]]
        .drop_duplicates()
        .sort_values("numero_departement")
    )
    libelles = {
        f"{ligne.numero_departement} — {ligne.departement}":
            ligne.numero_departement
        for ligne in departements.itertuples()
    }

    libelle_departement = col_departement.selectbox(
        "Département",
        list(libelles),
    )
    numero_departement = libelles[libelle_departement]

    echeances_disponibles = sorted(
        selection_date.loc[
            selection_date["numero_departement"] == numero_departement,
            "echeance",
        ].unique()
    )
    echeance = col_echeance.selectbox(
        "Échéance",
        echeances_disponibles,
        help="J1 = lendemain de la publication, J2 = surlendemain.",
    )

ligne = selection_date[
    (selection_date["numero_departement"] == numero_departement)
    & (selection_date["echeance"] == echeance)
].iloc[0]

st.markdown(
    """
    <div class="small-note">
        Cette interface sert à tester le prototype sur des observations
        historiques gardées pour l'évaluation. Elle ne fournit pas une
        prévision opérationnelle en temps réel.
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

if st.button(
    "Lancer la prédiction",
    type="primary",
    use_container_width=True,
):
    index = ligne.name
    entree = x_test.loc[[index]]

    prediction = int(modele.predict(entree)[0])
    niveau_officiel = int(ligne[COLONNE_CIBLE])
    probabilites_modele = modele.predict_proba(entree)[0]
    confiance = float(probabilites_modele.max())

    st.markdown(
        '<div class="section-title">2. Résultat</div>',
        unsafe_allow_html=True,
    )

    col_modele, col_reference, col_confiance = st.columns([1, 1, 0.8])

    with col_modele:
        carte_niveau("Prédiction du modèle", prediction)

    with col_reference:
        carte_niveau("Référence Météo-France", niveau_officiel)

    with col_confiance:
        st.metric(
            "Confiance maximale",
            f"{confiance:.0%}",
            help="Probabilité la plus élevée attribuée par le modèle.",
        )
        st.metric(
            "Échéance",
            echeance,
        )

    if prediction == niveau_officiel:
        st.markdown(
            """
            <div class="match-ok">
                ✅ Le modèle retrouve le niveau officiel pour cette observation.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="match-ko">
                ⚠️ Le modèle ne retrouve pas le niveau officiel pour cette observation.
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_probabilites, tab_meteo, tab_details = st.tabs(
        ["📊 Probabilités", "🌦️ Météo utilisée", "ℹ️ Détails"]
    )

    with tab_probabilites:
        probabilites = pd.DataFrame(
            {
                "Niveau": [
                    f"Niveau {int(classe)} — {NOMS_NIVEAUX[int(classe)]}"
                    for classe in modele.classes_
                ],
                "Probabilité": probabilites_modele,
            }
        ).set_index("Niveau")

        st.subheader("Répartition des probabilités")
        st.bar_chart(
            probabilites,
            y="Probabilité",
            horizontal=True,
        )
        st.caption(
            "La classe la plus probable devient la prédiction affichée au-dessus."
        )

    with tab_meteo:
        st.subheader("Conditions météo utilisées")

        meteo_1, meteo_2, meteo_3, meteo_4 = st.columns(4)
        meteo_1.metric(
            "Température",
            f"{float(ligne['temperature_moyenne']):.1f} °C",
        )
        meteo_2.metric(
            "Humidité",
            f"{float(ligne['humidite_moyenne']):.0f} %",
        )
        meteo_3.metric(
            "Précipitations",
            f"{float(ligne['precipitations_moyennes']):.2f} mm",
        )
        meteo_4.metric(
            "Rafale maximale",
            f"{float(ligne['rafale_vent_maximale']):.1f} km/h",
        )

        if "deficit_pression_vapeur_maximal" in ligne.index:
            st.metric(
                "VPD maximal",
                f"{float(ligne['deficit_pression_vapeur_maximal']):.2f}",
                help=(
                    "Déficit de pression de vapeur : "
                    "indicateur de sécheresse de l'air."
                ),
            )

    with tab_details:
        st.subheader("Observation sélectionnée")
        st.write(
            {
                "Date de publication": str(date_choisie),
                "Département": libelle_departement,
                "Échéance": echeance,
                "Niveau prédit": (
                    f"{prediction} — {NOMS_NIVEAUX[prediction]}"
                ),
                "Niveau officiel": (
                    f"{niveau_officiel} — {NOMS_NIVEAUX[niveau_officiel]}"
                ),
            }
        )
        st.info(
            "Le Random Forest atteint 55,51 % d'accuracy sur la période de test. "
            "Les niveaux 3 et 4 restent les plus difficiles à reconnaître."
        )

st.markdown(
    """
    <div class="footer-note">
        Prototype étudiant Fourcasters · Le modèle cherche à reproduire le
        niveau de danger Météo-France. Il ne prédit pas les départs de feu réels
        et ne remplace pas les informations officielles.
    </div>
    """,
    unsafe_allow_html=True,
)
