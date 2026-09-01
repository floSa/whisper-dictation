"""Capture audio microphone avec sounddevice et encodage WAV en mémoire."""

import io
import logging
import wave
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Enregistreur audio en mémoire utilisant sounddevice."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self._is_recording = False
        self._audio_chunks: list[np.ndarray] = []
        self._stream = None

    @property
    def is_recording(self) -> bool:
        """Indique si un enregistrement est actif."""
        return self._is_recording

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: dict, status: int) -> None:
        """Callback appelé par sounddevice pour chaque paquet audio."""
        if status:
            logger.warning("Statut flux audio : %s", status)
        if self._is_recording:
            self._audio_chunks.append(indata.copy())

    def start(self) -> None:
        """Démarre la capture audio."""
        if self._is_recording:
            logger.warning("Enregistrement déjà en cours.")
            return

        import sounddevice as sd

        self._audio_chunks = []
        self._is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            callback=self._audio_callback,
        )
        self._stream.start()
        logger.debug("Flux audio démarré.")

    def stop(self) -> Optional[bytes]:
        """Arrête la capture et retourne les octets WAV en mémoire."""
        if not self._is_recording:
            logger.warning("Aucun enregistrement actif à arrêter.")
            return None

        self._is_recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._audio_chunks:
            logger.warning("Aucune donnée audio capturée.")
            return None

        # Concaténation des blocs audio
        full_audio = np.concatenate(self._audio_chunks, axis=0)

        # Encodage en fichier WAV pur en mémoire (io.BytesIO)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16 bits = 2 octets
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(full_audio.tobytes())

        buffer.seek(0)
        wav_bytes = buffer.read()
        logger.debug("Audio capturé : %d octets (%d échantillons)", len(wav_bytes), len(full_audio))
        return wav_bytes
