"""Lance les deux collectes quotidiennes du projet Fourcasters."""

from fourcasters_dbt import incendie, openmeteo


def main() -> None:
    """Actualise la météo puis le niveau de danger incendie."""

    print("\nACTUALISATION FOURCASTERS")

    # La météo est chargée en premier pour garder un ordre simple dans les logs.
    print("\n1. Open-Meteo")
    openmeteo.main()

    print("\n2. Météo-France - danger incendie")
    incendie.main()

    print("\nActualisation Fourcasters terminée.")


if __name__ == "__main__":
    main()
