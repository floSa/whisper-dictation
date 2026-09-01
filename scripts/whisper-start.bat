@echo off
echo [Whisper] Demarrage du serveur Whisper GPU...
wsl -d Ubuntu-24.04 -- bash -c "/home/florian/mes_projets/whisper-dictation/scripts/start_server.sh"
echo [Whisper] Lancement du client silencieux en arriere-plan...
wscript.exe "%~dp0run_silent.vbs"
echo [Whisper] Pret ! Raccourci Ctrl+Alt+D actif en arriere-plan.
timeout /t 2 >nul
