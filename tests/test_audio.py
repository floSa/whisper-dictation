"""Tests du module audio."""

from whisper_dictation.audio import AudioRecorder


def test_audio_recorder_initial_state() -> None:
    """Vérifie l'état initial de l'enregistreur."""
    rec = AudioRecorder(sample_rate=16000)
    assert rec.is_recording is False
    assert rec.stop() is None
