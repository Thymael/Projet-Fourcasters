"""Application Streamlit de démonstration du modèle Fourcasters."""

import joblib
import pandas as pd
import streamlit as st
from sklearn.metrics import classification_report, confusion_matrix, f1_score

from fourcasters_dbt.ml_incendie import (
    COLONNE_CIBLE,
    FICHIER_PIPELINE,
    VERSION_FEATURES,
    charger_donnees,
    preparer_donnees,
    separer_dates,
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
            --fc-muted: #a9b6c7;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(64,153,255,.18), transparent 30%),
                radial-gradient(circle at 92% 4%, rgba(255,111,42,.16), transparent 28%),
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
            border: 1px solid rgba(255,255,255,.10);
            background:
                linear-gradient(
                    120deg,
                    rgba(27,89,135,.44),
                    rgba(28,62,54,.36) 52%,
                    rgba(126,55,24,.36)
                );
            box-shadow: 0 18px 45px rgba(0,0,0,.18);
            margin-bottom: 1.2rem;
        }

        .hero::after {
            content: "☁️  ☀️  🌲  🔥";
            position: absolute;
            right: 1.6rem;
            top: 1.3rem;
            font-size: 2rem;
            letter-spacing: .35rem;
            opacity: .18;
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
            max-width: 800px;
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

        .result-card {
            min-height: 165px;
            padding: 1.15rem 1.2rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,.09);
            background:
                linear-gradient(
                    145deg,
                    rgba(255,255,255,.055),
                    rgba(255,255,255,.018)
                );
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

        .legend-row {
            display: flex;
            gap: .6rem;
            flex-wrap: wrap;
            margin: .5rem 0 1rem 0;
        }

        .legend-chip {
            padding: .28rem .55rem;
            border-radius: 999px;
            font-size: .78rem;
            border: 1px solid rgba(255,255,255,.10);
        }

        .legend-green { background: rgba(73,185,110,.18); }
        .legend-orange { background: rgba(239,147,61,.18); }
        .legend-red { background: rgba(227,79,79,.18); }

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
    modele = joblib.load(FICHIER_PIPELINE)
    version = getattr(modele, "fourcasters_feature_version", None)
    if version != VERSION_FEATURES:
        raise ValueError(
            "Le pipeline.pkl ne correspond pas au split actuel "
            "2024-2025 → 2026 ou à la fenêtre météo D-6 à D. "
            "Relance scripts/entrainer_ml_incendie.py après dbt build."
        )
    return modele


@st.cache_data(ttl=3600)
def charger_periode_test():
    donnees = charger_donnees().reset_index(drop=True)
    x, _ = preparer_donnees(donnees)
    dates_prevision = pd.to_datetime(
        donnees.loc[x.index, "date_prevision"]
    )
    _, test = separer_dates(dates_prevision)

    indices_test = x.index[test]
    donnees_test = donnees.loc[indices_test].copy()
    x_test = x.loc[indices_test].copy()
    donnees_test["date_publication"] = pd.to_datetime(
        donnees_test["date_publication"]
    )
    donnees_test["date_prevision"] = pd.to_datetime(
        donnees_test["date_prevision"]
    )
    return donnees_test, x_test


@st.cache_data(ttl=3600)
def construire_comparaison_test() -> pd.DataFrame:
    """Compare les prédictions du jeu de test à Météo-France."""
    donnees_test, x_test = charger_periode_test()
    modele = charger_pipeline_historique()

    predictions = modele.predict(x_test).astype(int)
    probabilites = modele.predict_proba(x_test)

    comparaison = donnees_test.loc[
        x_test.index,
        [
            "date_publication",
            "date_prevision",
            "numero_departement",
            "departement",
            "echeance",
            COLONNE_CIBLE,
        ],
    ].copy()

    comparaison["niveau_reel"] = comparaison[COLONNE_CIBLE].astype(int)
    comparaison["niveau_predit"] = predictions
    comparaison["ecart"] = (
        comparaison["niveau_predit"] - comparaison["niveau_reel"]
    )
    comparaison["ecart_absolu"] = comparaison["ecart"].abs()
    comparaison["confiance"] = probabilites.max(axis=1)
    comparaison["resultat"] = comparaison["ecart"].map(
        lambda valeur: "✅ Juste" if valeur == 0 else "❌ Erreur"
    )

    return comparaison.drop(
        columns=[COLONNE_CIBLE]
    ).reset_index(drop=True)


def libelle_niveau(niveau: int) -> str:
    """Retourne le libellé d'un niveau de danger."""
    return f"Niveau {niveau} — {NOMS_NIVEAUX.get(niveau, 'Inconnu')}"


def couleur_niveau(valeur: str) -> str:
    """Couleur d'une cellule selon le niveau de danger."""
    if "Niveau 1" in str(valeur):
        return "background-color: #173b2a; color: #dff7e8; font-weight: 600"
    if "Niveau 2" in str(valeur):
        return "background-color: #4a4118; color: #fff4bc; font-weight: 600"
    if "Niveau 3" in str(valeur):
        return "background-color: #56341c; color: #ffe1c2; font-weight: 600"
    if "Niveau 4" in str(valeur):
        return "background-color: #512525; color: #ffd4d4; font-weight: 600"
    return ""


def couleur_resultat(valeur: str) -> str:
    """Met en évidence une prédiction juste ou fausse."""
    if "Juste" in str(valeur):
        return "background-color: #173b2a; color: #dff7e8; font-weight: 700"
    return "background-color: #512525; color: #ffd4d4; font-weight: 700"


def couleur_ecart(valeur) -> str:
    """Colore l'écart entre niveau prédit et niveau réel."""
    try:
        ecart = abs(float(valeur))
    except (TypeError, ValueError):
        return ""

    if ecart == 0:
        return "background-color: #173b2a; color: #dff7e8; font-weight: 700"
    if ecart == 1:
        return "background-color: #56341c; color: #ffe1c2; font-weight: 700"
    return "background-color: #512525; color: #ffd4d4; font-weight: 700"


def couleur_score(valeur) -> str:
    """Colore une métrique comprise entre 0 et 1."""
    try:
        score = float(valeur)
    except (TypeError, ValueError):
        return ""

    if score >= 0.60:
        return "background-color: #173b2a; color: #dff7e8"
    if score >= 0.30:
        return "background-color: #56341c; color: #ffe1c2"
    return "background-color: #512525; color: #ffd4d4"


def style_matrice(data: pd.DataFrame) -> pd.DataFrame:
    """Colore la diagonale en vert et les erreurs en orange/rouge."""
    styles = pd.DataFrame(
        "",
        index=data.index,
        columns=data.columns,
    )
    maximum = max(int(data.to_numpy().max()), 1)

    for ligne in range(data.shape[0]):
        for colonne in range(data.shape[1]):
            valeur = int(data.iat[ligne, colonne])
            if ligne == colonne:
                styles.iat[ligne, colonne] = (
                    "background-color: #173b2a; "
                    "color: #dff7e8; font-weight: 800"
                )
            elif valeur == 0:
                styles.iat[ligne, colonne] = (
                    "background-color: #17212b; color: #8fa0b4"
                )
            elif valeur / maximum >= 0.25:
                styles.iat[ligne, colonne] = (
                    "background-color: #512525; "
                    "color: #ffd4d4; font-weight: 700"
                )
            else:
                styles.iat[ligne, colonne] = (
                    "background-color: #56341c; color: #ffe1c2"
                )

    return styles


def carte_niveau(
    horizon: str,
    niveau: int,
    confiance: float | None = None,
) -> None:
    nom = NOMS_NIVEAUX.get(niveau, "Inconnu")
    confiance_html = ""
    if confiance is not None:
        confiance_html = (
            '<div class="result-confidence">'
            f"Confiance du modèle : {confiance:.0%}"
            "</div>"
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
        <h1>Du ciel au danger incendie</h1>
        <p>
            Explorer un cas historique et comprendre les performances
            du modèle en comparant ses prédictions aux niveaux officiels
            publiés par Météo-France.
        </p>
        <div class="hero-tags">
            <span class="hero-tag">🌦️ Open-Meteo</span>
            <span class="hero-tag">🔥 Météo-France</span>
            <span class="hero-tag">📍 96 départements</span>
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
except Exception as erreur:
    st.error(f"Impossible de charger l'application : {erreur}")
    st.stop()


tab_historique, tab_resultats = st.tabs(
    [
        "🗓️ Cas historique",
        "📈 Résultats ML",
    ]
)


with tab_historique:
    st.markdown(
        '<div class="section-title">Comparer le modèle à Météo-France</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">'
        "Choisir une date prévue en 2026, un département et l'échéance, "
        "puis comparer la prédiction au niveau officiel Météo-France."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        col_date, col_departement, col_echeance = st.columns(
            [1, 1.6, .8]
        )

        dates = sorted(
            donnees_test["date_prevision"].dt.date.unique(),
            reverse=True,
        )
        date_choisie = col_date.selectbox(
            "Date prévue",
            dates,
            key="historique_date",
        )

        selection_date = donnees_test[
            donnees_test["date_prevision"].dt.date == date_choisie
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

        echeances = sorted(
            selection_date.loc[
                selection_date["numero_departement"]
                == numero_departement,
                "echeance",
            ].unique()
        )
        echeance = col_echeance.selectbox(
            "Échéance",
            echeances,
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
                "Bulletin",
                pd.to_datetime(
                    ligne["date_publication"]
                ).strftime("%d/%m/%Y"),
            )

        if prediction == niveau_officiel:
            st.markdown(
                '<div class="match-ok">'
                "✅ Le modèle retrouve le niveau officiel."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            ecart = prediction - niveau_officiel
            signe = "+" if ecart > 0 else ""
            st.markdown(
                '<div class="match-ko">'
                f"⚠️ Écart de {signe}{ecart} niveau(x) par rapport "
                "à Météo-France."
                "</div>",
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


with tab_resultats:
    st.markdown(
        '<div class="section-title">Résultats du modèle sur 2026</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">'
        "Le Random Forest apprend uniquement sur les cibles 2024-2025. "
        "Toutes les cibles 2026 disponibles sont réservées au test."
        "</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown("#### 🌦️ Le rôle du modèle")
        st.write(
            "Fourcasters rapproche la météo historique et les niveaux "
            "officiels de danger incendie. Le modèle cherche à reproduire "
            "un niveau Météo-France de 1 à 4 à partir des variables météo."
        )
        st.caption(
            "Il ne prédit pas le départ réel d'un feu et ne remplace pas "
            "les informations officielles."
        )
        st.info(
            "Apprentissage : 2024-2025 · Test : 2026. "
            "Fenêtre météo : les 7 derniers jours connus, de D−6 à D. "
            "J1 cible D+1 et J2 cible D+2."
        )

    comparaison = construire_comparaison_test()
    comparaison_2026 = comparaison[
        comparaison["date_prevision"].dt.year == 2026
    ].copy()

    if comparaison_2026.empty:
        st.warning(
            "Aucune observation 2026 n'est présente dans le jeu de test."
        )
    else:
        y_reel = comparaison_2026["niveau_reel"]
        y_predit = comparaison_2026["niveau_predit"]

        accuracy = (y_reel == y_predit).mean()
        f1_macro = f1_score(
            y_reel,
            y_predit,
            labels=[1, 2, 3, 4],
            average="macro",
            zero_division=0,
        )
        classe_majoritaire = y_reel.value_counts(
            normalize=True
        ).max()
        ecart_moyen = comparaison_2026[
            "ecart_absolu"
        ].mean()

        kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
        kpi_1.metric("Accuracy", f"{accuracy:.2%}")
        kpi_2.metric(
            "Référence naïve",
            f"{classe_majoritaire:.2%}",
        )
        kpi_3.metric("F1 macro", f"{f1_macro:.3f}")
        kpi_4.metric(
            "Écart moyen",
            f"{ecart_moyen:.2f} niveau",
        )

        date_min = comparaison_2026[
            "date_prevision"
        ].min().date()
        date_max = comparaison_2026[
            "date_prevision"
        ].max().date()

        st.caption(
            f"Période évaluée : {date_min} → {date_max} · "
            f"{len(comparaison_2026):,} observations."
        )

        exact = (
            comparaison_2026["ecart_absolu"] == 0
        ).mean()
        un_niveau = (
            comparaison_2026["ecart_absolu"] == 1
        ).mean()
        deux_ou_plus = (
            comparaison_2026["ecart_absolu"] >= 2
        ).mean()

        lecture_1, lecture_2, lecture_3 = st.columns(3)
        lecture_1.metric("Même niveau", f"{exact:.1%}")
        lecture_2.metric(
            "Écart d'un niveau",
            f"{un_niveau:.1%}",
        )
        lecture_3.metric(
            "Écart ≥ 2 niveaux",
            f"{deux_ou_plus:.1%}",
        )

        st.markdown(
            """
            <div class="legend-row">
                <span class="legend-chip legend-green">Vert · correct</span>
                <span class="legend-chip legend-orange">Orange · écart faible</span>
                <span class="legend-chip legend-red">Rouge · erreur importante</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Répartition réel / prédit")

        distribution = pd.DataFrame(
            {
                "Météo-France": y_reel.value_counts().reindex(
                    [1, 2, 3, 4],
                    fill_value=0,
                ).to_numpy(),
                "Modèle": y_predit.value_counts().reindex(
                    [1, 2, 3, 4],
                    fill_value=0,
                ).to_numpy(),
            },
            index=[
                "Niveau 1",
                "Niveau 2",
                "Niveau 3",
                "Niveau 4",
            ],
        )
        st.bar_chart(distribution)

        col_performance, col_confusion = st.columns(
            [1.15, 1]
        )

        with col_performance:
            st.markdown("##### Performance par niveau")
            rapport = classification_report(
                y_reel,
                y_predit,
                labels=[1, 2, 3, 4],
                output_dict=True,
                zero_division=0,
            )
            performance = pd.DataFrame(
                {
                    "Niveau": [
                        "Niveau 1 — Faible",
                        "Niveau 2 — Modéré",
                        "Niveau 3 — Élevé",
                        "Niveau 4 — Très élevé",
                    ],
                    "Précision": [
                        rapport[str(niveau)]["precision"]
                        for niveau in [1, 2, 3, 4]
                    ],
                    "Rappel": [
                        rapport[str(niveau)]["recall"]
                        for niveau in [1, 2, 3, 4]
                    ],
                    "F1": [
                        rapport[str(niveau)]["f1-score"]
                        for niveau in [1, 2, 3, 4]
                    ],
                    "Observations": [
                        int(rapport[str(niveau)]["support"])
                        for niveau in [1, 2, 3, 4]
                    ],
                }
            )

            performance_style = (
                performance.style
                .map(couleur_niveau, subset=["Niveau"])
                .map(
                    couleur_score,
                    subset=["Précision", "Rappel", "F1"],
                )
                .format(
                    {
                        "Précision": "{:.1%}",
                        "Rappel": "{:.1%}",
                        "F1": "{:.3f}",
                    }
                )
            )
            st.dataframe(
                performance_style,
                hide_index=True,
                use_container_width=True,
            )

        with col_confusion:
            st.markdown("##### Matrice de confusion")
            matrice = confusion_matrix(
                y_reel,
                y_predit,
                labels=[1, 2, 3, 4],
            )
            matrice_df = pd.DataFrame(
                matrice,
                index=[
                    "Réel N1",
                    "Réel N2",
                    "Réel N3",
                    "Réel N4",
                ],
                columns=[
                    "Prédit N1",
                    "Prédit N2",
                    "Prédit N3",
                    "Prédit N4",
                ],
            )

            matrice_style = (
                matrice_df.style
                .apply(style_matrice, axis=None)
                .set_properties(
                    **{
                        "text-align": "center",
                        "font-size": "1rem",
                    }
                )
            )
            st.dataframe(
                matrice_style,
                use_container_width=True,
            )
            st.caption(
                "La diagonale verte correspond aux bonnes prédictions. "
                "Les cases orange/rouges montrent les confusions."
            )

        st.markdown("#### Détail prédiction vs réalité")

        filtre_1, filtre_2, filtre_3 = st.columns(
            [1.4, .8, .8]
        )

        departements_resultats = ["Tous"] + sorted(
            comparaison_2026[
                "departement"
            ].dropna().unique().tolist()
        )
        departement_filtre = filtre_1.selectbox(
            "Département",
            departements_resultats,
            key="resultats_departement",
        )

        echeance_filtre = filtre_2.selectbox(
            "Échéance",
            ["Toutes", "J1", "J2"],
            key="resultats_echeance",
        )

        resultat_filtre = filtre_3.selectbox(
            "Résultat",
            ["Tous", "✅ Juste", "❌ Erreur"],
            key="resultats_statut",
        )

        detail = comparaison_2026.copy()

        if departement_filtre != "Tous":
            detail = detail[
                detail["departement"]
                == departement_filtre
            ]

        if echeance_filtre != "Toutes":
            detail = detail[
                detail["echeance"]
                == echeance_filtre
            ]

        if resultat_filtre != "Tous":
            detail = detail[
                detail["resultat"]
                == resultat_filtre
            ]

        detail["Réel"] = detail[
            "niveau_reel"
        ].map(libelle_niveau)
        detail["Prédit"] = detail[
            "niveau_predit"
        ].map(libelle_niveau)
        detail["Confiance"] = detail["confiance"]
        detail["Écart"] = detail["ecart"]
        detail["Date prévue"] = detail[
            "date_prevision"
        ].dt.date
        detail["Bulletin"] = detail[
            "date_publication"
        ].dt.date

        tableau = detail[
            [
                "Date prévue",
                "Bulletin",
                "numero_departement",
                "departement",
                "echeance",
                "Réel",
                "Prédit",
                "Écart",
                "Confiance",
                "resultat",
            ]
        ].rename(
            columns={
                "numero_departement": "Dépt.",
                "departement": "Département",
                "echeance": "Horizon",
                "resultat": "Résultat",
            }
        )

        tableau_style = (
            tableau.style
            .map(couleur_niveau, subset=["Réel", "Prédit"])
            .map(couleur_ecart, subset=["Écart"])
            .map(couleur_resultat, subset=["Résultat"])
            .format({"Confiance": "{:.1%}"})
        )

        st.dataframe(
            tableau_style,
            hide_index=True,
            use_container_width=True,
            height=430,
        )

        csv = tableau.to_csv(
            index=False
        ).encode("utf-8-sig")
        st.download_button(
            "⬇️ Télécharger la comparaison 2026",
            data=csv,
            file_name="fourcasters_comparaison_ml_2026.csv",
            mime="text/csv",
            use_container_width=True,
        )

        with st.expander("Comment lire les résultats ?"):
            st.write(
                "**Écart = niveau prédit − niveau officiel.** "
                "0 signifie que le modèle retrouve exactement "
                "Météo-France. +1 signifie qu'il prédit un niveau "
                "plus élevé ; -1 un niveau plus faible."
            )
            st.write(
                "La **référence naïve** utilise un DummyClassifier : "
                "elle prédit toujours la classe la plus fréquente dans "
                "l'apprentissage 2024-2025. Elle sert uniquement de repère minimal."
            )
            st.write(
                "Le **F1 macro** donne le même poids aux quatre niveaux. "
                "Il est utile ici car les niveaux 3 et surtout 4 "
                "sont beaucoup plus rares."
            )


st.markdown(
    """
    <div class="footer-note">
        Fourcasters est un prototype étudiant. Le modèle cherche à
        reproduire le niveau de danger Météo-France ; il ne prédit pas
        les départs de feu réels et ne remplace pas les informations
        officielles.
    </div>
    """,
    unsafe_allow_html=True,
)
