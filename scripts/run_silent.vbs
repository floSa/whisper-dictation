' Lanceur silencieux Windows sans fenetre noire
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "uv run whisper-dictation run", 0, False
Set WshShell = Nothing
