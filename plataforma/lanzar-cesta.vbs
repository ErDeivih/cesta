Option Explicit
' lanzar-cesta.vbs - arranca el lanzador de Cesta con la ventana oculta (2026-11-09).
'
' Lo llama Cesta.cmd al hacer doble clic. No hace el trabajo: solo ejecuta
' powershell.exe con el script lanzar-cesta.ps1 y espera a que termine.
' Asi no queda ninguna consola abierta (estilo de ventana 0 = oculta).
'
' Para el registro de lo que pasa: data\arranque-cesta.log

Dim fso, shell, carpeta, ps1, ps, comando, codigo

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

carpeta = fso.GetParentFolderName(WScript.ScriptFullName)
ps1 = fso.BuildPath(carpeta, "lanzar-cesta.ps1")
If Not fso.FileExists(ps1) Then WScript.Quit 3

ps = shell.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
comando = """" & ps & """ -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """"

' 0 = ventana oculta; True = esperar (wscript vive lo mismo que el trabajo).
codigo = shell.Run(comando, 0, True)
WScript.Quit codigo
