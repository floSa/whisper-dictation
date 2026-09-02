Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\FLORIAN\Documents\_Documents\Codes_Projes_Dev\whisper-dictation"

' 1. Reveil de WSL et demarrage du conteneur Whisper GPU
WshShell.Run "wsl.exe -d Ubuntu-24.04 -- bash /home/florian/mes_projets/whisper-dictation/scripts/start_server.sh", 0, False

' 2. Lancement du client silencieux de dictee (100% invisible)
cmd_client = Chr(34) & "C:\Users\FLORIAN\Documents\_Documents\Codes_Projes_Dev\whisper-dictation\.venv\Scripts\pythonw.exe" & Chr(34) & " -m whisper_dictation.main run"
WshShell.Run cmd_client, 0, False
Set WshShell = Nothing
