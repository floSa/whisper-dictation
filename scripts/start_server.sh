#!/usr/bin/env bash
# Démarre le serveur Whisper partagé
set -euo pipefail
cd "$(dirname "$0")/../"

# Modèle conservé en VRAM GPU en permanence (zéro déchargement) pour transcription instantanée
export WHISPER_TTL=0

if curl -fsS -o /dev/null "http://localhost:8000/health" 2>/dev/null; then
  echo "[whisper-dictation] Le serveur Whisper est déjà actif sur http://localhost:8000/v1"
  exit 0
fi

if command -v docker >/dev/null 2>&1; then
  echo "[whisper-dictation] Démarrage du conteneur watch-speaches..."
  docker start watch-speaches || /home/florian/mes_projets/claude-skills/local-whisper/speaches-up.sh
else
  echo "[whisper-dictation] ERREUR : Docker introuvable." >&2
  exit 1
fi
