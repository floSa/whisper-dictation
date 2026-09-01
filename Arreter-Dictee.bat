@echo off
taskkill /F /IM pythonw.exe 2>nul
wsl -d Ubuntu-24.04 -- bash -c "/home/florian/mes_projets/whisper-dictation/scripts/stop_server.sh"
echo [Whisper] Dictee et serveur arretes. VRAM 100% liberee.
timeout /t 2 >nul
