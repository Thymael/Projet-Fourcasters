"""Application Streamlit de démonstration du projet Fourcasters."""

import math

import joblib
import pandas as pd
import streamlit as st

from fourcasters_dbt.configuration import FICHIER_COMMUNES
from fourcasters_dbt.ml_incendie import (
    COLONNE_CIBLE,
    FICHIER_PIPELINE,
    charger_donnees,
    preparer_donnees,
    separer_dates,
)
from fourcasters_dbt.ml_simulation import (
    FICHIER_PIPELINE_SIMULATION,
    creer_entrees_simulation,
)


st.set_page_config(
    page_title="Fourcasters | Météo & danger incendie",
    page_icon="🔥",
    layout="wide",
)


st.markdown(
    """
    <style>
        :root {
            --fc-blue: #62b6ff;
            --fc-sky: #99d8ff;
            --fc-green: #72d6a0;
            --fc-fire: #ff9f43;
            --fc-red: #ff5d5d;
            --fc-ink: #f4f7fb;
            --fc-muted: #a9b6c7;
            --fc-panel: rgba(14, 25, 36, 0.78);
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(64, 153, 255, 0.18), transparent 30%),
                radial-gradient(circle at 92% 4%, rgba(255, 111, 42, 0.16), transparent 28%),
                linear-gradient(155deg, #07121d 0%, #0b1b27 48%, #161916 100%);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 1.7rem;
            padding-bottom: 3.5rem;
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: 1.8rem 2rem;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.10);
            background:
                linear-gradient(120deg, rgba(27, 89, 135, 0.44), rgba(28, 62, 54, 0.36) 52%, rgba(126, 55, 24, 0.36));
            box-shadow: 0 18px 45px rgba(0,0,0,0.18);
            margin-bottom: 1.2rem;
        }

        .hero::after {
            content: "☁️  ☀️  🌲  🔥";
            position: absolute;
            right: 1.6rem;
            top: 1.3rem;
            font-size: 2rem;
            letter-spacing: 0.35rem;
            opacity: 0.18;
        }

        .hero-kicker {
            color: var(--fc-sky);
            text-transform: uppercase;
            letter-spacing: .14em;
            font-size: .76rem;
            font-weight: 700;
        }

        .hero h1 {
            margin: .25rem 0 .4rem 0;
            font-size: 2.45rem;
            line-height: 1.05;
        }

        .hero p {
            max-width: 780px;
            margin: 0;
            color: #d9e4ef;
            line-height: 1.55;
        }

        .hero-tags {
            display: flex;
            gap: .55rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .hero-tag {
            padding: .34rem .65rem;
            border: 1px solid rgba(255,255,255,.12);
            border-radius: 999px;
            background: rgba(255,255,255,.05);
            color: #dce8f4;
            font-size: .78rem;
        }

        .section-title {
            margin: .2rem 0 .8rem 0;
            font-size: 1.2rem;
            font-weight: 750;
        }

        .section-subtitle {
            margin-top: -.45rem;
            margin-bottom: .8rem;
            color: var(--fc-muted);
            font-size: .9rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(255,255,255,.09);
            border-radius: 18px;
            background: rgba(255,255,255,.018);
        }

        div[data-testid="stMetric"] {
            padding: .85rem 1rem;
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 15px;
            background: rgba(255,255,255,.025);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--fc-muted);
        }

        div[data-testid="stButton"] button {
            min-height: 3rem;
            border-radius: 13px;
            font-weight: 750;
        }

        div[data-testid="stTabs"] button {
            font-weight: 700;
        }

        .location-card {
            padding: .85rem 1rem;
            border-radius: 14px;
            background: rgba(98,182,255,.08);
            border: 1px solid rgba(98,182,255,.18);
            color: #dcecff;
            margin-bottom: .85rem;
        }

        .result-card {
            min-height: 170px;
            padding: 1.15rem 1.2rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,.09);
            background: linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.018));
            box-shadow: 0 12px 28px rgba(0,0,0,.12);
        }

        .result-card.level-1 { border-top: 4px solid #49b96e; }
        .result-card.level-2 { border-top: 4px solid #e5c84b; }
        .result-card.level-3 { border-top: 4px solid #ef933d; }
        .result-card.level-4 { border-top: 4px solid #e34f4f; }

        .result-horizon {
            color: var(--fc-muted);
            font-size: .82rem;
            margin-bottom: .6rem;
            text-transform: uppercase;
            letter-spacing: .08em;
        }

        .result-level {
            font-size: 1.75rem;
            line-height: 1.05;
            font-weight: 850;
        }

        .result-name {
            margin-top: .35rem;
            font-size: 1rem;
            font-weight: 650;
        }

        .result-confidence {
            margin-top: .8rem;
            color: var(--fc-muted);
            font-size: .86rem;
        }

        .match-ok,
        .match-ko {
            margin-top: .8rem;
            padding: .85rem 1rem;
            border-radius: 13px;
        }

        .match-ok {
            background: rgba(73,185,110,.12);
            border: 1px solid rgba(73,185,110,.30);
        }

        .match-ko {
            background: rgba(239,147,61,.12);
            border: 1px solid rgba(239,147,61,.30);
        }

        .small-note {
            color: var(--fc-muted);
            font-size: .86rem;
            line-height: 1.5;
        }

        .footer-note {
            margin-top: 2.3rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,.08);
            color: #8fa0b4;
            font-size: .82rem;
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
def charger_pipeline_historique():
    return joblib.load(FICHIER_PIPELINE)


@st.cache_resource
def charger_pipeline_simulation():
    return joblib.load(FICHIER_PIPELINE_SIMULATION)


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


@st.cache_data
def charger_referentiel() -> pd.DataFrame:
    """Charge les 360 points météo utilisés dans le projet."""
    referentiel = pd.read_csv(
        FICHIER_COMMUNES,
        dtype={
            "numero_departement": "string",
            "code_insee": "string",
        },
    )
    referentiel["numero_departement"] = (
        referentiel["numero_departement"].str.strip()
    )
    return referentiel.sort_values(
        ["numero_departement", "commune"]
    ).reset_index(drop=True)


def calculer_vpd(
    temperature_maximale: float,
    humidite_moyenne: float,
) -> float:
    """Estime le VPD en kPa à partir de la température et de l'humidité."""
    pression_saturation = 0.6108 * math.exp(
        (17.27 * temperature_maximale)
        / (temperature_maximale + 237.3)
    )
    return max(
        0.0,
        pression_saturation * (1 - humidite_moyenne / 100),
    )


def carte_niveau(
    horizon: str,
    niveau: int,
    confiance: float | None = None,
) -> None:
    nom = NOMS_NIVEAUX.get(niveau, "Inconnu")
    confiance_html = ""
    if confiance is not None:
        confiance_html = (
            f'<div class="result-confidence">'
            f'Confiance du modèle : {confiance:.0%}'
            f'</div>'
        )

    st.markdown(
        f"""
        <div class="result-card level-{niveau}">
            <div class="result-horizon">{horizon}</div>
            <div class="result-level">Niveau {niveau}</div>
            <div class="result-name">{nom}</div>
            {confiance_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Fourcasters · météo & danger incendie</div>
        <h1>Du ciel au risque feu</h1>
        <p>
            Explorer des cas historiques ou tester un scénario météo
            sur l'un des 360 points du projet.
        </p>
        <div class="hero-tags">
            <span class="hero-tag">🌦️ Open-Meteo</span>
            <span class="hero-tag">🔥 Météo-France</span>
            <span class="hero-tag">📍 360 points météo</span>
            <span class="hero-tag">🤖 Random Forest</span>
        </div>
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
    modele_historique = charger_pipeline_historique()
    donnees_test, x_test = charger_periode_test()
    referentiel = charger_referentiel()
except Exception as erreur:
    st.error(f"Impossible de charger l'application : {erreur}")
    st.stop()


tab_historique, tab_simulation = st.tabs(
    [
        "🗓️ Cas historique",
        "🔥 Simulateur météo",
    ]
)


with tab_historique:
    st.markdown(
        '<div class="section-title">Comparer le modèle à Météo-France</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">'
        'Choisir un bulletin de la période de test, puis comparer '
        'la prédiction au niveau officiel.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        col_date, col_departement, col_echeance = st.columns(
            [1, 1.6, .8]
        )

        dates = sorted(
            donnees_test["date_publication"].dt.date.unique(),
            reverse=True,
        )
        date_choisie = col_date.selectbox(
            "Date de publication",
            dates,
            key="historique_date",
        )

        selection_date = donnees_test[
            donnees_test["date_publication"].dt.date == date_choisie
        ]

        departements = (
            selection_date[
                ["numero_departement", "departement"]
            ]
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
            key="historique_departement",
        )
        numero_departement = libelles[libelle_departement]

        echeances_disponibles = sorted(
            selection_date.loc[
                selection_date["numero_departement"]
                == numero_departement,
                "echeance",
            ].unique()
        )
        echeance = col_echeance.selectbox(
            "Échéance",
            echeances_disponibles,
            key="historique_echeance",
        )

    ligne = selection_date[
        (selection_date["numero_departement"] == numero_departement)
        & (selection_date["echeance"] == echeance)
    ].iloc[0]

    if st.button(
        "Comparer la prédiction",
        type="primary",
        use_container_width=True,
        key="bouton_historique",
    ):
        index = ligne.name
        entree = x_test.loc[[index]]

        prediction = int(modele_historique.predict(entree)[0])
        niveau_officiel = int(ligne[COLONNE_CIBLE])
        probabilites = modele_historique.predict_proba(entree)[0]
        confiance = float(probabilites.max())

        col_modele, col_reference, col_info = st.columns(
            [1, 1, .75]
        )

        with col_modele:
            carte_niveau(
                "Prédiction du modèle",
                prediction,
                confiance,
            )

        with col_reference:
            carte_niveau(
                "Référence Météo-France",
                niveau_officiel,
            )

        with col_info:
            st.metric("Échéance", echeance)
            st.metric(
                "Département",
                str(numero_departement),
            )

        if prediction == niveau_officiel:
            st.markdown(
                '<div class="match-ok">'
                '✅ Le modèle retrouve le niveau officiel.'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="match-ko">'
                '⚠️ Le modèle ne retrouve pas le niveau officiel '
                'pour cette observation.'
                '</div>',
                unsafe_allow_html=True,
            )

        historique_prob, historique_meteo = st.tabs(
            ["📊 Probabilités", "🌦️ Météo utilisée"]
        )

        with historique_prob:
            proba = pd.DataFrame(
                {
                    "Niveau": [
                        f"Niveau {int(classe)} — "
                        f"{NOMS_NIVEAUX[int(classe)]}"
                        for classe in modele_historique.classes_
                    ],
                    "Probabilité": probabilites,
                }
            ).set_index("Niveau")
            st.bar_chart(proba, y="Probabilité")

        with historique_meteo:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Température",
                f"{float(ligne['temperature_moyenne']):.1f} °C",
            )
            m2.metric(
                "Humidité",
                f"{float(ligne['humidite_moyenne']):.0f} %",
            )
            m3.metric(
                "Précipitations",
                f"{float(ligne['precipitations_moyennes']):.2f} mm",
            )
            m4.metric(
                "Rafale maximale",
                f"{float(ligne['rafale_vent_maximale']):.1f} km/h",
            )


with tab_simulation:
    st.markdown(
        '<div class="section-title">Tester un scénario météo</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">'
        'Choisir un point du référentiel, saisir les conditions météo '
        'et estimer le niveau départemental pour aujourd’hui, J+1 et J+2.'
        '</div>',
        unsafe_allow_html=True,
    )

    if not FICHIER_PIPELINE_SIMULATION.exists():
        st.warning(
            "Le modèle du simulateur n'est pas encore entraîné. "
            "Après avoir récupéré cette mise à jour, lance :"
        )
        st.code(
            "uv run dbt build --project-dir fourcasters\n"
            "uv run python scripts/entrainer_ml_simulation.py",
            language="bash",
        )
    else:
        try:
            modele_simulation = charger_pipeline_simulation()
        except Exception as erreur:
            st.error(
                f"Impossible de charger le modèle du simulateur : {erreur}"
            )
            st.stop()

        departements_ref = (
            referentiel[
                ["numero_departement", "departement"]
            ]
            .drop_duplicates()
            .sort_values("numero_departement")
        )

        departements_ref["libelle"] = (
            departements_ref["numero_departement"]
            + " — "
            + departements_ref["departement"]
        )

        with st.form("formulaire_simulation"):
            localisation_1, localisation_2 = st.columns([1, 1.45])

            departement_choisi = localisation_1.selectbox(
                "Département",
                departements_ref["libelle"].tolist(),
            )
            code_departement = departement_choisi.split(
                " — ",
                maxsplit=1,
            )[0]

            villes = referentiel[
                referentiel["numero_departement"]
                == code_departement
            ].copy()

            ville_libelles = {
                f"{ligne.commune} · {ligne.service}": ligne.code_insee
                for ligne in villes.itertuples()
            }

            ville_choisie = localisation_2.selectbox(
                "Ville / point météo",
                list(ville_libelles),
            )
            code_insee = ville_libelles[ville_choisie]

            point = villes[
                villes["code_insee"] == code_insee
            ].iloc[0]

            st.markdown(
                f"""
                <div class="location-card">
                    📍 <strong>{point['commune']}</strong> ·
                    {point['departement']}<br>
                    <span style="opacity:.72">
                    {point['latitude']:.4f}, {point['longitude']:.4f}
                    · {point['service']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### Conditions météo du jour")

            meteo_1, meteo_2, meteo_3 = st.columns(3)
            temperature_moyenne = meteo_1.number_input(
                "Température moyenne (°C)",
                min_value=-30.0,
                max_value=50.0,
                value=25.0,
                step=.5,
            )
            temperature_maximale = meteo_2.number_input(
                "Température maximale (°C)",
                min_value=-30.0,
                max_value=55.0,
                value=31.0,
                step=.5,
            )
            humidite_moyenne = meteo_3.number_input(
                "Humidité moyenne (%)",
                min_value=0.0,
                max_value=100.0,
                value=45.0,
                step=1.0,
            )

            meteo_4, meteo_5 = st.columns(2)
            precipitations = meteo_4.number_input(
                "Précipitations (mm)",
                min_value=0.0,
                max_value=300.0,
                value=0.0,
                step=.5,
            )
            rafale_vent_maximale = meteo_5.number_input(
                "Rafale maximale (km/h)",
                min_value=0.0,
                max_value=250.0,
                value=35.0,
                step=1.0,
            )

            lancer_simulation = st.form_submit_button(
                "🔥 Estimer le danger incendie",
                type="primary",
                use_container_width=True,
            )

        if lancer_simulation:
            if temperature_maximale < temperature_moyenne:
                st.error(
                    "La température maximale doit être supérieure "
                    "ou égale à la température moyenne."
                )
            else:
                vpd = calculer_vpd(
                    temperature_maximale,
                    humidite_moyenne,
                )

                entrees = creer_entrees_simulation(
                    latitude=float(point["latitude"]),
                    longitude=float(point["longitude"]),
                    temperature_moyenne=temperature_moyenne,
                    temperature_maximale=temperature_maximale,
                    humidite_moyenne=humidite_moyenne,
                    precipitations=precipitations,
                    rafale_vent_maximale=rafale_vent_maximale,
                    deficit_pression_vapeur_maximal=vpd,
                )

                predictions = modele_simulation.predict(entrees)
                probabilites = modele_simulation.predict_proba(
                    entrees
                )

                horizons = [
                    "Aujourd'hui",
                    "J+1 · Demain",
                    "J+2 · Après-demain",
                ]

                colonnes_resultat = st.columns(3)
                for index_horizon, colonne in enumerate(
                    colonnes_resultat
                ):
                    niveau = int(predictions[index_horizon])
                    confiance = float(
                        probabilites[index_horizon].max()
                    )
                    with colonne:
                        carte_niveau(
                            horizons[index_horizon],
                            niveau,
                            confiance,
                        )

                st.write("")
                metrique_1, metrique_2, metrique_3 = st.columns(3)
                metrique_1.metric(
                    "Point météo",
                    str(point["commune"]),
                )
                metrique_2.metric(
                    "VPD estimé",
                    f"{vpd:.2f} kPa",
                )
                metrique_3.metric(
                    "Département",
                    str(point["numero_departement"]),
                )

                with st.expander(
                    "Voir le détail des probabilités"
                ):
                    tableau_probabilites = pd.DataFrame(
                        probabilites,
                        columns=[
                            f"Niveau {int(classe)}"
                            for classe in modele_simulation.classes_
                        ],
                        index=horizons,
                    )
                    st.dataframe(
                        tableau_probabilites.style.format(
                            "{:.1%}"
                        ),
                        use_container_width=True,
                    )

                st.markdown(
                    """
                    <div class="small-note">
                        La ville sert de point météo de référence.
                        Le niveau prédit reste un niveau départemental.
                        Le VPD est estimé automatiquement à partir de la
                        température maximale et de l'humidité saisies.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


st.markdown(
    """
    <div class="footer-note">
        Fourcasters est un prototype étudiant. Les estimations affichées
        ne remplacent pas les informations officielles de Météo-France
        et ne doivent pas être utilisées comme outil opérationnel.
    </div>
    """,
    unsafe_allow_html=True,
)
