@echo off
REM ============================================================================
REM  Cesta: la recoleccion diaria entera en un solo comando.
REM
REM  Hace, por este orden:
REM    1. las cinco cadenas (carrefour, dia, mercadona, aldi, alcampo)
REM    2. las fichas maestras nuevas del dia (EAN, ingredientes, marca)
REM    3. el pipeline    raw -> bronze -> silver -> gold
REM    4. el emparejador entre cadenas y las calidades A/B/C
REM    5. el resumen de lo que ha quedado en disco
REM
REM  UNA VEZ AL DIA. Si ya se hizo hoy, sale enseguida sin tocar nada: asi la
REM  tarea puede dispararse al encender el ordenador y en cada inicio de sesion
REM  sin repetir noventa minutos de trabajo. La marca solo se escribe si el dia
REM  ha ido bien, de modo que un dia fallido se reintenta al siguiente arranque
REM  (y como el crudo ya esta en cache, ese reintento cuesta minutos, no horas).
REM
REM    ejecutar.bat            una vez al dia
REM    ejecutar.bat --forzar   otra vez hoy, a proposito
REM
REM  Dar de alta la tarea: registrar-tarea.ps1 (PowerShell como administrador)
REM ============================================================================
setlocal enabledelayedexpansion
set PYTHONUTF8=1
REM Sin esto Python guarda la salida en un bufer y el log se queda vacio horas:
REM la manana del 8 sep la ejecucion llevaba una hora corriendo y el fichero solo
REM tenia la linea de la fecha. Un log que no se puede leer mientras pasa no sirve.
set PYTHONUNBUFFERED=1
cd /d "%~dp0"

for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set HOY=%%d
set MARCA=data\ultima_ejecucion.txt

if /i not "%~1"=="--forzar" (
  if exist "%MARCA%" (
    set /p ULTIMA=<"%MARCA%"
    if "!ULTIMA!"=="!HOY!" (
      echo Cesta: la recoleccion de !HOY! ya esta hecha. Nada que hacer.
      echo   ^(para repetirla:  ejecutar.bat --forzar^)
      exit /b 0
    )
  )
)

if not exist ".venv" (
  echo Primera vez: instalando dependencias...
  uv sync
)

echo. >> "data\ejecuciones.log"
echo ############ !HOY! %time% ############ >> "data\ejecuciones.log"
uv run python -m projects.cesta.run >> "data\ejecuciones.log" 2>&1
set CODIGO=!errorlevel!

REM La marca solo se pone si el dia ha ido bien. Un dia a medias se reintenta.
if !CODIGO!==0 (
  echo !HOY!> "%MARCA%"
) else (
  echo Cesta: la ejecucion de !HOY! termino con fallos; se reintentara en el proximo arranque.
)

powershell -NoProfile -Command "Get-Content 'data\ejecuciones.log' -Tail 24"
exit /b !CODIGO!
