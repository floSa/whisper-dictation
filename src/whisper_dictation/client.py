"""Client HTTP pour le serveur Whisper local."""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class WhisperServerUnavailable(Exception):
    """Exception levée lorsque le serveur Whisper est inaccessible."""

    pass


class WhisperClient:
    """Client API Whisper avec pool de connexions réutilisables."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000/v1",
        model: str = "Systran/faster-whisper-large-v3",
        language: str = "fr",
        initial_prompt: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language
        self.initial_prompt = initial_prompt
        self.timeout_seconds = timeout_seconds
        # Session HTTP persistante pour éliminer la latence TCP/TLS
        self._session = httpx.Client(timeout=self.timeout_seconds)

    def check_health(self) -> bool:
        """Vérifie si le serveur Whisper répond sainement."""
        health_url = self.base_url.replace("/v1", "") + "/health"
        try:
            resp = self._session.get(health_url, timeout=2.0)
            if resp.status_code == 200:
                return True
            models_resp = self._session.get(f"{self.base_url}/models", timeout=2.0)
            return models_resp.status_code == 200
        except Exception as err:
            logger.warning("Vérification santé Whisper échouée sur %s : %s", health_url, err)
            return False

    def transcribe(self, wav_bytes: bytes) -> str:
        """Envoie l'audio WAV au serveur et retourne le texte transcrit."""
        transcribe_url = f"{self.base_url}/audio/transcriptions"
        files = {
            "file": ("dictation.wav", wav_bytes, "audio/wav"),
        }
        data = {
            "model": self.model,
            "language": self.language,
            "response_format": "json",
            "vad_filter": "true",
        }
        if self.initial_prompt:
            data["prompt"] = self.initial_prompt

        try:
            resp = self._session.post(transcribe_url, data=data, files=files)
            if resp.status_code != 200:
                logger.error("Réponse API Whisper HTTP %d : %s", resp.status_code, resp.text)
                raise WhisperServerUnavailable(f"Erreur API HTTP {resp.status_code} : {resp.text}")

            result = resp.json()
            return result.get("text", "").strip()
        except httpx.RequestError as err:
            logger.error("Erreur réseau vers le serveur Whisper : %s", err)
            raise WhisperServerUnavailable(f"Serveur Whisper injoignable : {err}") from err

    def close(self) -> None:
        """Ferme la session HTTP."""
        self._session.close()
