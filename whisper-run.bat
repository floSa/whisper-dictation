@echo off
title Whisper Dictation (GPU Large-v3)
cd /d %~dp0
echo =========================================================
echo   Lancement de Whisper Dictation sur votre GPU...
echo =========================================================
.\.venv\Scripts\python.exe -m whisper_dictation.main run
pause
