"""Gestion des retours sonores et visuels pour la dictée."""

import logging
import platform
import threading

logger = logging.getLogger(__name__)


class SoundFeedback:
    """Émetteur de signaux sonores discrets."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._is_windows = platform.system() == "Windows"

    def _play_beep(self, freq: int, duration_ms: int) -> None:
        """Joue une tonalité sur Windows ou émet un signal."""
        if not self.enabled:
            return

        def _worker() -> None:
            if self._is_windows:
                try:
                    import winsound

                    winsound.Beep(freq, duration_ms)
                except Exception as err:
                    logger.debug("Échec winsound : %s", err)
            else:
                # Signal sonore terminal / log sur Linux
                logger.debug("Signal audio (%d Hz, %d ms)", freq, duration_ms)

        threading.Thread(target=_worker, daemon=True).start()

    def beep_start(self) -> None:
        """Signal aigu indiquant le début de l'enregistrement."""
        logger.info("Enregistrement démarré...")
        self._play_beep(880, 100)

    def beep_stop(self) -> None:
        """Signal médium indiquant la fin de l'enregistrement et le début du calcul."""
        logger.info("Enregistrement arrêté, transcription en cours...")
        self._play_beep(587, 100)

    def beep_success(self) -> None:
        """Signal aigu court confirmant le collage du texte."""
        logger.info("Transcription collée avec succès.")
        self._play_beep(1046, 80)

    def beep_error(self) -> None:
        """Double signal grave indiquant une erreur (serveur inaccessible, micro muet...)."""
        logger.warning("Erreur survenue lors de la dictée.")

        def _error_worker() -> None:
            if self._is_windows:
                try:
                    import time
                    import winsound

                    winsound.Beep(300, 150)
                    time.sleep(0.05)
                    winsound.Beep(300, 200)
                except Exception as err:
                    logger.debug("Échec winsound : %s", err)

        if self.enabled:
            threading.Thread(target=_error_worker, daemon=True).start()
