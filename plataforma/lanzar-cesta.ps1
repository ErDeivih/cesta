#Requires -Version 5.1
<#
  lanzar-cesta.ps1 - el trabajo real de Cesta.cmd (doble clic, sin ventanas).

  Lo lanza plataforma\lanzar-cesta.vbs (wscript, ventana oculta), que a su vez
  lo dispara Cesta.cmd. Este script es el unico que hace cosas:

    1. Si la app ya responde en /api/salud: no toca nada, abre el navegador y sale.
    2. Si el motor de Docker no responde: arranca Docker Desktop y espera (tope 120 s).
    3. docker compose up -d en plataforma (con --build solo si falta la imagen cesta-api).
    4. Espera a http://127.0.0.1:8080/api/salud (tope 60 s) y abre http://localhost:8080.

  Todo se apunta en data\arranque-cesta.log con fecha y resultado. No mata procesos,
  no toca otros proyectos de Docker, no lanza la recoleccion (eso es ejecutar.bat a
  las 06:00) y no escribe fuera de su carpeta salvo el log.

  Uso:  powershell.exe -NoProfile -ExecutionPolicy Bypass -File plataforma\lanzar-cesta.ps1
        (normalmente no se llama a mano: se hace doble clic en Cesta.cmd)

  Parametros:
    -SinNavegador   no abre el navegador (solo para pruebas del lanzador).
