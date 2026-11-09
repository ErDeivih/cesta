@echo off
REM ============================================================================
REM  Cesta.cmd - doble clic para tener Cesta arriba en http://localhost:8080
REM
REM  Este .cmd no hace el trabajo: dispara wscript -> plataforma\lanzar-cesta.vbs,
REM  que llama a plataforma\lanzar-cesta.ps1 con la ventana oculta. Asi no queda
REM  ninguna consola abierta y este .cmd termina de inmediato.
REM
REM  Todo lo que pasa queda en data\arranque-cesta.log (con fecha y resultado).
REM  Si ya estaba todo arriba, el .ps1 solo abre el navegador (es idempotente).
REM  No lanza la recoleccion: eso es la tarea de las 06:00 (ejecutar.bat).
REM ============================================================================
setlocal
set "CESTA_AQUI=%~dp0"

if not exist "%CESTA_AQUI%plataforma\lanzar-cesta.vbs" (
  echo Faltan ficheros del repositorio: plataforma\lanzar-cesta.vbs
  exit /b 1
)
if not exist "%SystemRoot%\System32\wscript.exe" (
  echo Falta wscript.exe en este Windows: no puedo lanzar Cesta sin ventana.
  exit /b 1
)

start "" "%SystemRoot%\System32\wscript.exe" //B //Nologo "%CESTA_AQUI%plataforma\lanzar-cesta.vbs"
exit /b 0
