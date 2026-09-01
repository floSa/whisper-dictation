"""Tests de l'injecteur de texte."""

from unittest.mock import MagicMock, patch
from whisper_dictation.injector import TextInjector


@patch("whisper_dictation.injector.pyperclip.copy")
def test_injector_copy(mock_copy: MagicMock) -> None:
    """Vérifie la copie du texte dans le presse-papier."""
    injector = TextInjector(paste_delay_ms=0)
    injector.paste_text("Bonjour le monde")
    mock_copy.assert_called_once_with("Bonjour le monde")


@patch("whisper_dictation.injector.pyperclip.copy")
def test_injector_empty_text(mock_copy: MagicMock) -> None:
    """Vérifie qu'un texte vide n'est pas copié."""
    injector = TextInjector(paste_delay_ms=0)
    injector.paste_text("")
    mock_copy.assert_not_called()
