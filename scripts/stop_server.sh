#!/usr/bin/env bash
# Arrête le serveur Whisper pour libérer 100% de la VRAM (jeux / gros LLM)
set -euo pipefail
echo "[whisper-dictation] Arrêt du conteneur Whisper pour libérer la mémoire GPU..."
if command -v docker >/dev/null 2>&1; then
  docker stop watch-speaches 2>/dev/null || true
  echo "[whisper-dictation] VRAM GPU 100% libérée."
else
  echo "[whisper-dictation] ERREUR : Docker introuvable." >&2
  exit 1
fi
