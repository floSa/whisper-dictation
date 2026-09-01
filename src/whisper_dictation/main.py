"""Point d'entrée principal du client de dictée vocale."""

import argparse
import logging
import sys
import time
from typing import Optional

from whisper_dictation.audio import AudioRecorder
from whisper_dictation.client import WhisperClient, WhisperServerUnavailable
from whisper_dictation.config import settings
from whisper_dictation.feedback import SoundFeedback
from whisper_dictation.injector import TextInjector
from whisper_dictation.server_manager import get_server_status, start_server, stop_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
)
logger = logging.getLogger("whisper-dictation")


class DictationApp:
    """Application de dictée globale gérant le raccourci et le cycle d'inférence."""

    def __init__(self) -> None:
        self.recorder = AudioRecorder(sample_rate=settings.sample_rate)
        self.client = WhisperClient(
            base_url=settings.whisper_base_url,
            model=settings.whisper_model,
            language=settings.whisper_language,
            initial_prompt=settings.initial_prompt,
        )
        self.feedback = SoundFeedback(enabled=settings.audio_feedback)
        self.injector = TextInjector(paste_delay_ms=settings.paste_delay_ms)
        self._is_processing = False

    def toggle_dictation(self) -> None:
        """Bascule entre démarrage et arrêt/transcription de la dictée."""
        if self._is_processing:
            logger.debug("Traitement d'une transcription en cours, action ignorée.")
            return

        if not self.recorder.is_recording:
            # Vérification préalable de la disponibilité du serveur
            if not self.client.check_health():
                self.feedback.beep_error()
                logger.warning(
                    "Serveur Whisper inactif sur %s. Démarrez-le avec whisper-start.bat",
                    settings.whisper_base_url,
                )
                return

            self.feedback.beep_start()
            self.recorder.start()
        else:
            self.feedback.beep_stop()
            self._is_processing = True
            try:
                wav_bytes = self.recorder.stop()
                if not wav_bytes:
                    logger.warning("Aucun son capturé.")
                    self.feedback.beep_error()
                    return

                # Inférence
                text = self.client.transcribe(wav_bytes)
                if text:
                    self.injector.paste_text(text)
                    self.feedback.beep_success()
                else:
                    logger.info("Transcription vide.")
            except WhisperServerUnavailable as err:
                logger.error("%s", err)
                self.feedback.beep_error()
            except Exception as err:
                logger.error("Erreur lors de la transcription : %s", err)
                self.feedback.beep_error()
            finally:
                self._is_processing = False

    def run_daemon(self) -> None:
        """Lance l'écouteur global de raccourci clavier en arrière-plan."""
        try:
            from pynput import keyboard
        except ImportError:
            logger.error(
                "Le module 'pynput' n'est pas installé. "
                "Sous Windows, lancez 'uv sync' pour installer les dépendances de raccourcis."
            )
            return

        hotkey_str = settings.dictation_hotkey
        logger.info("Lancement du démon de dictée vocale...")
        logger.info("Raccourci configuré : %s", hotkey_str)
        logger.info("Serveur Whisper cible : %s (Modèle : %s)", settings.whisper_base_url, settings.whisper_model)
        logger.info("Appuyez sur %s pour dicter (Ctrl+C pour quitter)", hotkey_str)

        hotkey_map = {
            hotkey_str: self.toggle_dictation,
        }

        try:
            with keyboard.GlobalHotKeys(hotkey_map) as listener:
                listener.join()
        except Exception as err:
            logger.error("Erreur lors de l'écoute du raccourci clavier : %s", err)


def cmd_status() -> None:
    """Affiche l'état du serveur et de la configuration."""
    print("=== État Whisper Dictation ===")
    print(f"URL serveur : {settings.whisper_base_url}")
    print(f"Modèle      : {settings.whisper_model}")
    print(f"Raccourci   : {settings.dictation_hotkey}")
    print(f"Langue      : {settings.whisper_language}")

    client = WhisperClient(base_url=settings.whisper_base_url)
    healthy = client.check_health()
    status_str = "Disponible / En ligne" if healthy else "Inaccessible / Éteint"
    print(f"API Whisper : {status_str}")

    running, desc = get_server_status()
    print(f"Docker      : {desc}")


def main() -> None:
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(description="Client de dictée vocale Whisper")
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    subparsers.add_parser("run", help="Lancer l'écouteur global de raccourci (défaut)")
    subparsers.add_parser("status", help="Vérifier l'état du serveur et de la config")
    subparsers.add_parser("start-server", help="Démarrer le conteneur Docker Whisper")
    subparsers.add_parser("stop-server", help="Arrêter le conteneur Whisper (libérer la VRAM)")

    args = parser.parse_args()
    cmd = args.command or "run"

    if cmd == "run":
        app = DictationApp()
        app.run_daemon()
    elif cmd == "status":
        cmd_status()
    elif cmd == "start-server":
        start_server()
    elif cmd == "stop-server":
        stop_server()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
