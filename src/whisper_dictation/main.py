"""Point d'entrée principal du client de dictée vocale."""

import argparse
import logging
import platform
import sys
import time
from pathlib import Path
from typing import Optional

from whisper_dictation.audio import AudioRecorder
from whisper_dictation.client import WhisperClient, WhisperServerUnavailable
from whisper_dictation.config import settings
from whisper_dictation.feedback import SoundFeedback
from whisper_dictation.injector import TextInjector
from whisper_dictation.server_manager import get_server_status, start_server, stop_server

# Journalisation fichier et console
log_file = Path.home() / ".whisper-dictation.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
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
                print("[ERREUR] Serveur Whisper inactif sur http://localhost:8000/v1 !")
                print("Démarrez-le en double-cliquant sur scripts/whisper-start.bat")
                return

            print(">>> ENREGISTREMENT EN COURS... (Parlez maintenant) <<<")
            self.feedback.beep_start()
            self.recorder.start()
        else:
            print(">>> ARRET ENREGISTREMENT -> Transcription GPU en cours... <<<")
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
                    print(f">>> TRANSCRIPTION : \"{text}\" -> Collage...")
                    self.injector.paste_text(text)
                    self.feedback.beep_success()
                    print(">>> TERMINE !\n")
                else:
                    logger.info("Transcription vide retournée.")
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
        print("=" * 60)
        print("  WHISPER DICTATION (Large-v3 sur GPU CUDA)")
        print(f"  Serveur cible : {settings.whisper_base_url}")
        print("  Raccourcis natifs actifs :")
        print("    -> Ctrl + Alt + D   (Recommandé : D pour Dictée)")
        print("    -> Ctrl + Alt + W   (W pour Whisper)")
        print("    -> F8 (ou Fn+8 sur clavier 60%)")
        print("=" * 60)
        print("En attente d'un raccourci... (Laissez cette fenêtre ouverte)\n")

        if platform.system() == "Windows":
            from whisper_dictation.hotkey import Win32GlobalHotKey

            hk = Win32GlobalHotKey(self.toggle_dictation)
            hk.register(1, "ctrl+alt+d")
            hk.register(2, "ctrl+alt+w")
            hk.register(3, "f8")
            if settings.dictation_hotkey not in ("<ctrl>+<alt>+d", "<ctrl>+<alt>+w", "<f8>"):
                hk.register(4, settings.dictation_hotkey)

            try:
                hk.listen_loop()
            except (KeyboardInterrupt, SystemExit):
                print("\nArrêt du service de dictée.")
            finally:
                hk.unregister_all()
        else:
            # Fallback pynput sous Linux
            try:
                from pynput import keyboard
                hotkey_map = {
                    "<ctrl>+<alt>+d": self.toggle_dictation,
                    "<f8>": self.toggle_dictation,
                }
                with keyboard.GlobalHotKeys(hotkey_map) as listener:
                    listener.join()
            except Exception as err:
                logger.error("Erreur pynput Linux : %s", err)


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
