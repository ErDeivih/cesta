@echo off
REM ============================================================================
REM  Cesta: el vigilante de la ingesta, con su PROPIA programacion.
REM
REM  El vigilante no puede depender de `ejecutar.bat`: si el Programador no
REM  lanza la recoleccion, ese .bat nunca llega a llamarlo y el fallo se queda
REM  callado. Esta tarea corre aparte, a las 08:00, 14:00 y 20:00, y contesta a
REM  una sola pregunta: **¿hoy arranco la ingesta y dejo el dato?**
REM
REM  - Antes de las 08:00 no se avisa de que falte: `--margen-hasta 08:00` deja
REM    las ausencias como aviso `en_margen_arranque` (sale 0 con --solo-fallos).
REM  - Un aviso conocido (Alcampo corto por la vara del 17/10) NO hace fallar
REM    el dia: `--solo-fallos` sale 0 y el aviso queda escrito.
REM  - Si la pasada esta en curso, tambien sale 0: aun no se puede decir que
REM    falte.
REM  - Si no hay pasada, o el gold no se publico, sale 1 y se deja el aviso en
REM    data\avisos_ingesta.log y data\INGESTA-DETENIDA.txt, ademas del JSON que
REM    lee el panel. La salida del propio .bat va a data\vigilante.log, no a
REM    data\ejecuciones.log (esa la tiene abierta la recoleccion mientras corre).
REM
REM  La espera de 5 minutos antes de dar el fallo evita el falso positivo del
REM  arranque: cuando Windows recupera una tarea perdida al iniciar sesion, la
REM  recoleccion puede estar arrancando en ese mismo momento.
REM ============================================================================
setlocal enabledelayedexpansion
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1
cd /d "%~dp0"

set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo Cesta: no encuentro %PY% para el vigilante. >> "data\avisos_ingesta.log"
  exit /b 1
)

call :vigila
if !errorlevel! equ 0 goto :bien

REM Si el fallo es de Alcampo y su crudo esta en disco, se reintenta SOLO Alcampo
REM (run.py reutiliza data/raw) y se vuelve a mirar. Si ya hay bronce o no hay
REM crudo, el script no lanza nada. El aviso viejo se borra si la recuperacion va bien.
"%PY%" -m scripts.recuperar_alcampo >> "data\vigilante.log" 2>&1
if !errorlevel! equ 0 (
  call :vigila
  if !errorlevel! equ 0 goto :bien
)

REM Segunda oportunidad: si el ordenador acaba de arrancar, la recoleccion
REM puede estar empezando ahora mismo. Se espera y se vuelve a mirar.
powershell -NoProfile -Command "Start-Sleep -Seconds 300" >nul 2>&1
call :vigila
if !errorlevel! equ 0 goto :bien

echo %date% %time% FALLO: la ingesta de hoy no arranco o no termino bien.>> "data\avisos_ingesta.log"
(
  echo La ingesta de hoy no ha arrancado o no ha terminado bien. Fecha: %date% %time%.
  echo Mira data\avisos_ingesta.json y data\avisos_ingesta.log.
  echo Para relanzarla: ejecutar.bat
) > "data\INGESTA-DETENIDA.txt"
echo Cesta: la ingesta de hoy no arranco o no termino bien. Mira data\avisos_ingesta.json
"%PY%" -m projects.cesta.metricas >nul 2>&1
exit /b 1

:bien
if exist "data\INGESTA-DETENIDA.txt" del "data\INGESTA-DETENIDA.txt" >nul 2>&1
"%PY%" -m projects.cesta.metricas >nul 2>&1
exit /b 0

:vigila
"%PY%" -m scripts.vigilar_ingesta --solo-fallos --margen-hasta 08:00 >> "data\vigilante.log" 2>&1
exit /b !errorlevel!
