@echo off
title Whisper Dictation (Large-v3 GPU)
echo Demarrage du serveur Whisper GPU...
wsl -d Ubuntu-24.04 -- bash -c "/home/florian/mes_projets/whisper-dictation/scripts/start_server.sh"
echo Lancement du service de dictee (minimise dans la barre des taches)...
start /min "Whisper Dictation" "C:\Users\FLORIAN\Documents\_Documents\Codes_Projes_Dev\whisper-dictation\.venv\Scripts\python.exe" -m whisper_dictation.main run
echo Pret ! Le service tourne minimise dans votre barre des taches.
timeout /t 2 >nul
