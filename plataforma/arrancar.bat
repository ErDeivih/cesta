@echo off
REM ============================================================================
REM  Cesta: levanta la plataforma. Los datos se quedan en este PC.
REM
REM    .\arrancar.bat            levantar (o actualizar si ya estaba)
REM    .\arrancar.bat parar      parar
REM    .\arrancar.bat logs       ver que pasa
REM    .\arrancar.bat cuenta     dar de alta a una persona
REM
REM  El .\ de delante no sobra: PowerShell no ejecuta nada del directorio
REM  actual sin una ruta, y sin el contesta "no se reconoce como nombre de un
REM  cmdlet", que parece que falte el fichero. En cmd funcionan las dos.
REM
REM  El scraper NO va aqui: sigue siendo ejecutar.bat, en Windows, con su
REM  Chrome de verdad para el WAF de Alcampo. Las dos mitades solo se hablan
REM  por la carpeta data\gold, que este contenedor lee y nunca escribe.
REM ============================================================================
setlocal
cd /d "%~dp0"

where docker >nul 2>&1
if errorlevel 1 (
  echo Falta Docker Desktop. Instalalo y vuelve a intentarlo.
  exit /b 1
)

if not exist ".env" (
  echo Primera vez: falta el fichero .env
  echo   1. copia .env.ejemplo a .env
  echo   2. cambia CESTA_CLAVE_DB por algo largo
  echo   3. vuelve a ejecutar esto
  exit /b 1
)

if /i "%~1"=="parar" (
  docker compose down
  exit /b 0
)
if /i "%~1"=="logs" (
  docker compose logs -f --tail 60
  exit /b 0
)
if /i "%~1"=="cuenta" (
  if "%~2"=="" (
    echo Uso: .\arrancar.bat cuenta ^<usuario^> "^<Nombre^>"
    exit /b 2
  )
  docker compose exec api python -m plataforma.cuenta %2 %3
  exit /b %errorlevel%
)

echo Levantando Cesta...
docker compose up -d --build
if errorlevel 1 exit /b 1

echo.
echo Esperando a que la API responda...
set INTENTOS=0
:espera
set /a INTENTOS+=1
timeout /t 2 /nobreak >nul
curl -sf http://localhost:8080/api/salud >nul 2>&1
if not errorlevel 1 goto lista
if %INTENTOS% lss 30 goto espera
echo No responde despues de un minuto. Lo que dice la API:
echo     docker compose logs --tail 80 api
echo Si ahi pone ModuleNotFoundError, la API se muere al importarse: le falta
echo un paquete en la imagen. Lo vigila tests\test_imagen_api.py.
exit /b 1

:lista
echo.
echo   Cesta esta en marcha.
echo     en este PC          http://localhost:8080
echo     desde el movil      http://cesta:8080     (con Tailscale puesto)
echo.
echo   Si es la primera vez, da de alta las cuentas:
echo     .\arrancar.bat cuenta david "David"
echo     .\arrancar.bat cuenta mama  "Mama"
echo.
echo   La contrasena se teclea dos veces y necesita ocho caracteres o mas.
echo.
