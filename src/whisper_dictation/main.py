"""Point d'entrée principal du client de dictée vocale."""

import argparse
import ctypes
import logging
import platform
import subprocess
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

_global_mutex = None


def acquire_single_instance_lock() -> bool:
    """Garantit qu'une seule instance de whisper-dictation tourne sous Windows."""
    global _global_mutex
    if platform.system() != "Windows":
        return True

    ERROR_ALREADY_EXISTS = 183
    _global_mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "WhisperDictationUserSessionMutex")
    last_error = ctypes.windll.kernel32.GetLastError()
    if last_error == ERROR_ALREADY_EXISTS:
        logger.warning("Une autre instance de whisper-dictation est déjà en cours d'exécution. Arrêt du doublon.")
        return False
    return True


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
        logger.info("Signal raccourci reçu !")
        if self._is_processing:
            logger.debug("Traitement d'une transcription en cours, action ignorée.")
            return

        if not self.recorder.is_recording:
            # Démarrage instantané de l'enregistrement microphone
            print(">>> ENREGISTREMENT EN COURS... (Parlez maintenant) <<<")
            self.feedback.beep_start()
            try:
                self.recorder.start()
            except Exception as err:
                logger.error("Impossible de démarrer le microphone : %s", err)
                self.feedback.beep_error(f"Microphone inaccessible : {err}")
        else:
            print(">>> ARRET ENREGISTREMENT -> Transcription GPU en cours... <<<")
            self.feedback.beep_stop()
            self._is_processing = True
            try:
                wav_bytes = self.recorder.stop()
                if not wav_bytes or len(wav_bytes) < 1000:
                    logger.warning("Son capturé vide ou trop court.")
                    self.feedback.beep_error("Enregistrement audio vide ou trop court")
                    return

                # Inférence avec auto-réveil du serveur si besoin
                text = None
                try:
                    text = self.client.transcribe(wav_bytes)
                except WhisperServerUnavailable:
                    logger.info("Serveur indisponible, tentative de réveil automatique...")
                    subprocess.run(
                        [
                            "wsl.exe",
                            "-d",
                            "Ubuntu-24.04",
                            "--",
                            "bash",
                            "/home/florian/mes_projets/whisper-dictation/scripts/start_server.sh",
                        ],
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        timeout=15,
                        check=False,
                    )
                    time.sleep(2)
                    text = self.client.transcribe(wav_bytes)

                if text:
                    print(f">>> TRANSCRIPTION : \"{text}\" -> Collage...")
                    self.injector.paste_text(text)
                    self.feedback.beep_success()
                    print(">>> TERMINE !\n")
                else:
                    logger.info("Transcription vide retournée.")
            except WhisperServerUnavailable as err:
                logger.error("Serveur indisponible : %s", err)
                self.feedback.beep_error(f"Serveur Whisper injoignable : {err}")
            except Exception as err:
                logger.error("Erreur inattendue : %s", err)
                self.feedback.beep_error(f"Erreur inattendue : {err}")
            finally:
                self._is_processing = False

    def run_daemon(self) -> None:
        """Lance l'écouteur global de raccourci clavier en arrière-plan."""
        if not acquire_single_instance_lock():
            sys.exit(0)

        print("=" * 60)
        print("  WHISPER DICTATION (Large-v3 sur GPU CUDA)")
        print(f"  Serveur cible : {settings.whisper_base_url}")
        print("  Raccourcis actifs :")
        print("    -> Ctrl + Alt + D   (Recommandé : D pour Dictée)")
        print("    -> Ctrl + Alt + W   (W pour Whisper)")
        print("    -> F8 (ou Fn+8 sur clavier 60%)")
        print("=" * 60)
        print("En attente d'un raccourci... (Laissez cette fenêtre ouverte)\n")

        from pynput import keyboard

        hotkey_map = {
            "<ctrl>+<alt>+d": self.toggle_dictation,
            "<ctrl>+<alt>+w": self.toggle_dictation,
            "<f8>": self.toggle_dictation,
        }
        if settings.dictation_hotkey not in hotkey_map:
            hotkey_map[settings.dictation_hotkey] = self.toggle_dictation

        logger.info("Écouteur pynput actif sur : %s", list(hotkey_map.keys()))

        with keyboard.GlobalHotKeys(hotkey_map) as listener:
            listener.join()


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
