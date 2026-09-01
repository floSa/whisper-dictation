"""Injection de texte transcrit dans la fenêtre active."""

import logging
import platform
import time
import pyperclip

logger = logging.getLogger(__name__)


class TextInjector:
    """Injecte du texte au niveau du curseur via presse-papier et collage."""

    def __init__(self, paste_delay_ms: int = 100) -> None:
        self.paste_delay_sec = paste_delay_ms / 1000.0
        self._is_windows = platform.system() == "Windows"

    def paste_text(self, text: str) -> None:
        """Copie le texte dans le presse-papier et simule Ctrl+V."""
        if not text:
            logger.debug("Aucun texte à coller.")
            return

        # Copie du nouveau texte
        try:
            pyperclip.copy(text)
            logger.debug("Texte copié dans le presse-papier.")
        except Exception as err:
            logger.error("Erreur lors de la copie dans le presse-papier : %s", err)
            return

        time.sleep(self.paste_delay_sec)

        # Simulation de la combinaison Ctrl+V
        try:
            from pynput.keyboard import Controller, Key

            keyboard = Controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press("v")
                keyboard.release("v")
            logger.debug("Combinaison Ctrl+V envoyée via pynput.")
        except Exception as err:
            logger.debug("pynput non disponible ou erreur Ctrl+V : %s", err)
            try:
                import pyautogui

                pyautogui.hotkey("ctrl", "v")
                logger.debug("Combinaison Ctrl+V envoyée via pyautogui.")
            except Exception as err_fallback:
                logger.debug("pyautogui non disponible : %s", err_fallback)
