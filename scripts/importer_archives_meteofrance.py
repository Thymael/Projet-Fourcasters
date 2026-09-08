"""Point d'entrée de l'import historique Météo-France."""

from fourcasters_dbt.archives_meteofrance import importer_archives


if __name__ == "__main__":
    importer_archives()
