@echo off
echo [Whisper] Arret du serveur Whisper et liberation de la VRAM GPU...
wsl -d Ubuntu-24.04 -- bash -c "/home/florian/mes_projets/whisper-dictation/scripts/stop_server.sh"
echo [Whisper] VRAM GPU 100%% liberee.
pause
