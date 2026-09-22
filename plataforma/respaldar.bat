@echo off
REM ============================================================================
REM  Cesta: respaldo de PostgreSQL.
REM
REM  Es lo UNICO que hay que respaldar. Gold se regenera solo desde raw con
REM  `ejecutar.bat`, y raw se vuelve a bajar de las webs. Pero las cuentas, las
REM  listas y los favoritos solo existen aqui: si se pierde este volumen, se
REM  pierde todo lo que habeis escrito vosotros.
REM
REM    respaldar.bat              guarda uno nuevo y borra los de mas de 30 dias
REM    respaldar.bat restaurar <fichero.sql.gz>
REM
REM  Se puede dar de alta como tarea diaria igual que ejecutar.bat.
REM ============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist ".env" (
  echo Falta el fichero .env
  exit /b 1
)

set DESTINO=..\data\respaldos
if not exist "%DESTINO%" mkdir "%DESTINO%"

if /i "%~1"=="restaurar" (
  if "%~2"=="" (
    echo Uso: respaldar.bat restaurar ^<fichero.sql.gz^>
    echo.
    echo Los que hay:
    dir /b /o-d "%DESTINO%\*.sql.gz" 2>nul
    exit /b 2
  )
  echo.
  echo  ATENCION: esto SOBRESCRIBE las listas y cuentas que haya ahora.
  echo  Fichero: %~2
  set /p CONFIRMA="  Escribe SI para continuar: "
  if /i not "!CONFIRMA!"=="SI" (
    echo Cancelado.
    exit /b 0
  )
  docker compose exec -T db psql -U cesta -d cesta -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  powershell -NoProfile -Command "$in=[System.IO.File]::OpenRead('%~2'); $gz=New-Object System.IO.Compression.GzipStream($in,[System.IO.Compression.CompressionMode]::Decompress); $out=[System.Console]::OpenStandardOutput(); $gz.CopyTo($out); $gz.Close(); $in.Close()" | docker compose exec -T db psql -U cesta -d cesta
  if errorlevel 1 (
    echo El restaurado fallo.
    exit /b 1
  )
  echo Restaurado.
  exit /b 0
)

for /f %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HHmm"') do set CUANDO=%%d
set FICHERO=%DESTINO%\cesta_%CUANDO%.sql

docker compose ps db 2>nul | findstr /i "running" >nul
if errorlevel 1 (
  echo La base de datos no esta levantada. Arranca primero con arrancar.bat
  exit /b 1
)

echo Respaldando...
docker compose exec -T db pg_dump -U cesta -d cesta --clean --if-exists > "%FICHERO%"
if errorlevel 1 (
  echo El respaldo fallo. No se borra nada.
  del "%FICHERO%" 2>nul
  exit /b 1
)

REM Un fichero de cero bytes es un respaldo que no lo es. Mejor fallar ruidoso.
for %%A in ("%FICHERO%") do set TAM=%%~zA
if !TAM! lss 1000 (
  echo El respaldo salio vacio ^(!TAM! bytes^). Algo va mal; no se guarda.
  del "%FICHERO%" 2>nul
  exit /b 1
)

powershell -NoProfile -Command "$in=[System.IO.File]::OpenRead('%FICHERO%'); $out=[System.IO.File]::Create('%FICHERO%.gz'); $gz=New-Object System.IO.Compression.GzipStream($out,[System.IO.Compression.CompressionLevel]::Optimal); $in.CopyTo($gz); $gz.Close(); $out.Close(); $in.Close()"
del "%FICHERO%"

echo   Guardado: %FICHERO%.gz
for %%A in ("%FICHERO%.gz") do echo   Tamano:   %%~zA bytes

REM Los de mas de 30 dias sobran: con dos usuarios esto son kilobytes, pero un
REM directorio que crece para siempre acaba siendo un problema de otro dia.
forfiles /p "%DESTINO%" /m *.sql.gz /d -30 /c "cmd /c del @path" 2>nul

echo.
echo   Respaldos que hay ahora:
dir /b /o-d "%DESTINO%\*.sql.gz" 2>nul
