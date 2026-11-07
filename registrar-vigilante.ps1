# Da de alta el VIGILANTE de la ingesta en el Programador de tareas de Windows.
# Ejecutar UNA VEZ, en PowerShell como ADMINISTRADOR si el registro normal falla:
#     powershell -ExecutionPolicy Bypass -File F:\Proyectos\cesta\registrar-vigilante.ps1
#
# Por que esta tarea es aparte de «Cesta diaria»:
#   El vigilante vivia al final de ejecutar.bat. Si el Programador no lanzaba
#   ese .bat, el vigilante tampoco corria y el fallo se quedaba callado. Esta
#   tarea comprueba a las 08:00, 14:00 y 20:00 que la ingesta del dia arranco y
#   publico: si no arranca, se sabe por la mañana, no solo al final del dia.
#
# Disparadores:
#   - Diario a las 08:00, 14:00 y 20:00.
#   - Al iniciar sesion, con 25 minutos de margen: si el PC estaba apagado a
#     las 08:00, se mira al entrar.
#   - StartWhenAvailable: si el PC estaba apagado, Windows recupera la tarea.
#   - MultipleInstances IgnoreNew: dos comprobaciones a la vez no duplican avisos.
#
# Si el registro falla por permisos, ejecutar este mismo archivo como
# administrador una vez; luego la tarea corre con la sesion del usuario, que es
# lo que necesita para ver `data/`.

$ErrorActionPreference = "Stop"
$carpeta = Split-Path -Parent $MyInvocation.MyCommand.Path
$bat = Join-Path $carpeta "ejecutar-vigilante.bat"
$nombre = "Cesta vigilante"

if (-not (Test-Path $bat)) { throw "no encuentro $bat" }

$accion = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $carpeta

$disparadores = @(
    (New-ScheduledTaskTrigger -Daily -At 6:30am),
    (New-ScheduledTaskTrigger -Daily -At 8:00am),
    (New-ScheduledTaskTrigger -Daily -At 2:00pm),
    (New-ScheduledTaskTrigger -Daily -At 8:00pm),
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME)
)
$disparadores[4].Delay = "PT25M"

$ajustes = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparadores `
    -Settings $ajustes -Principal $principal -Force | Out-Null

Write-Host "Tarea '$nombre' registrada." -ForegroundColor Green
Write-Host "  comprobar:  Get-ScheduledTask -TaskName '$nombre' | Get-ScheduledTaskInfo"
Write-Host "  lanzar ya:  Start-ScheduledTask -TaskName '$nombre'"
Write-Host "  quitar:     Unregister-ScheduledTask -TaskName '$nombre' -Confirm:`$false"