#>
[CmdletBinding()]
param(
    [switch]$SinNavegador
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$Raiz         = Split-Path -Parent $PSScriptRoot
$Plataforma   = Join-Path $Raiz 'plataforma'
$CarpetaDatos = Join-Path $Raiz 'data'
$RutaLog      = Join-Path $CarpetaDatos 'arranque-cesta.log'
$UrlApp       = 'http://localhost:8080'
$UrlSalud     = 'http://127.0.0.1:8080/api/salud'
$Inicio       = Get-Date
$Resultado    = 'FALLO'
$Codigo       = 1
$tengoMutex   = $false
$mutex        = $null

# ---------------------------------------------------------------------------
# Log: una linea por suceso, con fecha. Nunca rompe el arranque si falla.
# ---------------------------------------------------------------------------
# Cola de lineas pendientes. Si otro proceso tiene el log abierto (por ejemplo
# alguien lo esta mirando con Get-Content), Add-Content falla y la linea se
# perderia; medido: sin proteccion se pierden lineas bajo lectura intensa. Con
# la cola, la linea se queda en memoria y se escribe en la siguiente llamada y,
# como ultimo recurso, en Volcar-LogFinal antes de salir.
$script:LogPendiente = New-Object System.Collections.ArrayList

function Escribir-Una-Linea {
    param([string]$Linea)
    try {
        if (-not (Test-Path -LiteralPath $CarpetaDatos)) {
            New-Item -ItemType Directory -Path $CarpetaDatos -Force | Out-Null
        }
        Add-Content -LiteralPath $RutaLog -Value $Linea -Encoding UTF8
        return $true
    } catch {
        return $false
    }
}

function Volcar-Log {
    # Escribe en orden las pendientes y para en la primera que falle, para no
    # desordenar el log.
    $escritas = 0
    while ($escritas -lt $script:LogPendiente.Count) {
        if (Escribir-Una-Linea $script:LogPendiente[$escritas]) { $escritas++ } else { break }
    }
    if ($escritas -gt 0) { $script:LogPendiente.RemoveRange(0, $escritas) }
}

function Volcar-LogFinal {
    # Ultimo intento antes de salir: hasta 15 s con reintentos, para no perder
    # lineas si el fichero estaba abierto mientras el lanzador trabajaba.
    $t0 = Get-Date
    while ($script:LogPendiente.Count -gt 0 -and ((Get-Date) - $t0).TotalSeconds -lt 15) {
        Volcar-Log
        if ($script:LogPendiente.Count -gt 0) { Start-Sleep -Milliseconds 250 }
    }
}

function Escribir-Log {
    param([Parameter(Mandatory)][string]$Texto)
    $linea = '{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Texto
    [void]$script:LogPendiente.Add($linea)
    Volcar-Log
}

function Rotar-Log {
    try {
        if (Test-Path -LiteralPath $RutaLog) {
            if ((Get-Item -LiteralPath $RutaLog).Length -gt 512KB) {
                Move-Item -LiteralPath $RutaLog -Destination ($RutaLog + '.1') -Force
            }
        }
    } catch { }
}

# ---------------------------------------------------------------------------
# Ejecuta un programa externo sin ventana, con salida y error a ficheros
# temporales (asi no se mezclan con la consola oculta del lanzador).
# ---------------------------------------------------------------------------
function Invoke-Oculto {
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Argumentos = @(),
        [string]$Directorio = $Plataforma
    )
    $rutaSalida  = [System.IO.Path]::GetTempFileName()
    $rutaErrores = [System.IO.Path]::GetTempFileName()
    try {
        # Los argumentos con espacios van entre comillas en la linea de comandos.
        $partes = @()
        foreach ($a in $Argumentos) {
            if ($a -match '\s' -and $a -notmatch '^"') { $partes += ('"' + $a + '"') } else { $partes += $a }
        }
        $linea = $partes -join ' '
        $p = Start-Process -FilePath $Exe -ArgumentList $linea -WorkingDirectory $Directorio `
                           -NoNewWindow -Wait -PassThru `
                           -RedirectStandardOutput $rutaSalida -RedirectStandardError $rutaErrores
        $texto = @()
        foreach ($f in @($rutaSalida, $rutaErrores)) {
            if (Test-Path -LiteralPath $f) {
                foreach ($l in @(Get-Content -LiteralPath $f -ErrorAction SilentlyContinue)) {
                    if ("$l".Trim()) { $texto += "$l".Trim() }
                }
            }
        }
        [pscustomobject]@{ Codigo = [int]$p.ExitCode; Texto = $texto }
    } finally {
        Remove-Item -LiteralPath $rutaSalida, $rutaErrores -Force -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Piezas del arranque
# ---------------------------------------------------------------------------
function Buscar-Docker {
    try {
        $cmd = Get-Command docker.exe -ErrorAction Stop
        return $cmd.Source
    } catch {
        return $null
    }
}

function Motor-Docker {
    # Devuelve la version del motor, o $null si no responde.
    param([Parameter(Mandatory)][string]$RutaDocker)
    try {
        $r = Invoke-Oculto -Exe $RutaDocker -Argumentos @('version', '--format', '{{.Server.Version}}')
        if ($r.Codigo -eq 0) {
            $v = @($r.Texto | Where-Object { $_ -match '^\d+\.\d+' }) | Select-Object -First 1
            if ($v) { return "$v".Trim() }
        }
    } catch { }
    return $null
}

function Buscar-DockerDesktop {
    $candidatos = @()
    if ($env:ProgramFiles)          { $candidatos += (Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe') }
    if (${env:ProgramFiles(x86)})   { $candidatos += (Join-Path ${env:ProgramFiles(x86)} 'Docker\Docker\Docker Desktop.exe') }
    if ($env:LOCALAPPDATA)          { $candidatos += (Join-Path $env:LOCALAPPDATA 'Docker\Docker Desktop.exe') }
    foreach ($c in $candidatos) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return $null
}

function Probar-Salud {
    try {
        $r = Invoke-WebRequest -Uri $UrlSalud -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200 -and $r.Content) { return "$($r.Content)".Trim() }
    } catch { }
    return $null
}

function Abrir-Navegador {
    if ($SinNavegador) {
        Escribir-Log '[ok] navegador: no se abre (-SinNavegador)'
        return
    }
    try {
        Start-Process -FilePath $UrlApp | Out-Null
        Escribir-Log ("[ok] navegador abierto en {0}" -f $UrlApp)
    } catch {
        Escribir-Log ("[aviso] no pude abrir el navegador: {0}" -f $_.Exception.Message)
    }
}

function Esperar-Salud {
    param([int]$Segundos = 60)
    $t0 = Get-Date
    while (((Get-Date) - $t0).TotalSeconds -lt $Segundos) {
        $salud = Probar-Salud
        if ($salud) { return [pscustomobject]@{ Cuerpo = $salud; Segundos = ((Get-Date) - $t0).TotalSeconds } }
        Start-Sleep -Seconds 2
    }
    return $null
}

function Invoke-CestaArranque {
    # 1. El atajo idempotente: si ya esta arriba, solo abrir el navegador.
    $salud = Probar-Salud
    if ($salud) {
        Escribir-Log ("[ok] la app ya estaba arriba: {0}" -f $salud)
        Abrir-Navegador
        return 'OK'
    }

    # 2. Motor de Docker.
    $rutaDocker = Buscar-Docker
    if (-not $rutaDocker) {
        throw 'no encuentro docker.exe en el PATH: falta Docker Desktop'
    }
    $version = Motor-Docker -RutaDocker $rutaDocker
    if (-not $version) {
        Escribir-Log '[aviso] el motor de Docker no responde'
        $exeDockerDesktop = Buscar-DockerDesktop
        if (-not $exeDockerDesktop) {
            throw 'el motor de Docker no responde y no encuentro Docker Desktop instalado; arrancalo a mano'
        }
        Escribir-Log ("[paso] arrancando Docker Desktop: {0}" -f $exeDockerDesktop)
        Start-Process -FilePath $exeDockerDesktop | Out-Null
        $espera = 120
        $t0 = Get-Date
        do {
            Start-Sleep -Seconds 3
            $version = Motor-Docker -RutaDocker $rutaDocker
        } while (-not $version -and ((Get-Date) - $t0).TotalSeconds -lt $espera)
        if (-not $version) {
            throw ("el motor de Docker no respondio en {0} s; abre Docker Desktop y vuelve a intentarlo" -f $espera)
        }
        Escribir-Log ("[ok] motor arriba: Docker {0} (tras {1:N0} s)" -f $version, ((Get-Date) - $t0).TotalSeconds)
    } else {
        Escribir-Log ("[ok] motor de Docker ya estaba arriba: {0}" -f $version)
    }

    # 3. docker compose up -d (sin --build salvo que falte la imagen).
    if (-not (Test-Path -LiteralPath (Join-Path $Plataforma 'docker-compose.yml'))) {
        throw 'no encuentro plataforma\docker-compose.yml; el repo esta incompleto'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Plataforma '.env'))) {
        throw 'falta plataforma\.env: copia .env.ejemplo a .env y pon una CESTA_CLAVE_DB larga'
    }

    $argumentos = @('compose', 'up', '-d')
    $imagen = Invoke-Oculto -Exe $rutaDocker -Argumentos @('image', 'inspect', 'cesta-api')
    if ($imagen.Codigo -ne 0) {
        $argumentos += '--build'
        Escribir-Log '[aviso] falta la imagen cesta-api: reconstruyo (--build). Tarda unos minutos la primera vez'
    }
    Escribir-Log ("[paso] docker compose up -d{0}" -f $(if ($argumentos -contains '--build') { ' --build' } else { '' }))
    $compose = Invoke-Oculto -Exe $rutaDocker -Argumentos $argumentos -Directorio $Plataforma
    foreach ($l in @($compose.Texto)) { Escribir-Log ("  compose: {0}" -f $l) }
    if ($compose.Codigo -ne 0) {
        throw ("docker compose up -d fallo con codigo {0}: mira el log y 'plataforma\arrancar.bat logs'" -f $compose.Codigo)
    }
    Escribir-Log '[ok] docker compose up -d: codigo 0'

    $estado = Invoke-Oculto -Exe $rutaDocker -Argumentos @('compose', 'ps', '--format', '{{.Name}}|{{.Status}}') -Directorio $Plataforma
    if ($estado.Codigo -eq 0) {
        foreach ($l in @($estado.Texto)) { Escribir-Log ("  estado: {0}" -f $l) }
    }

    # 4. Esperar a que la app responda y abrir el navegador.
    $listo = Esperar-Salud -Segundos 60
    if (-not $listo) {
        throw 'la app no respondio en /api/salud en 60 s: docker compose ps, docker compose logs --tail 80 api'
    }
    Escribir-Log ("[ok] /api/salud responde tras {0:N0} s: {1}" -f $listo.Segundos, $listo.Cuerpo)
    try {
        $raiz = Invoke-WebRequest -Uri $UrlApp -UseBasicParsing -TimeoutSec 10
        Escribir-Log ("[ok] {0} -> {1}" -f $UrlApp, $raiz.StatusCode)
    } catch {
        Escribir-Log ("[aviso] {0} no responde: {1}" -f $UrlApp, $_.Exception.Message)
    }
    Abrir-Navegador
    return 'OK'
}

# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------
try {
    Rotar-Log

    # Evita dos arranques a la vez (dos dobles clics seguidos).
    try {
        $mutex = New-Object System.Threading.Mutex($false, 'Local\CestaArranque')
        try {
            $tengoMutex = $mutex.WaitOne(0)
        } catch [System.Threading.AbandonedMutexException] {
            $tengoMutex = $true
        }
    } catch {
        # Sin mutex se sigue: peor seria no arrancar.
        $tengoMutex = $true
    }

    if (-not $tengoMutex) {
        Escribir-Log '[aviso] ya hay un arranque de Cesta en curso: no lanzo otro'
        $Resultado = 'YA-EN-CURSO'
        $Codigo = 0
    } else {
        Escribir-Log ("[inicio] arranque de Cesta (usuario {0}, powershell {1}, pid {2})" -f $env:USERNAME, $PSVersionTable.PSVersion.ToString(), $PID)
        $Resultado = Invoke-CestaArranque
        $Codigo = 0
    }
} catch {
    $Resultado = 'FALLO'
    $Codigo = 1
    Escribir-Log ("[fallo] {0}" -f $_.Exception.Message)
} finally {
    if ($tengoMutex -and $mutex) {
        try { $mutex.ReleaseMutex() } catch { }
    }
    if ($mutex) { try { $mutex.Dispose() } catch { } }
    Escribir-Log ("[fin] resultado={0} en {1:N1} s" -f $Resultado, ((Get-Date) - $Inicio).TotalSeconds)
    Volcar-LogFinal
}

exit $Codigo
