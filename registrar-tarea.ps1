# Da de alta la recoleccion diaria en el Programador de tareas de Windows.
# Ejecutar UNA VEZ, en PowerShell como ADMINISTRADOR:
#     powershell -ExecutionPolicy Bypass -File F:\Proyectos\cesta\registrar-tarea.ps1
#
# Como queda configurada, y por que:
#
#   - Se dispara a las 06:00 todos los dias, AL ENCENDER el ordenador y en cada
#     inicio de sesion. Tres disparadores a proposito: el ordenador no siempre
#     esta encendido a las seis, y lo que importa es que el dia que se encienda
#     se haga.
#   - StartWhenAvailable: si el ordenador estaba apagado a las 06:00, Windows
#     lanza la tarea en cuanto puede en vez de saltarse el dia.
#   - Repetirse no cuesta nada: ejecutar.bat lleva su propia marca diaria y sale
#     al instante si el trabajo de hoy ya esta hecho.
#   - Corre con la sesion iniciada (no "aunque el usuario no haya iniciado
#     sesion"): el reto de AWS WAF de Alcampo se resuelve con un navegador
#     VISIBLE, y sin escritorio interactivo falla mucho mas.
#   - No se ejecuta si el portatil va con bateria y no se para si se desenchufa
#     a medias: noventa minutos de red con la bateria justa no compensan.

$ErrorActionPreference = "Stop"
$carpeta = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat     = Join-Path $carpeta "ejecutar.bat"
$nombre  = "Cesta diaria"

if (-not (Test-Path $bat)) { throw "no encuentro $bat" }

$accion = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $carpeta

$disparadores = @(
    (New-ScheduledTaskTrigger -Daily -At 6:00am),
    (New-ScheduledTaskTrigger -AtStartup),
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME)
)
# Un margen tras arrancar: si se lanza mientras Windows todavia esta levantando
# servicios y red, la primera peticion falla y arrastra a toda la ejecucion.
$disparadores[1].Delay = "PT3M"
$disparadores[2].Delay = "PT2M"

$ajustes = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparadores `
    -Settings $ajustes -Principal $principal -Force | Out-Null

Write-Host "Tarea '$nombre' registrada." -ForegroundColor Green
Write-Host "  comprobar:  Get-ScheduledTask -TaskName '$nombre' | Get-ScheduledTaskInfo"
Write-Host "  lanzar ya:  Start-ScheduledTask -TaskName '$nombre'"
Write-Host "  quitar:     Unregister-ScheduledTask -TaskName '$nombre' -Confirm:`$false"
