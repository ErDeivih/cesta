@echo off
REM ============================================================================
REM  Cesta: respaldo de PostgreSQL, del RECETARIO y del DIARIO.
REM  *(La primera linea decia solo «de PostgreSQL», y era lo mismo que la cabecera
REM  de abajo: **una lista corta que se lee como completa.**)*
REM
REM  **Y NO es lo unico, aunque esta cabecera lo decia.** *Lo que no se
REM  regenera son TRES cosas, y este guion respaldaba UNA:*
REM
REM    - PostgreSQL  -> las cuentas, las listas, la compra y los favoritos
REM    - recetas.sqlite -> EL RECETARIO
REM    - diario.sqlite  -> EL DIARIO, lo que cada uno ha comido
REM
REM  Gold se regenera solo desde raw con `ejecutar.bat`, y raw se vuelve a
REM  bajar de las webs -- eso sigue siendo verdad. Pero los otros dos NO son
REM  crudo ni se recalculan, y lo dice `docker-compose.yml:60-66` con estas
REM  palabras: *"no son crudo ni se recalculan -- son lo que la casa ha
REM  escrito"*, y avisa de que **`robocopy data\raw` NO LOS VE**.
REM
REM  *Y no son el fichero del host*: viven en el volumen `datos_api`
REM  (`/app/data`), y el compose explica por que no es un `bind` a `../data`.
REM  *Asi que se copian DEL VOLUMEN y con `VACUUM INTO` -- coherentes aunque
REM  la API los tenga abiertos --, que es lo que hace `scripts/respaldar_sqlite.py`.*
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

REM **La comprobacion, por el ID y no por una palabra de la tabla.**
REM
REM *Aqui habia `docker compose ps db | findstr /i "running"`, y **dejo de funcionar sin que nadie
REM tocara el guion**: *Docker Compose cambio el formato de `ps`, y la columna STATUS hoy dice
REM **«Up 22 hours (healthy)»**, no «running». *Asi que el `findstr` **no encontraba nada**, el
REM `errorlevel` daba 1, y el guion **abortaba diciendo que la base no estaba levantada -- con la base
REM levantada y sana.*
REM
REM *Y la consecuencia no era un mensaje feo*: **era que Cesta se quedaba SIN RESPALDO** de lo unico
REM que no se puede regenerar. *Lo dice la cabecera de este mismo fichero: las cuentas, las listas y los
REM favoritos solo existen en ese volumen.* *Y `data\respaldos` **no existia**: la carpeta la crea este
REM guion, asi que **nunca se habia ejecutado con exito.***
REM
REM *Ahora se pregunta por el ID del contenedor.* `--status running -q` **no imprime nada si no corre**,
REM *y eso si es una respuesta del estado y no una coincidencia de texto.* *La leccion es la misma que la
REM del `isdigit()` y la de `linea_con_destino`: **no se comprueba por como se llama algo, sino por lo
REM que hace.***
set CORRIENDO=
for /f %%i in ('docker compose ps --status running -q db 2^>nul') do set CORRIENDO=%%i
if "!CORRIENDO!"=="" (
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

REM *** Y LAS DOS SQLITE, que este guion no respaldaba. ***
REM *Se copian DEL VOLUMEN y con `VACUUM INTO` -- coherentes aunque la API las tenga abiertas --,
REM y con el MISMO sello de tiempo que la de PostgreSQL.*
echo   Respaldando el recetario y el diario...
uv run python "%~dp0..\scripts\respaldar_sqlite.py" --destino "%DESTINO%" --sello "%CUANDO%"
if errorlevel 1 (
  echo El respaldo de las SQLite fallo. El de PostgreSQL SI se guardo.
  exit /b 1
)

REM Los de mas de 30 dias sobran: con dos usuarios esto son kilobytes, pero un
REM directorio que crece para siempre acaba siendo un problema de otro dia.
forfiles /p "%DESTINO%" /m *.sql.gz /d -30 /c "cmd /c del @path" 2>nul
REM *Y las de las SQLite, con el mismo plazo.* Llevan sello de tiempo, asi que tambien se
REM acumulan. *Si se llamaran siempre igual no haria falta -- y seria peor: la copia de hoy
REM pisaria la de ayer, que es justo cuando un respaldo hace falta.*
forfiles /p "%DESTINO%" /m *.sqlite /d -30 /c "cmd /c del @path" 2>nul

echo.
echo   Respaldos que hay ahora:
dir /b /o-d "%DESTINO%\*.sql.gz" 2>nul
