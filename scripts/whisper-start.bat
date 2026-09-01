@echo off
echo [Whisper] Demarrage du serveur Whisper...
wsl -d Ubuntu-24.04 -- bash -c "/home/florian/mes_projets/whisper-dictation/scripts/start_server.sh"
echo [Whisper] Pret.
pause
