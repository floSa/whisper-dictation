"""Tests du client HTTP Whisper."""

from unittest.mock import MagicMock, patch
import pytest
from whisper_dictation.client import WhisperClient, WhisperServerUnavailable


def test_client_health_offline() -> None:
    """Vérifie le comportement quand le serveur est injoignable."""
    client = WhisperClient(base_url="http://127.0.0.1:9999/v1")
    assert client.check_health() is False


def test_transcribe_raises_when_offline() -> None:
    """Vérifie qu'une exception WhisperServerUnavailable est levée quand le serveur est éteint."""
    client = WhisperClient(base_url="http://127.0.0.1:9999/v1")
    with pytest.raises(WhisperServerUnavailable):
        client.transcribe(b"fake_wav_data")


@patch("httpx.Client.get")
@patch("httpx.Client.post")
def test_transcribe_success(mock_post: MagicMock, mock_get: MagicMock) -> None:
    """Vérifie la réception correcte d'une transcription simulée."""
    mock_get.return_value = MagicMock(status_code=200)
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"text": "Ceci est un test de transcription vocale."},
    )

    client = WhisperClient(base_url="http://localhost:8000/v1")
    res = client.transcribe(b"dummy_wav")
    assert res == "Ceci est un test de transcription vocale."
