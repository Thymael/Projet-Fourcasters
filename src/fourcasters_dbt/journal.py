"""Même format de messages pour les trois scripts du projet."""

import logging


def configurer_logs() -> None:
    """Affiche l'heure, le niveau et le message dans la console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
