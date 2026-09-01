"""Tests de la configuration."""

from whisper_dictation.config import Settings


def test_default_settings() -> None:
    """Vérifie les valeurs par défaut de la configuration."""
    s = Settings()
    assert "localhost" in s.whisper_base_url
    assert "large-v3" in s.whisper_model
    assert s.whisper_language == "fr"
    assert s.sample_rate == 16000
    assert s.dictation_hotkey == "<f8>"
