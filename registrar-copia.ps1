# Da de alta la COPIA DIARIA de la base de casa en el Programador de tareas de Windows.
#
# Ejecutar UNA VEZ, en PowerShell como ADMINISTRADOR:
#     powershell -ExecutionPolicy Bypass -File F:\aprendizaje\scrap\registrar-copia.ps1
#
# **Y NO se ejecuta solo.** *Este fichero no se lanza al abrirlo: hay que quererlo.* **Crear una tarea
# programada es un cambio en el sistema, y no se hace por cuenta propia.**
#
# Como queda configurada, y por que cada cosa:
#
#   - **A las 03:30**, y no a las 06:00: *la recoleccion diaria arranca a las seis y dura hasta cuatro
#     horas.* **Una copia a las seis de la mañana copiaria una base a medio escribir** -- *y ademas
#     competiria por el disco con el scraping.* *A las 03:30 no hay nadie trabajando.*
#   - **`StartWhenAvailable`**: *si el ordenador estaba apagado a las 03:30, Windows la lanza en cuanto
#     pueda en vez de saltarse el dia.* **Y con las copias, saltarse un dia es exactamente lo que no se
#     quiere.**
#   - **`DontStopIfGoingOnBatteries`**: *una copia de 340 KB tarda menos de un segundo.* **Pararla por
#     bateria no ahorra nada y deja un dia sin copia.**
#   - **`MultipleInstances IgnoreNew`**: *si la anterior sigue corriendo, no se lanza otra.* **Dos copias
#     a la vez escribiendo el mismo fichero no tiene ningun sentido.**
#   - **`ExecutionTimeLimit` de 5 minutos**: *`pg_dump` de esta base tarda menos de un segundo.* **Si
#     tarda cinco minutos, algo va mal y hay que matarlo**, no dejarlo colgado toda la noche.
#   - **Sin `RunLevel Highest`**: *no hace falta.* **Lee con `docker exec` y escribe en `data/copias`.**
#     *La tarea de la recoleccion si lo pide, y por otro motivo: alli el WAF de Alcampo necesita un
#     navegador visible.*
#   - **Y la retencion es de 7.** *Una semana de copias diarias: si algo se rompe un viernes, el lunes
#     todavia hay copia del jueves.*
#
# Lo que la tarea NO toca, y es lo que costo 716 usuarios:
#
#   - no toca `facylf-postgres` (el 5433): es de otro encargo;
#   - no toca la base de pruebas (`cesta-prueba-db`, el 5434);
#   - **no borra ningun contenedor**: lee de `cesta-db-1` y escribe un fichero.

$ErrorActionPreference = "Stop"
$carpeta = Split-Path -Parent $MyInvocation.MyCommand.Path
$nombre  = "Cesta copia diaria"

if (-not (Test-Path (Join-Path $carpeta "plataforma\copia_programada.py"))) {
    throw "no encuentro plataforma\copia_programada.py: esto no es la raiz de Cesta"
}

# **Se llama a `uv run python -m`, que es como se corre todo lo demas del proyecto.** *Y `uv` tiene que
# estar en el PATH de la tarea: si no lo esta, la tarea falla y el programador lo dira con su codigo.*
$accion = New-ScheduledTaskAction `
    -Execute "uv" `
    -Argument "run python -m plataforma.copia_programada --retencion 7" `
    -WorkingDirectory $carpeta

$disparadores = @(
    (New-ScheduledTaskTrigger -Daily -At 3:30am),
    (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME)
)
# *El mismo margen que la recoleccion, y por la misma razon*: si se lanza mientras Windows levanta
# servicios, Docker todavia no responde y la copia diria que el contenedor no esta.
$disparadores[1].Delay = "PT2M"

$ajustes = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive

Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger $disparadores `
    -Settings $ajustes -Principal $principal -Force | Out-Null

Write-Host "Tarea '$nombre' registrada." -ForegroundColor Green
Write-Host "  comprobar:  Get-ScheduledTask -TaskName '$nombre' | Get-ScheduledTaskInfo"
Write-Host "  lanzar ya:  Start-ScheduledTask -TaskName '$nombre'"
Write-Host "  ver las copias:  uv run python -m plataforma.copia_programada --listar"
Write-Host "  quitar:     Unregister-ScheduledTask -TaskName '$nombre' -Confirm:`$false"
Write-Host ""
Write-Host "Y una cosa que hay que decir: esto NO se ha registrado por su cuenta." -ForegroundColor Yellow
Write-Host "  El fichero esta escrito y probado; darlo de alta es una decision." -ForegroundColor Yellow
