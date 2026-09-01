"""Gestion du cycle de vie du conteneur Docker Whisper et de la VRAM."""

import logging
import subprocess
import shutil
from typing import Tuple

logger = logging.getLogger(__name__)

CONTAINER_NAME = "watch-speaches"


def is_docker_available() -> bool:
    """Vérifie si Docker est installé et exécutable."""
    return shutil.which("docker") is not None


def get_server_status() -> Tuple[bool, str]:
    """Retourne l'état du serveur Whisper (actif/inactif) et une description."""
    if not is_docker_available():
        return False, "Docker introuvable sur le système hôte."

    try:
        res = subprocess.run(
            ["docker", "inspect", CONTAINER_NAME, "--format", "{{.State.Status}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            status = res.stdout.strip()
            is_running = status == "running"
            return is_running, f"Conteneur {CONTAINER_NAME} : {status}"
        return False, f"Conteneur {CONTAINER_NAME} inexistant ou non créé."
    except Exception as err:
        return False, f"Erreur de communication Docker : {err}"


def stop_server() -> bool:
    """Arrête le conteneur Docker Whisper pour libérer 100% de la VRAM."""
    logger.info("Arrêt du conteneur Whisper pour libérer la VRAM...")
    try:
        res = subprocess.run(
            ["docker", "stop", CONTAINER_NAME],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            logger.info("Conteneur %s arrêté. VRAM 100%% libérée.", CONTAINER_NAME)
            return True
        logger.warning("Échec de l'arrêt du conteneur : %s", res.stderr)
        return False
    except Exception as err:
        logger.error("Erreur lors de l'arrêt du conteneur : %s", err)
        return False


def start_server() -> bool:
    """Démarre le conteneur Docker Whisper existant."""
    logger.info("Démarrage du conteneur Whisper...")
    try:
        res = subprocess.run(
            ["docker", "start", CONTAINER_NAME],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            logger.info("Conteneur %s démarré avec succès.", CONTAINER_NAME)
            return True
        logger.warning("Échec du démarrage direct du conteneur : %s", res.stderr)
        return False
    except Exception as err:
        logger.error("Erreur lors du démarrage du conteneur : %s", err)
        return False
