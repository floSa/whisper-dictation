"""Client HTTP pour l'API Whisper (compatible OpenAI)."""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class WhisperError(Exception):
    """Exception levée en cas d'erreur de communication avec Whisper."""


class WhisperServerUnavailable(WhisperError):
    """Exception levée quand le serveur Whisper est éteint ou inaccessible."""


class WhisperClient:
    """Client d'inférence HTTP pour le serveur Whisper local."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
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

    def check_health(self) -> bool:
        """Vérifie si le serveur Whisper répond sainement."""
        # Test sur /health (Speaches) ou sur /v1/models
        health_url = self.base_url.replace("/v1", "") + "/health"
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(health_url)
                if resp.status_code == 200:
                    return True
                # Fallback sur /v1/models
                models_resp = client.get(f"{self.base_url}/models")
                return models_resp.status_code == 200
        except Exception as err:
            logger.debug("Serveur Whisper injoignable : %s", err)
            return False

    def transcribe(self, wav_bytes: bytes) -> str:
        """Envoie l'audio WAV au serveur et retourne le texte transcrit."""
        if not self.check_health():
            raise WhisperServerUnavailable(
                f"Le serveur Whisper est injoignable sur {self.base_url}. "
                "Assurez-vous qu'il est démarré via whisper-start.bat ou ./scripts/start_server.sh"
            )

        transcribe_url = f"{self.base_url}/audio/transcriptions"
        files = {
            "file": ("dictation.wav", wav_bytes, "audio/wav"),
        }
        data = {
            "model": self.model,
            "language": self.language,
            "response_format": "json",
        }
        if self.initial_prompt:
            data["prompt"] = self.initial_prompt

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(transcribe_url, files=files, data=data)
                response.raise_for_status()
                json_data = response.json()
                text = json_data.get("text", "").strip()
                logger.info("Transcription reçue : %s", text)
                return text
        except httpx.HTTPStatusError as err:
            logger.error("Erreur HTTP de transcription : %s (corps: %s)", err, err.response.text)
            raise WhisperError(f"Erreur HTTP {err.response.status_code}: {err.response.text}") from err
        except Exception as err:
            logger.error("Erreur inattendue de transcription : %s", err)
            raise WhisperError(f"Échec de transcription : {err}") from err
