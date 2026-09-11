"""Appels HTTP avec un délai maximum et trois essais en cas de panne."""

import logging
import time

import requests

logger = logging.getLogger(__name__)
NOMBRE_TENTATIVES = 3


def recuperer_reponse(url: str, *, params=None, headers=None, timeout=60):
    """Réessaie les pannes réseau, les quotas et les erreurs du serveur."""
    for tentative in range(1, NOMBRE_TENTATIVES + 1):
        try:
            reponse = requests.get(url, params=params, headers=headers, timeout=timeout)
            reponse.raise_for_status()
            return reponse
        except requests.RequestException as erreur:
            statut = erreur.response.status_code if erreur.response is not None else None
            # Une clé refusée ou une requête incorrecte ne sera pas réparée en attendant.
            if statut is not None and statut not in (408, 429) and statut < 500:
                raise
            if tentative == NOMBRE_TENTATIVES:
                raise
            pause = 60 if statut == 429 else 10
            logger.warning(
                "⏳ Appel HTTP interrompu (%s). Essai %s/%s dans %s s.",
                statut or type(erreur).__name__, tentative + 1, NOMBRE_TENTATIVES, pause,
            )
            time.sleep(pause)
