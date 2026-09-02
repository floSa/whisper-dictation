"""Module de gestion des raccourcis globaux natifs Windows via Win32 RegisterHotKey."""

import ctypes
import ctypes.wintypes
import logging
import platform
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Constantes Win32
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# Mapping des touches courantes vers les Virtual Key Codes
VK_MAP = {
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73,
    "f5": 0x74, "f6": 0x75, "f7": 0x76, "f8": 0x77,
    "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "space": 0x20, "espace": 0x20,
    "insert": 0x2D, "pause": 0x13,
}
for c in "abcdefghijklmnopqrstuvwxyz":
    VK_MAP[c] = ord(c.upper())
for n in "0123456789":
    VK_MAP[n] = ord(n)


def parse_hotkey_string(hotkey_str: str) -> tuple[int, int]:
    """Parse une chaîne type '<ctrl>+<alt>+d' ou 'ctrl+alt+w' ou 'f8' en (modifiers, vk_code)."""
    clean_str = hotkey_str.lower().replace("<", "").replace(">", "").strip()
    parts = [p.strip() for p in clean_str.split("+")]

    mods = MOD_NOREPEAT
    vk = 0

    for part in parts:
        if part in ("ctrl", "control"):
            mods |= MOD_CONTROL
        elif part == "alt":
            mods |= MOD_ALT
        elif part == "shift":
            mods |= MOD_SHIFT
        elif part in ("win", "windows"):
            mods |= MOD_WIN
        elif part in VK_MAP:
            vk = VK_MAP[part]
        elif len(part) == 1:
            vk = ord(part.upper())
        else:
            logger.warning("Touche inconnue : %s", part)

    return mods, vk


class Win32GlobalHotKey:
    """Écouteur de raccourcis globaux basé sur RegisterHotKey de l'API Windows."""

    def __init__(self, callback: Callable[[], None]) -> None:
        self.callback = callback
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self._is_running = False
        self._registered_ids: list[int] = []

    def register(self, hotkey_id: int, hotkey_str: str) -> bool:
        """Enregistre un raccourci global auprès du noyau Windows."""
        mods, vk = parse_hotkey_string(hotkey_str)
        if vk == 0:
            logger.error("Impossible d'enregistrer le raccourci invalide : %s", hotkey_str)
            return False

        res = self.user32.RegisterHotKey(None, hotkey_id, mods, vk)
        if res:
            logger.info("Raccourci Win32 enregistré : '%s' (ID: %d)", hotkey_str, hotkey_id)
            self._registered_ids.append(hotkey_id)
            return True
        else:
            err = self.kernel32.GetLastError()
            logger.warning("Échec de l'enregistrement du raccourci '%s' (Erreur Win32 : %d)", hotkey_str, err)
            return False

    def listen_loop(self) -> None:
        """Boucle de messages Windows traitant les événements WM_HOTKEY."""
        self._is_running = True
        msg = ctypes.wintypes.MSG()
        logger.info("Boucle de messages Win32 active.")

        try:
            while self._is_running:
                # GetMessage bloque efficacement sans consommer de CPU
                res = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if not self._is_running:
                    break

                if res == -1:
                    logger.error("Erreur GetMessageW : %d", self.kernel32.GetLastError())
                    time.sleep(0.05)
                    continue

                if res == 0:
                    # Message WM_QUIT ignoré pour maintenir le service actif
                    logger.debug("Message WM_QUIT reçu, maintien de la boucle actif.")
                    continue

                if msg.message == WM_HOTKEY:
                    logger.info("Événement WM_HOTKEY détecté (ID: %d) !", msg.wParam)
                    try:
                        self.callback()
                    except Exception as err:
                        logger.exception("Erreur dans le callback de dictée : %s", err)

                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as err:
            logger.exception("Erreur inattendue dans la boucle Win32 : %s", err)
        finally:
            self.unregister_all()

    def unregister_all(self) -> None:
        """Désenregistre tous les raccourcis."""
        for hid in self._registered_ids:
            self.user32.UnregisterHotKey(None, hid)
        self._registered_ids.clear()
        logger.info("Tous les raccourcis Win32 ont été libérés.")

    def stop(self) -> None:
        """Arrête la boucle d'écoute."""
        self._is_running = False
        self.user32.PostQuitMessage(0)
