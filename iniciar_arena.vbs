Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Caminho do projeto
pasta = "G:\Meu Drive\ALLAN RA" & ChrW(205) & "ZES\Ra" & ChrW(237) & "zes Replay"

' Caminho do Python
python = "C:\Users\allan\AppData\Local\Programs\Python\Python313\python.exe"

' Aguarda o Google Drive ficar disponível
tentativas = 0

Do While Not FSO.FolderExists(pasta)

    WScript.Sleep 5000
    tentativas = tentativas + 1

    If tentativas >= 24 Then
        MsgBox "O Google Drive demorou demais para carregar." & vbCrLf & _
               "O sistema será iniciado manualmente quando o Drive estiver disponível."
        WScript.Quit
    End If

Loop

' Aguarda mais 5 segundos para garantir que o Drive terminou de carregar
WScript.Sleep 5000

' Inicia o Flask
comando = "cmd /c cd /d """ & pasta & """ && """ & python & """ app.py"

WshShell.Run comando, 0, False