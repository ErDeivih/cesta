# Arrancar Cesta: doble clic en `Cesta.cmd` (vía local)

1. La vía elegida es **local en este PC**, la que razona y mide [docs/DESPLIEGUE-VIAS-2026-11-09.md](DESPLIEGUE-VIAS-2026-11-09.md): nada sale de casa y no hay servidor que mantener.
2. Doble clic en `Cesta.cmd` (raíz del repo): arranca Docker Desktop si hace falta, hace `docker compose up -d` en `plataforma`, espera a `/api/salud` y abre `http://localhost:8080`.
3. No deja ventanas abiertas: el `.cmd` solo dispara `wscript` → PowerShell oculto y termina; el trabajo real lo hace `plataforma/lanzar-cesta.ps1` y todo queda en `data/arranque-cesta.log` con fecha y resultado.
4. Es idempotente: si la app ya responde, no toca contenedores y solo abre el navegador; si ya hay un arranque en curso, no lanza otro.
5. No hace scraping ni la recolección (eso sigue siendo la tarea de las 06:00, `ejecutar.bat`) y no para contenedores ni toca otros proyectos; si falla, la última línea del log lo dice.

## Cómo se usa

- **Doble clic en `Cesta.cmd`**. Tarda ~0,5 s si ya estaba todo arriba; 10–30 s si hay que levantar
  contenedores; hasta ~2 min si Docker Desktop estaba cerrado.
- Señal de que ha ido bien: el navegador se abre en `http://localhost:8080` y el final de
  `data\arranque-cesta.log` dice `[fin] resultado=OK`.
- Ver el log: `Get-Content data\arranque-cesta.log -Tail 20`.
- No necesita consola ni permisos de administrador. Para parar: `plataforma\arrancar.bat parar`
  (no borra datos).
- Ficheros del lanzador: `Cesta.cmd`, `plataforma/lanzar-cesta.vbs` y `plataforma/lanzar-cesta.ps1`. El `.ps1` va en ASCII sin BOM a proposito: la prueba de documentos del repo prohibe la marca U+FEFF, y PowerShell 5.1 lo ejecuta igual (probado con el arnés del lanzador).

## Si falla

| Lo que ves en `data\arranque-cesta.log` | Qué hacer |
|---|---|
| `[fallo] el motor de Docker no respondio en 120 s` | Abre Docker Desktop a mano, espera a «Engine running» y vuelve a hacer doble clic. |
| `[fallo] docker compose up -d fallo con codigo N` | Ejecuta `plataforma\arrancar.bat` (con consola) para ver el error real; `plataforma\arrancar.bat logs` para la API. |
| `[fallo] falta plataforma\.env` | Copia `plataforma\.env.ejemplo` a `plataforma\.env` y pon una `CESTA_CLAVE_DB` larga. |
| `[fallo] falta la imagen cesta-api` / `--build` | La primera vez reconstruye la imagen y tarda minutos; si falla, revisa `plataforma\Dockerfile`. |
| No hay log o no pasa nada al hacer doble clic | Que existan `plataforma\lanzar-cesta.vbs` y `wscript.exe`; mientras tanto, `plataforma\arrancar.bat` sigue valiendo. |

La app puede estar arriba y aun así fallar la página: comprueba `docker compose ps` (api/db *healthy*,
web *Up*) y `http://127.0.0.1:8080/api/salud`. Para problemas de la plataforma en sí, la tabla de
«Problemas conocidos» de [docs/DESPLIEGUE-VIAS-2026-11-09.md](DESPLIEGUE-VIAS-2026-11-09.md) §6.10.

## Qué está probado (9/11/2026, este PC)

| Caso | Resultado |
|---|---|
| Doble clic con todo ya arriba (idempotente) | Verde: 0,2–0,6 s, `[ok] la app ya estaba arriba`, navegador abierto, sin consolas ni procesos vivos del lanzador. |
| Arranque desde parado (contenedor `web` parado a propósito) | Verde: `docker compose up -d` → web *Started* → `/api/salud` en 2 s → navegador; 15,5 s en total. |
| Doble clic con otro arranque en curso | Verde: `[aviso] ya hay un arranque de Cesta en curso` y resultado `YA-EN-CURSO`; no abre otra consola ni otro navegador. |
| Log leído en bucle mientras arranca (otro proceso) | Verde: las líneas se encolan y se vuelcan al final; no se pierde ninguna. |
| **No probado**: Docker Desktop apagado | Habría que parar Docker, así que no se ha ejecutado la rama que lanza `Docker Desktop.exe` y espera hasta 120 s; el código está y el resto de la rama sí se ha probado. |
| **No probado**: reconstrucción con `--build` | La imagen `cesta-api` ya existe; esa rama solo se activa si falta la imagen. |
