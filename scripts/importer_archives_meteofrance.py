"""Point d'entrée de l'import historique Météo-France."""

import logging

from fourcasters_dbt.archives_meteofrance import importer_archives
from fourcasters_dbt.journal import configurer_logs


if __name__ == "__main__":
    configurer_logs()
    try:
        importer_archives()
    except Exception:
        logging.getLogger(__name__).exception("❌ Import des archives interrompu")
        raise SystemExit(1)
