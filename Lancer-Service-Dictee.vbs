Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\FLORIAN\Documents\_Documents\Codes_Projes_Dev\whisper-dictation"
WshShell.Run """C:\Users\FLORIAN\Documents\_Documents\Codes_Projes_Dev\whisper-dictation\.venv\Scripts\pythonw.exe"" -m whisper_dictation.main run", 0, False
Set WshShell = Nothing
