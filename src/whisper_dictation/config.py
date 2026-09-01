"""Configuration du client de dictée vocale."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs chargés depuis l'environnement ou .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    whisper_base_url: str = Field(
        default="http://localhost:8000/v1",
        description="URL de base de l'API Whisper (compatible OpenAI).",
    )
    whisper_model: str = Field(
        default="Systran/faster-whisper-large-v3",
        description="Identifiant du modèle Whisper chargé sur le serveur.",
    )
    whisper_language: str = Field(
        default="fr",
        description="Code langue pour la transcription (ex: fr, en).",
    )
    dictation_hotkey: str = Field(
        default="<f8>",
        description="Raccourci clavier global (syntaxe pynput, ex: <f8>, <ctrl>+<alt>+<space>).",
    )
    dictation_mode: str = Field(
        default="toggle",
        description="Mode de capture : 'toggle' (appui/réappui) ou 'push_to_talk' (maintenir).",
    )
    audio_feedback: bool = Field(
        default=True,
        description="Activer les bips sonores de confirmation (début/fin/erreur).",
    )
    initial_prompt: str = Field(
        default=(
            "Docker, API, GPU, CUDA, CI/CD, PR, WSL, LLM, Python, PyTest, Git, "
            "TypeScript, Linux, Kubernetes, VS Code, CTranslate2, Speaches"
        ),
        description="Prompt initial guidant le modèle sur le vocabulaire technique.",
    )
    sample_rate: int = Field(
        default=16000,
        description="Fréquence d'échantillonnage audio (16 kHz optimal pour Whisper).",
    )
    paste_delay_ms: int = Field(
        default=100,
        description="Délai en millisecondes avant la simulation de frappe de collage.",
    )


settings = Settings()
