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
        if self._is_windows:
            try:
                import ctypes

                VK_CONTROL = 0x11
                VK_V = 0x56
                KEYEVENTF_KEYUP = 0x0002

                user32 = ctypes.windll.user32
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                user32.keybd_event(VK_V, 0, 0, 0)
                time.sleep(0.01)
                user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                logger.debug("Combinaison Ctrl+V envoyée via Win32 keybd_event natif.")
                return
            except Exception as err:
                logger.error("Erreur keybd_event Win32 : %s", err)

        # Fallback pour Linux ou si Win32 échoue
        try:
            from pynput.keyboard import Controller, Key

            keyboard = Controller()
            with keyboard.pressed(Key.ctrl):
                keyboard.press("v")
                keyboard.release("v")
            logger.debug("Combinaison Ctrl+V envoyée via pynput.")
        except Exception:
            try:
                import pyautogui

                pyautogui.hotkey("ctrl", "v")
            except Exception as err_fallback:
                logger.debug("pyautogui non disponible : %s", err_fallback)
