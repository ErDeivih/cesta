# Despliegue de Cesta: las dos vías y la elegida (2026-11-09)

**Escrito por** el agente `despliegue` (equipo DSH) por encargo de David del 9/11/2026.
**Medido** el 9/11/2026 entre las **16:55 y las 17:05** (Europe/Madrid), en `DESKTOP-7J6LBK4`.
**Para** David y para el agente que continúe: el documento es autosuficiente; no hace falta el
contexto de la sesión donde se escribió.

Lo que este documento **no** es: no es un plan de migración ejecutado. No se ha tocado `.env`,
`docker-compose.yml`, `Caddyfile`, los `.bat`, ni `docs/DESPLIEGUE.md` (histórico). No hay commits
ni push. Las propuestas van marcadas como **propuesta** y con su comando exacto, para que las
ejecute quien tenga el encargo y el permiso.

El documento hace cinco cosas: describir lo que hay hoy con números medidos (§1), describir las dos
vías reales (§2), fijar la restricción que decide la partida (§3), comparar y elegir (§4–§5) y dar
el runbook de la vía elegida más el esquema mínimo de la otra (§6–§7). Al final quedan las
decisiones que necesitan a David (§8) y lo que no se ha podido medir (§9).

---

## 0. La decisión, en una frase

**Vía A: todo se queda en el PC de David, como está hoy.** La plataforma ya corre en Docker
Desktop y las dos piezas que la hacen útil (recolección diaria en Windows y app en el navegador)
llevan días funcionando sin desplegar nada. Lo único que falta para el móvil son dos cambios de
configuración —cero código— y programar el respaldo.

| Pregunta | Respuesta corta | Evidencia |
|---|---|---|
| ¿Qué coste nuevo tiene? | **0 €/mes**. Docker Desktop y Tailscale ya están instalados y en marcha | §1.1, §1.5 |
| ¿Cuánto se tarda en «terminar»? | 0 minutos para seguir como hoy; ~15 min para el móvil; ~5 min para programar el respaldo | §6.6, §6.8 |
| ¿Qué se acepta? | **Si el PC está apagado, la app no existe** para el móvil (la lista abierta se conserva en el teléfono) | `docs/DESPLIEGUE.md` §6, `plataforma/LEEME.md` «Sin cobertura» |
| ¿Qué cambia respecto a hoy? | Nada obligatorio. Opcional: escucha para el móvil, nombre de Tailscale `cesta`, respaldo programado | §5.3 |
| ¿Cuándo se revisa? | Cuando haga falta disponibilidad con el PC apagado, más personas, o notificaciones | §5.5 |

---

## 1. Lo que hay hoy, medido

### 1.1 La plataforma en Docker

Comandos y resultado (todos desde `F:\Proyectos\cesta\plataforma`):

| Comando | Resultado medido |
|---|---|
| `docker version --format '{{.Server.Version}}'` | **27.4.0** |
| `docker compose version` | **v2.31.0-desktop.2** |
| `docker compose config` | 3 servicios (`api`, `db`, `web`) y 3 volúmenes (`datos_api`, `datos_caddy`, `datos_db`); todo lo demás, abajo |
| `docker compose images` | `cesta-api` 89,1 MB · `postgres:16-alpine` 116 MB · `caddy:2-alpine` 24 MB (**229,1 MB** de imágenes del proyecto) |
| `docker stats --no-stream` | `cesta-api-1` 0,17 % CPU / **114 MiB**; `cesta-web-1` 0,00 % / **20,87 MiB**; `cesta-db-1` 0,00 % / **34,45 MiB** (≈ **169 MiB** en total; límite de la VM de Docker: 7,758 GiB) |
| `docker system df -v` | `cesta_datos_db` **77,12 MB**; `cesta_datos_api` **61,44 kB**; `cesta_datos_caddy` **143 B** |

`docker compose ps` (la foto de las 16:58):

| Contenedor | Imagen | Estado | Puertos publicados |
|---|---|---|---|
| `cesta-api-1` | `cesta-api` | Up 7 hours (**healthy**) | ninguno (solo red interna `8000/tcp`) |
| `cesta-db-1` | `postgres:16-alpine` | Up 7 hours (**healthy**) | `127.0.0.1:5432->5432/tcp` |
| `cesta-web-1` | `caddy:2-alpine` | Up 7 hours | `127.0.0.1:8080->8080/tcp` (además `80`, `443`, `2019`, `443/udp` **internos** de Caddy) |

Qué significa cada línea de `docker compose config` que importa:

- **`api`** se construye con contexto **`F:\Proyectos\cesta`** y `dockerfile: plataforma/Dockerfile`
  (imagen `python:3.12-slim`; solo `fastapi`, `uvicorn`, `duckdb`, `psycopg`, `argon2-cffi`,
  `pydantic`). Entorno: `CESTA_GOLD=/datos/gold`, `CESTA_ORIGENES`, `CESTA_DIAS_SESION=30`.
  Volúmenes: **`F:\Proyectos\cesta\data` → `/datos` (`read_only: true`)** y el volumen
  `datos_api` → `/app/data` (ahí viven `recetas.sqlite` y `diario.sqlite`, que sí se escriben; por
  eso son volumen con nombre y no un `bind` sobre `data/`).
- **`db`**: `postgres:16-alpine`, `PGDATA=/var/lib/postgresql/data/pgdata`, volumen `datos_db`, y
  el puerto **solo en loopback** (`127.0.0.1:5432`) porque la cadena diaria del PC
  (`projects/cesta/avisos.py`) mira las alertas a las 06:00 y necesita llegar a esa base.
- **`web`**: `caddy:2-alpine`; sirve `plataforma/web/dist` en `/srv:ro`, el material de
  `plataforma/web/aprende` en `/aprende:ro` y `plataforma/Caddyfile`; publica **`127.0.0.1:8080`**
  porque `plataforma/.env` tiene `CESTA_ESCUCHA=127.0.0.1` (el valor por defecto del compose es
  loopback desde el 12/10/2026; `0.0.0.0` hay que pedirlo).

`docker ps` mostró además dos contenedores **ajenos al compose del proyecto**, que no se tocan:
`facylf-postgres` (`127.0.0.1:5433`, otro proyecto — lo protege `plataforma/api/ajustes.py:70`) y
un `cesta-ensayo-propio` (`postgres:16-alpine`) suelto de una prueba que estaba corriendo en
paralelo a esta medición.

### 1.2 La app responde

| Petición | Resultado medido |
|---|---|
| `GET http://127.0.0.1:8080/` | **200**, 1.715 bytes |
| `GET http://127.0.0.1:8080/api/salud` | **200**, 40 bytes: `{"vivo":true,"fecha_datos":"2026-11-09"}` |
| `GET http://127.0.0.1:8080/api/estado` | **200**, 4.805 bytes |

De `/api/estado`: `fecha_datos` **2026-11-09**, `version_catalogo` **20261109-113939**,
`dias_precio_valido` 3, y **seis cadenas** con dato de hoy. Cobertura de hoy de las cinco de
catálogo: Mercadona 100,1 % · Carrefour 99,9 % · DIA 98,4 % · Aldi 93,6 % · Alcampo **84,1 %
(«corta», 9 huecos de 30 días, captura 23.562 frente a referencia 28.022 del 17/10)**; Lidl son
ofertas semanales (82 fichas), no catálogo.

### 1.3 El disco: qué datos hay y cuánto ocupan

| Ruta | Contenido | Tamaño medido |
|---|---|---:|
| `F:\Proyectos\cesta\data` | todo el árbol de datos | **16.646,4 MB**, 100.058 ficheros |
| `data\gold` | catálogo publicado | **1.832,2 MB**, 475 ficheros, **39 versiones** `v*` |
| `data\gold\v20261109-113939` | **la versión que se sirve hoy** | **50,8 MB**, 6 parquet |
| `data\gold` (raíz) | puntero y sueltos | 242,12 MB, 12 ficheros |
| `data\gold\matching` | pasadas del emparejador | 32,4 MB, 229 ficheros |
| versiones viejas de `gold` (38) | histórico de versiones | **1.507,0 MB** |
| `data\raw` | crudo de las cadenas | 4.190,8 MB, 95.631 ficheros |
| `data\bronze` / `data\silver` / `data\master` | pipeline | 223,0 MB / 286,7 MB / 1,2 MB |
| `data\externo` | ficheros externos | 7.512,7 MB, 2 ficheros |
| `plataforma\web\dist` | interfaz compilada | 0,9 MB, 48 ficheros |

`data\gold\actual.json` (puntero, leído a las 16:58): `version` **20261109-113939**,
`publicado_en` **2026-11-09T11:39:39**, 6 ficheros con su sha256 (`grupos.parquet`,
`enlaces.parquet`, `precio_diario.parquet`, `precio_derivado.parquet`, `resumen.parquet`,
`promos_por_cadena.parquet`). El desglose de la versión vigente: `precio_diario` 34,82 MB ·
`precio_derivado` 9,83 MB · `grupos` 4,48 MB · `resumen` 1,43 MB · `enlaces` 0,27 MB · `promos`
≈0 MB.

**Consecuencia medida para cualquier despliegue fuera del PC**: la API resuelve la versión con
`core/version_vigente.py` (puntero `actual.json`) y para el panel sella `matching/`
(`plataforma/api/catalogo.py:35`, `plataforma/api/cache.py:107`). Lo mínimo que necesita un
servidor es **`actual.json` + la carpeta de la versión vigente + `matching/` ≈ 83 MB**; las 38
versiones viejas (1.507,0 MB) no hacen falta allí. Hoy el compose monta el árbol `data/` entero
(16,6 GB) en solo lectura; en el PC eso no se nota, en un servidor es lo primero que se recortaría.

### 1.4 La recolección diaria (Windows, fuera de Docker)

`ejecutar.bat` (raíz) hace las cinco cadenas + fichas + pipeline `raw→bronze→silver→gold` +
emparejador + resumen, y deja `data\ultima_ejecucion.txt` para no repetir el día. La marca se
escribe con código 0 **y con 3** (día hecho con alguna cadena menos); se reintenta al siguiente
arranque solo si el pipeline no llegó a correr.

Tareas de Windows medidas con `schtasks /Query /XML`:

| Tarea | Disparadores | Última ejecución | Resultado | Próxima |
|---|---|---|---|---|
| `Cesta diaria` | diario **06:00** (desde 04/11/2026) + **al arrancar** + **al iniciar sesión** | 09/11/2026 **09:59:54** | **0** | 10/11/2026 06:00 |
| `Cesta vigilante` | diario **08:00, 14:00, 20:00** (desde 07/11/2026) + **al iniciar sesión** | 09/11/2026 **14:00:01** | **0** | 09/11/2026 20:00 |

Ambas son «**Solo interactivo**» (`Ejecutar como usuario: David`), es decir: **necesitan sesión de
usuario iniciada**, y su acción es `wscript.exe //B //Nologo "F:\EspacioCodigo\_flujo-dsh\Lanzar-Oculto.vbs" "cmd.exe" "/c" "F:\Proyectos\cesta\ejecutar.bat"`.
No son tareas de servicio de Windows y no tienen nada que ver con Docker.

Dato del día que enseña cómo se comporta la vía local: **el PC arrancó hoy a las 09:52:20 y la
recolección se lanzó a las 09:59:54** (la tarea de las 06:00 no pudo correr con el PC apagado y se
recuperó al iniciar sesión). El gold de hoy se publicó a las **11:39:39**. Es decir: el «diario a
las 06:00» es cierto **si el PC está encendido a las 06:00**; si no, el dato llega más tarde, y eso
hay que decirlo en vez de suponerlo.

El `data/` **no está en git** (`.gitignore`: `data/`, `.venv/`, `.env`), y `.dockerignore` en la
raíz excluye `data`, `docs`, `plataforma/web`, `.venv`, `.git` del contexto de construcción: tocar
documentación **no** obliga a reconstruir la imagen de la API.

### 1.5 Red: Tailscale, y el hallazgo de que hoy el móvil no llega

`tailscale status --json`:

| Nodo | DNS | IP | Estado |
|---|---|---|---|
| **este PC** | `desktop-7j6lbk4.tail4263a0.ts.net` | **100.110.114.10** | propio |
| `servidor` | `servidor` | **100.117.58.93** | Linux, **active**, conexión directa `192.168.1.149:41641` |
| `poco-x4-pro-5g` | — | 100.105.207.14 | Android, **offline, visto por última vez hace 10 días** |

`tailscale serve status` (medido): hay un servicio `http://desktop-7j6lbk4:3080` (y por FQDN)
publicado **solo en la tailnet**, proxy a `http://127.0.0.1:3080`; ese 3080 es de otro proceso
(`node.exe`, que no respondió en 6 s). **El puerto 3080 de Tailscale ya está ocupado**, pero el
443 de `tailscale serve` no está configurado.

Prueba de acceso real desde el PC a su propia IP de Tailscale:

```
GET http://100.110.114.10:8080/  ->  FALLO: «No es posible conectar con el servidor remoto»
```

**Motivo medido, no supuesto**: `plataforma/.env` tiene `CESTA_ESCUCHA=127.0.0.1`, y
`docker compose config` lo confirma (`host_ip: 127.0.0.1`, `published: "8080"`). La web **solo
escucha en loopback**. Por tanto, hoy:
- desde el PC: `http://localhost:8080` y `http://127.0.0.1:8080` funcionan;
- desde el móvil con Tailscale: **no se llega**, ni por IP ni por nombre;
- y el nombre documentado `http://cesta:8080` (`docs/TAILSCALE.md` §4, salida de `arrancar.bat`)
  **tampoco existe**: la máquina se llama `desktop-7j6lbk4`, no `cesta`.

Esto no es un fallo de la app: es que falta el paso de exponerla a la tailnet. Las opciones están
en §6.6.

### 1.6 Respaldo y registro: los dos cabos sueltos

- **Respaldo**: existe `plataforma\respaldar.bat` (hace `pg_dump` de la base, copia
  `recetas.sqlite`/`diario.sqlite` con `VACUUM INTO` y borra lo de más de 30 días), pero **no hay
  tarea programada que lo llame** (`schtasks` filtrado por `respald` no devuelve nada) y los
  últimos ficheros de `data\respaldos` son del **14/10/2026** (`cesta_2026-10-14_1044.sql.gz` 125
  KB y `cesta_2026-10-14_1123.sql.gz` 125 KB, más `recetas_2026-10-14_1123.sqlite` 32 KB). Lo que
  no se regenera es la base (77,12 MB de volumen) y las dos SQLite (61,44 kB de volumen); `gold`
  se regenera desde `raw` con `ejecutar.bat`.
- **Registro**: `CESTA_REGISTRO` **no está definida** en `plataforma/.env` y
  `plataforma/api/ajustes.py:53-54` la interpreta como **abierta** salvo que valga `cerrado`. Hoy
  cualquiera que llegue a la página puede crearse cuenta; es razonable **mientras solo se llegue
  por Tailscale** (`plataforma/LEEME.md`, «El registro está abierto…»). El día que haya una URL
  pública, o un túnel, hay que poner `CESTA_REGISTRO=cerrado` **antes** de exponer.

---

## 2. Las dos vías reales

### 2.1 Vía A — todo en el PC de David (la de hoy)

```
PC de David, Windows 11, AMD Ryzen 5 3600 (6c/12t), 32 GB RAM, F: con 149 GiB libres (160,2 GB)
│
├─ FUERA DE DOCKER (Windows, sesión de David)
│    Tarea «Cesta diaria» 06:00 + al arrancar + al iniciar sesión
│      └─ ejecutar.bat → core/waf.py (Patchright + Chrome real) → data/raw → bronze → silver → gold
│    Tarea «Cesta vigilante» 08:00/14:00/20:00 + al iniciar sesión → vigilar_ingesta
│
├─ DOCKER DESKTOP (arranca solo con Windows; contenedores `restart: unless-stopped`)
│    cesta-db-1   postgres:16-alpine  volumen datos_db (77,12 MB)  127.0.0.1:5432
│    cesta-api-1  imagen cesta-api    lee data/gold montado RO     red interna :8000
│    cesta-web-1  caddy:2-alpine      sirve web/dist              127.0.0.1:8080
│
└─ TAILSCALE (servicio Windows, arranque Automático)  este nodo: 100.110.114.10
     Hoy la web NO escucha en esa interfaz: el móvil no llega.
```

Ficheros que hacen cada cosa (los que hay que leer para tocar esto):

| Fichero | Qué hace |
|---|---|
| `plataforma\arrancar.bat` | levanta/actualiza (`docker compose up -d --build`), espera a `/api/salud`, da cuentas (`cuenta`), para (`parar`), logs (`logs`) |
| `plataforma\docker-compose.yml` | los 3 servicios, los 3 volúmenes y los montajes en solo lectura |
| `plataforma\Dockerfile` | imagen de la API (Python 3.12, solo lo que la API necesita) |
| `plataforma\entrar-api.sh` | arranque del contenedor de la API: adopta el volumen y baja a usuario `cesta` |
| `plataforma\Caddyfile` | sirve `web/dist`, `/aprende`, proxy `/api/*` a `api:8000`, CSP y cabeceras |
| `plataforma\.env` (no en git) | clave de la base, `CESTA_DATOS`, `CESTA_ESCUCHA`, `CESTA_ORIGENES`, `CESTA_DIAS_SESION` |
| `plataforma\respaldar.bat` | respaldo de base + SQLite en `data\respaldos`, y restauración |
| `ejecutar.bat` | la recolección diaria completa (no es Docker) |
| `plataforma\web\app` | fuente del front; `npm run build` deja `plataforma\web\dist` |

### 2.2 Vía B — un servidor siempre encendido

```
PC de David (Windows)                        Servidor (Linux, siempre encendido)
  scraper (obligatorio, §3)                    docker compose (mismos 3 servicios)
  data/gold  ──── sincronización diaria ────►  data/gold  (montado RO en la API)
  tareas 06:00/vigilante                       Caddy :443 (o :8080 en la tailnet)
                                                 ├─ cesta-api  (lee gold)
                                                 └─ cesta-db   (cuentas, listas, recetario)
móvil / PWA  ── Tailscale (o HTTPS público si es VPS) ──►  servidor
```

Hay dos variantes y **no cuestan lo mismo**:

**B1 — VPS alquilado.** Se contrata una máquina Linux (el proyecto venía estimando «VPS de 5 EUR»
al mes: `docs/OPERACION.md:550`, `docs/AMIGOS.md:135`); **precio no verificado hoy**). Ventaja
real: disponibilidad con el PC y la casa apagados, y HTTPS público si se quiere. El coste oculto:
la base y las listas salen de casa (disco alquilado), hay que administrar un servidor más, y **el
scraper sigue sin poder irse** (§3).

**B2 — el servidor que ya existe.** David ya tiene un nodo Linux en la tailnet (`servidor`,
`100.117.58.93`, en la LAN `192.168.1.149`). Medido por SSH de solo lectura:

| Dato del `servidor` | Medido |
|---|---|
| SO / arquitectura | Linux **x86_64** |
| CPU | **4 núcleos** |
| RAM | **15.907 MB** totales, **10.876 MB disponibles** en el momento de medir |
| Disco `/` | **211 GB**, 85 GB usados, **125 GB libres** (41 %) |
| Docker / Compose | **29.8.1** / v5.5.1 |
| Arrancado | 2026-11-09 **16:01:24** (55 min en el momento de medir) |
| Carga | **9,11 / 8,56 / 6,37** con 4 núcleos |
| Ocupación | **27 contenedores en `docker ps`** (40 creados) de Facylf y servicios propios (`facylf-*`, `homepage`, `ntfy`, `uptime-kuma`, `vigilante`…) |
| `/opt` | contiene `stacks` (parece el sitio de los compose) |
| ¿Hay Cesta? | **No** (`/opt/cesta`, `/srv/cesta`, `/home/*/cesta` no existen) |

Traducido: **B2 no necesita dinero nuevo, pero no es una máquina libre**. Ya sostiene la producción
de Facylf con carga 9,11 sobre 4 núcleos. Meter ahí Cesta es una decisión de convivencia, no una
instalación de trámite. Con 125 GB libres y 10,8 GB de RAM disponibles *hay sitio*; lo que no hay
es margen de CPU holgado.

**El problema central de B (las dos variantes)**: el scraper que produce `data/gold` no puede
salir de Windows (§3), así que **el dato tiene que cruzar de máquina todos los días**. Eso añade
una pieza nueva (sincronización) y un modo de fallo nuevo (la app sirve un gold más viejo del que
el PC ya tiene, y el aviso de frescura lo dirá, pero alguien tiene que mirarlo). Números para
dimensionarlo: **50,8 MB por versión diaria**; si se sincroniza `gold` entero, **1.832,2 MB**; si
solo lo que la API lee, **≈83 MB al principio y ~51 MB por día** (más el `matching/` cuando
cambie: 32,4 MB).

### 2.3 Lo que no es una vía (y no se reabre sin David)

- **Abrir un puerto en el router**: descartado con palabras en `docs/DESPLIEGUE.md` §4.3 y
  `docs/TAILSCALE.md` §7.
- **Cloudflare Tunnel / ngrok**: publican el servicio en internet; el proyecto exige entonces
  `CESTA_REGISTRO=cerrado` y asumir que la única puerta es Access (`docs/DESPLIEGUE.md` §4.2).
  No es una «tercera vía barata»: es la vía B1 sin comprar el servidor, y con más superficie.
- **GitHub Actions como despliegue**: fuera de encargo en esta tarea.

---

## 3. La restricción dura: el scraper no se muda

Esto no es una preferencia: es el hecho que decide el reparto. Evidencia en el propio código:

- `core/waf.py:181` — `from patchright.sync_api import sync_playwright`; `core/waf.py:205` —
  `p.chromium.launch_persistent_context(channel="chrome", …)`: **Chrome de verdad**, no el
  Chromium empaquetado, porque «el Chrome de verdad pasa más retos que el Chromium empaquetado».
- `core/waf.py:31-39` — el navegador se abre **visible** por defecto («con ventana pasa retos que
  sin ella no pasa») y `SCRAP_WAF_HEADLESS=1` «intenta sin ventana, sabiendo que entonces el WAF
  cortará más a menudo». Un servidor Linux sin escritorio no tiene ese «con ventana».
- `core/waf.py:73-120` — la colocación de la ventana usa `ctypes.windll.user32` y
  `GetSystemMetrics` (Windows): es código específico de Windows.
- `core/waf.py:16-17` y `:33` — el testigo de AWS WAF va ligado al **User-Agent** del navegador que
  lo obtuvo y la sesión caduca a las **6 horas**.
- `pyproject.toml` — `patchright>=1.47`; la API del Dockerfile **no** lo lleva (imagen
  `python:3.12-slim` con solo fastapi/uvicorn/duckdb/psycopg/argon2/pydantic).
- `docs/DIAGNOSTICO-ALCAMPO-2026-11-07.md` §2 — el 7/11 el WAF cortó tras **6.327 s**, con «20
  renovaciones / 11 intentos en una ventana de 60 s» sin pasar el reto, y con categorías y
  productos leídos bien hasta el corte: **bloqueo anti-bot, no selector**.
- `plataforma/Dockerfile:1-2` y `plataforma/LEEME.md` lo dicen con todas las letras: el scraper no
  va en el contenedor.
- La recolección es **diaria a las 06:00** en el PC (`Cesta diaria`) y mueve seis cadenas;
  `ejecutar.bat` contempla «noventa minutos de trabajo» y la de hoy publicó a las 11:39.

**Consecuencia para la vía B**: en un Linux habría que resolver Alcampo aparte (Chromium/Patchright
bajo X virtual, o renunciar a Alcampo). Renunciar a Alcampo no es un detalle: son **23.550
productos** de los 52.982 del catálogo y es una de las cadenas que hace que la comparación exista.
Por eso la vía B **no elimina el PC**: lo deja haciendo la recolección y le añade una máquina más.
Esa es la comparación honesta: no es «PC contra servidor», es «una máquina contra dos».

---

## 4. Tabla comparativa

Leyenda: **[M]** = medido en esta sesión; **[E]** = estimación o dato de documento del proyecto, no
verificado hoy.

| Dimensión | Vía A — local en el PC | Vía B — servidor |
|---|---|---|
| **Coste** | **0 € nuevos [M]**: Docker Desktop y Tailscale ya están instalados y funcionando. Electricidad no medida | **B1**: ~5 €/mes de VPS **[E, `docs/OPERACION.md:550`]** + dominio si es público (precio no medido). **B2**: 0 € nuevos, pero comparte máquina con Facylf [M] |
| **Esfuerzo de montaje** | **Ninguno para seguir como hoy [M]**; ~15 min para el móvil y ~5 min para programar el respaldo (§6.6, §6.8) | Horas, no medidas: clonar repo, `.env`, `docker compose up -d --build`, TLS/dominio o tailnet, **sync diario de gold**, migrar la base, respaldo y monitorización (§7) |
| **Privacidad** | **El dato no sale del PC [M]**: API y web en loopback; Tailscale no abre puertos (`docs/TAILSCALE.md` §1). Base con cuentas y listas en `datos_db` en el PC | **B1**: base y listas en disco alquilado. **B2**: en máquina propia, fuera del PC; el dato cruza la LAN/tailnet todos los días [M] |
| **Disponibilidad (PC apagado)** | **Se cae la app**: la lista abierta se conserva en el móvil (`docs/DESPLIEGUE.md` §6). Ejemplo real: hoy el PC arrancó a las 09:52 y el gold se publicó a las 11:39 [M] | **B1**: 24/7 mientras el proveedor esté. **B2**: disponible si el servidor, la luz y la internet de casa están; hoy el servidor llevaba 55 min arrancado [M] |
| **Mantenimiento** | 3 contenedores con `restart: unless-stopped`; imágenes de 229,1 MB; actualizar Docker Desktop y Windows; un `docker compose up -d --build api` cuando cambie la API [M] | Todo lo de A **más**: SO Linux, Docker del servidor (29.8.1 ≠ 27.4.0 del PC [M]), TLS, sincronización de gold, monitorización, y no romper Facylf [M] |
| **Copias de seguridad** | `respaldar.bat` existe y funciona por diseño, pero **no está programado** y el último respaldo es del **14/10/2026** [M]. La base son 77,12 MB de volumen; un dump comprimido, ~125 KB [M] | Igual, **más** el respaldo del servidor (snapshot del proveedor en B1, con coste; o copia aparte en B2), **más** el riesgo de que convivan dos bases y se separen |
| **Seguridad** | superficie mínima: **nada escuchando fuera de loopback [M]**; Tailscale con ACL (`docs/TAILSCALE.md` §4). Punto flojo actual: registro **abierto** por defecto (`ajustes.py:54`) | **B1**: servicio en internet → TLS, `CESTA_REGISTRO=cerrado`, cookie `secure`, parches y vigilancia. **B2**: se puede mantener cerrado con Tailscale (mejor que B1), pero es una máquina más que se puede ver comprometida |
| **Uso desde el móvil / PWA** | **Hoy no se llega [M]** (`GET http://100.110.114.10:8080` falla). Con §6.6: por HTTPS de Tailscale → PWA completa; por HTTP → navegador y acceso directo, sin service worker | **B1**: PWA completa desde cualquier red (HTTPS público). **B2**: como B1 dentro de la tailnet si se sirve HTTPS; no resuelve «sin Tailscale» |
| **Dónde viven los datos** | `data/gold` se escribe **en el PC** y se monta RO; la base y las SQLite en volúmenes de ese Docker [M] | Hay que **llevar gold** al servidor (§2.2): 50,8 MB/día o 1.832,2 MB si se copia entero [M] |
| **Recursos que pide** | **≈169 MiB de RAM y <0,2 % de CPU [M]** en un PC con 32 GB | Cabe en 2 GB de RAM y ~2 GB de disco **[E]**; el `servidor` tiene 10,8 GB de RAM libres y 125 GB de disco, pero **carga 9,11 en 4 núcleos [M]** |
| **Piezas que hay que sostener** | 2: recolección Windows + Docker (1 máquina) | 4: recolección Windows + sincronización + Docker en servidor + TLS/dominio (2 máquinas) |
| **El scraper** | Ya funciona, sin cambios | **Sigue en Windows** (§3): la vía B no lo sustituye, lo acompaña |

---

## 5. La vía elegida: local, y por qué es la más simple

### 5.1 El argumento, sin adjetivos

El PC no se puede quitar de la ecuación: el scraper de Alcampo necesita Patchright con Chrome de
verdad en Windows y la recolección es a las 06:00 en ese PC. Así que la decisión no es «PC o
servidor», sino **«una máquina o dos»**. La segunda máquina solo compra una cosa —que la app siga
en pie con el PC apagado— y a cambio pide: sincronizar gold todos los días, desplegar y mantener
el mismo stack en otro sitio, migrar la base, y respaldar dos sitios. Para una app de **uso
personal, no multiusuario**, cuyo dato nace en casa cada mañana, ese cambio no se paga hoy.
Cuando el motivo de la vía B aparezca (más gente, avisos, PC que ya no está encendido a diario),
la vía B pasará a ser la racional — y el servidor ya está ahí para ello.

### 5.2 Las cinco razones, con su evidencia

1. **Una sola fuente de verdad y cero sincronización.** El gold se escribe en
   `F:\Proyectos\cesta\data\gold` y la API lo lee del mismo disco (`docker compose config`: `data`
   → `/datos`, `read_only: true`). No hay retraso de sincronización, no hay dos copias que se
   separen y no hay un tercer proceso que vigilar. En la vía B hay 50,8 MB que cruzan de máquina
   cada día [M].
2. **Coste nuevo cero, y el «servidor gratis» no es gratis.** Todo lo necesario está instalado y
   en marcha: Docker 27.4.0 con los 3 contenedores *healthy*, Tailscale con arranque automático
   [M]. El servidor propio está sosteniendo otra producción con carga 9,11 en 4 núcleos [M];
   usarlo no cuesta euros, pero cuesta riesgo compartido. Un VPS cuesta ~5 €/mes **[E]** y saca la
   base de casa.
3. **Menos piezas que mantener.** Tres contenedores que consumen ≈169 MiB de RAM y <0,2 % de CPU
   [M], con `restart: unless-stopped` y arranque automático de Docker Desktop. La vía B duplica el
   mantenimiento (SO, Docker, TLS, sincronización) y añade una versión de Docker distinta a la del
   PC (29.8.1 frente a 27.4.0) [M].
4. **Privacidad y seguridad de superficie mínima.** Lo medido: la web escucha **solo en
   `127.0.0.1`**; la base, solo en `127.0.0.1:5432`; nada publicado a internet [M]. Las cuentas,
   listas y el diario se quedan en volúmenes del PC. La vía B1 pone esa base en un disco alquilado;
   la B2 la mueve a otra máquina que también hay que asegurar.
5. **El esfuerzo ya está hecho, y lo que falta no es desplegar.** La app responde hoy (200 en `/`,
   `/api/salud` y `/api/estado` [M]); el móvil necesita configuración, no despliegue (§6.6); el
   respaldo existe y solo hay que programarlo (§6.8). La vía B exige un runbook nuevo entero (§7).

### 5.3 Qué habría que cambiar respecto a lo que hay hoy

Nada **obligatorio** para que Cesta siga funcionando como hasta ahora. Lo que sí conviene, por
orden:

| # | Cambio | Por qué | Dónde | Estado |
|---|---|---|---|---|
| 1 | Exponer la app al móvil: `tailscale serve` HTTPS (M1) **o** `CESTA_ESCUCHA=0.0.0.0` (M2) | hoy el móvil no llega [M] | Tailscale / `plataforma\.env` | **propuesta**, no ejecutada (§6.6) |
| 2 | Renombrar el nodo de Tailscale de `desktop-7j6lbk4` a `cesta` | el nombre documentado `http://cesta:8080` no existe [M] | consola de Tailscale | **propuesta** |
| 3 | Programar `respaldar.bat` una vez al día | no hay tarea y el último respaldo es del 14/10 [M] | Programador de tareas | **propuesta** (§6.8) |
| 4 | `CESTA_REGISTRO=cerrado` **solo si** se publica fuera de la tailnet | hoy abierto por diseño (`ajustes.py:53-54`) | `plataforma\.env` | **decisión de David** (§8) |
| 5 | HTTPS de Tailscale para la PWA (service worker) | sin contexto seguro no hay service worker en el móvil | consola + `tailscale serve` | **propuesta** (§6.7) |
| 6 | Podar versiones viejas de gold (1.507,0 MB de 38 versiones) | no hace falta para servir; solo ocupa disco | `data\gold\v*` | **decisión de mantenimiento**, no urgente |

### 5.4 Lo que esta elección acepta (y no se puede prometer)

- **PC apagado = app caída** para el móvil. La lista abierta se guarda en el móvil y se sube al
  volver (`plataforma/LEEME.md` «Sin cobertura»). No hay notificaciones push: el proyecto ya las
  descartó por necesitar servidor siempre accesible (`docs/API.md`, `docs/FUNCIONALIDADES.md`).
- **La recolección de las 06:00 es condicional**: si el PC está apagado, la tarea se recupera al
  arrancar/iniciar sesión —hoy pasó a las 09:59:54— y el dato del día puede llegar a media mañana
  (hoy, 11:39) [M].
- **Sin HTTPS no hay PWA completa**: `plataforma/web/dist/sw.js` existe y el paquete registra
  `navigator.serviceWorker.register("/sw.js")` al cargar, pero un service worker exige contexto
  seguro (HTTPS o `localhost`). Por HTTP en el móvil se puede usar la web y guardar un acceso
  directo (el `site.webmanifest` se sirve), pero no contar con caché/offline de PWA. No se ha
  probado en un teléfono (§9).
- **La cookie de sesión no lleva `secure`** (`plataforma/api/main.py:93` y `:134`: `httponly`,
  `samesite="lax"` y sin `secure`): correcto en HTTP local, y habría que revisarlo el día que se
  sirva por HTTPS (decisión pequeña de código, ya señalada en `docs/MATRIZ-DE-ACEPTACION.md`).
- **Las tareas de Windows son «Solo interactivo»** [M]: si nadie inicia sesión, el trabajo que
  necesita escritorio (la ventana de Chrome del WAF) no corre.

### 5.5 Cuándo esta elección dejaría de ser la correcta

Dejaría de serlo —y entonces la vía B pasa a ser la recomendada— si ocurre **cualquiera** de
estas tres cosas:

1. **Más personas** que en casa: la madre o amigos usando la app desde otra casa y a horas
   cualesquiera (`docs/AMIGOS.md` §3.2 ya lo plantea).
2. **Avisos o push**: necesitan servidor siempre accesible.
3. **El PC deja de estar encendido a diario**: la recolección y la app dependen de que lo esté.

La regla, en una línea: **local mientras sean una o dos personas, en la misma casa, con el PC
encendido al menos una vez al día y sin notificaciones; servidor cuando falle cualquiera de las
tres.**

---

## 6. Runbook de la vía local

Todo lo de esta sección está pensado para ejecutarse en PowerShell en `F:\Proyectos\cesta`.
El `.\` delante de los `.bat` no sobra: PowerShell no ejecuta nada del directorio actual sin ruta
(`plataforma/LEEME.md`).

### 6.0 Comprobaciones previas (una vez)

```powershell
docker version --format '{{.Server.Version}}'   # esperado: 27.4.0 o superior
docker compose version                          # esperado: v2.31.0-desktop.2 o superior
& .\.venv\Scripts\python.exe --version          # esperado: Python 3.11.15
node --version                                  # esperado: v24.x (solo si se toca el front)
```

Los tres comandos están medidos en §1.1 y §Anexo A.

### 6.1 Puesta en marcha (primera vez y cada día)

Primera vez:

```powershell
cd F:\Proyectos\cesta\plataforma
copy .env.ejemplo .env
notepad .env
#   CESTA_CLAVE_DB = una clave larga y aleatoria (no se escribe nunca; la usan API y Postgres)
#   CESTA_DATOS     = ../data
#   CESTA_ESCUCHA   = 127.0.0.1      (loopback; para el móvil, ver 6.6)
#   CESTA_ORIGENES  = http://localhost:8080,http://cesta:8080
#   CESTA_DIAS_SESION = 30
.\arrancar.bat
```

`arrancar.bat` comprueba que existe Docker y `.env`, hace `docker compose up -d --build`, espera
hasta 30 veces × 2 s a que `http://localhost:8080/api/salud` conteste y termina con «Cesta está en
marcha». Los días siguientes suele bastar con no hacer nada: Docker Desktop arranca con Windows
(medido en `HKCU:\...\Run`: `Docker Desktop -Autostart`) y los contenedores tienen
`restart: unless-stopped`. Si algo se paró a mano:

```powershell
cd F:\Proyectos\cesta\plataforma
.\arrancar.bat
```

### 6.2 Alta de cuenta

```powershell
cd F:\Proyectos\cesta\plataforma
.\arrancar.bat cuenta david "David"
```

También se puede crear desde la propia página (`plataforma/LEEME.md`): el registro está abierto
salvo que `CESTA_REGISTRO=cerrado` (§1.6). La consola hace falta precisamente cuando se cierra el
registro.

### 6.3 Verificación (lo que tiene que salir)

```powershell
cd F:\Proyectos\cesta\plataforma
docker compose ps
#   cesta-api-1  Up (healthy)   8000/tcp
#   cesta-db-1   Up (healthy)   127.0.0.1:5432->5432/tcp
#   cesta-web-1  Up             127.0.0.1:8080->8080/tcp

(Invoke-WebRequest http://127.0.0.1:8080/api/salud -UseBasicParsing).Content
#   {"vivo":true,"fecha_datos":"2026-11-09"}

(Invoke-WebRequest http://127.0.0.1:8080/api/estado -UseBasicParsing).StatusCode
#   200
```

Y desde el navegador del PC: `http://localhost:8080` (o `http://127.0.0.1:8080`). Medido hoy: 200
con 1.715 bytes y el paquete de Vite en `/assets/index-BYw0TTA9.js`.

### 6.4 La recolección diaria y la frescura del dato

```powershell
cd F:\Proyectos\cesta
.\ejecutar.bat            # una vez al día; si ya se hizo hoy, sale enseguida
.\ejecutar.bat --forzar   # repetir a propósito (p. ej. tras un corte de Alcampo)
Get-Content data\gold\actual.json | Select-Object -First 8
```

La tarea «Cesta diaria» (06:00 + al arrancar + al iniciar sesión) y «Cesta vigilante»
(08:00/14:00/20:00 + al iniciar sesión) están verificadas en §1.4. Para comprobar la frescura que
ve la app: `GET /api/estado` → `fecha_datos` y `version_catalogo` (hoy: `2026-11-09` /
`20261109-113939`). El vigilante deja `data\avisos_ingesta.json` y, si hay fallo,
`data\INGESTA-DETENIDA.txt`.

### 6.5 Cambios de interfaz y de API

- **Interfaz** (`plataforma/web/app`): `npm run build` compila a `plataforma/web/dist` (el script
  es `tsc --noEmit && vite build && node scripts/sella-sw.mjs`; `package-lock.json` presente).
  Caddy sirve `dist` por `bind` montado en solo lectura, **no hace falta recrear el contenedor**:

  ```powershell
  cd F:\Proyectos\cesta\plataforma\web\app
  npm install          # solo la primera vez o si cambian dependencias
  npm run build
  (Invoke-WebRequest http://127.0.0.1:8080/sw.js -UseBasicParsing).StatusCode   # 200
  ```

- **API** (`core/` o `plataforma/`): hay que reconstruir la imagen (el contexto es la raíz y el
  `.dockerignore` de la raíz excluye `data`, `docs`, `.venv`, `plataforma/web`):

  ```powershell
  cd F:\Proyectos\cesta\plataforma
  docker compose up -d --build api
  docker compose ps    # cesta-api-1 Up (healthy)
  ```

- Antes de dar por bueno un despliegue, el proyecto tiene su propia prueba de lo servido:
  `& .\.venv\Scripts\python.exe -m plataforma.prueba_produccion` (desde la raíz, con la app
  levantada; mira el paquete compilado, el CSP de Caddy y la base de casa).

### 6.6 El móvil: hoy no se llega, y las tres formas de arreglarlo

Estado medido (§1.5): `.env` con `CESTA_ESCUCHA=127.0.0.1`; `GET http://100.110.114.10:8080`
falla; el nodo se llama `desktop-7j6lbk4`, no `cesta`.

**M1 — `tailscale serve` con HTTPS (recomendada; no toca el compose ni el `.env`)**

Mantiene la web en loopback y deja que Tailscale haga de proxy con TLS dentro de la tailnet. Esto
además da **contexto seguro** al móvil (PWA con service worker) y no expone nada a la wifi.

```powershell
# 1) (si no está) activar HTTPS/certificados en la consola de Tailscale: DNS → HTTPS Certificates
# 2) publicar la app en 443 de la tailnet, solo para miembros:
& 'C:\Program Files\Tailscale\tailscale.exe' serve --bg --https=443 http://127.0.0.1:8080
& 'C:\Program Files\Tailscale\tailscale.exe' serve status
# 3) desde el móvil, con Tailscale activo:
#    https://desktop-7j6lbk4.tail4263a0.ts.net/     (o https://cesta.tail4263a0.ts.net/ si se renombra, cambio 2 de §5.3)
```

El 443 no aparece configurado en `tailscale serve`; el 3080 ya lo usa otro servicio (§1.5). **No ejecutado**:
es un cambio de configuración de la tailnet y requiere que David decida (§8).

**M2 — `CESTA_ESCUCHA=0.0.0.0` (la de menos cambios si M1 no convence)**

```powershell
cd F:\Proyectos\cesta\plataforma
# editar .env:  CESTA_ESCUCHA=0.0.0.0
docker compose up -d web
docker compose ps    # esperado: 0.0.0.0:8080->8080/tcp
(Invoke-WebRequest http://100.110.114.10:8080/api/salud -UseBasicParsing).Content
```

Ventaja: `localhost:8080` sigue funcionando y la espera de `arrancar.bat` no se rompe. Coste:
además de la tailnet, escucha en la wifi de casa (y en cualquier VPN del PC). No hay puerto abierto
en el router, así que no queda en internet. **No ejecutado**: `.env` está fuera del alcance de este
trabajo.

**M3 — `CESTA_ESCUCHA=100.110.114.10` (la más estricta, y la que rompe una comprobación)**

Ataría la web **solo** a la interfaz de Tailscale. Problema medido en el código: `arrancar.bat:62`
espera `http://localhost:8080/api/salud`, que con esta opción **no responde**, así que el script
diría «No responde después de un minuto» con la plataforma perfectamente arriba. Habría que
cambiar esa línea para que consulte la misma dirección que `CESTA_ESCUCHA` (cambio pequeño, **no
hecho** porque `arrancar.bat` está fuera de mi alcance). Si se elige M3, es la tarea siguiente.

Y en las tres: renombrar el nodo a `cesta` en la consola (Machines → `desktop-7j6lbk4` → rename),
para que valga el `http://cesta:8080` que ya dicen `docs/TAILSCALE.md` y la salida de
`arrancar.bat`. Si no se renombra, usar `desktop-7j6lbk4` o la IP `100.110.114.10`.

### 6.7 PWA y HTTPS

`plataforma/web/dist` tiene `site.webmanifest`, `icono-192.png`, `icono-512.png`,
`icono-maskable-512.png` y `sw.js` (medido: 0,9 MB y 48 ficheros en `dist`; ver §Anexo A). El
paquete compilado registra `navigator.serviceWorker.register("/sw.js")` al cargar. Un service
worker **exige contexto seguro**: con `https://…ts.net` (M1) funciona; con `http://100.110.114.10:8080`
(M2) no se registra (el `catch` del código lo silencia). El manifiesto sí se sirve en HTTP, así que
«añadir a pantalla de inicio» se puede, pero sin cache offline. No probado en teléfono (§9).

### 6.8 Copias de seguridad (existe el guion; falta el reloj)

```powershell
cd F:\Proyectos\cesta\plataforma
.\respaldar.bat
#  Guardado: ..\data\respaldos\cesta_AAAA-MM-DD_HHMM.sql.gz  (~125 KB medidos)
#  + recetas_AAAA-MM-DD_HHMM.sqlite y diario_*.sqlite
#  borra los .sql.gz y .sqlite de más de 30 días
```

Restaurar (sobrescribe listas y cuentas; pide escribir `SI`):

```powershell
.\respaldar.bat restaurar ..\data\respaldos\cesta_2026-10-14_1123.sql.gz
```

Para dejarlo automático, **propuesta** (no ejecutada): una tarea diaria que llame a
`F:\Proyectos\cesta\plataforma\respaldar.bat`, p. ej. las 07:30 (después de la recolección, antes
del día), con el mismo patrón de las otras dos (`wscript Lanzar-Oculto.vbs cmd /c …`, usuario
David). El respaldo debe quedar **fuera del PC** además de en `data\respaldos` (el repo y
`data/` no están en git; `docs/OPERACION.md` y `DESPLIEGUE.md` ya avisan de que la base es lo único
irreemplazable). Destino externo: **decisión de David** (§8).

### 6.9 Parar, actualizar, volver atrás

```powershell
cd F:\Proyectos\cesta\plataforma
.\arrancar.bat parar    # docker compose down (NO borra volúmenes)
.\arrancar.bat logs     # docker compose logs -f --tail 60
docker compose logs --tail 80 api
```

- `docker compose down` conserva `datos_db`, `datos_api` y `datos_caddy`. `docker compose down -v`
  **borra** la base y las SQLite: no usarlo salvo que se quiera empezar de cero.
- Volver a la interfaz vieja: cambiar el montaje `./web/dist:/srv:ro` por `./web:/srv:ro` y
  recrear web (`docker compose up -d web`); la carpeta vieja se conserva como plan B
  (`docs/DESPLIEGUE.md` §8).

### 6.10 Problemas conocidos

| Síntoma | Causa y qué hacer |
|---|---|
| `cesta-api-1` se reinicia sin parar; `docker compose exec` dice «Container is restarting» | La API muere al importarse: `docker compose logs --tail 80 api`. Histórico: un `import polars` colado en la API; lo vigila `tests/test_imagen_api.py` |
| La API no arranca | Casi siempre `CESTA_GOLD` apunta a una carpeta sin parquet. Comprobar que existe `data\gold\grupos.parquet` |
| Entra pero no hay datos | El pipeline no ha corrido: `.\ejecutar.bat` en la raíz |
| Desde el móvil no se abre | Primero comprobar `http://localhost:8080` en el PC; si ahí va, es Tailscale o la escucha (§6.6) |
| `arrancar.bat` dice «No responde después de un minuto» y `docker compose ps` está bien | Si se usó `CESTA_ESCUCHA` con la IP de Tailscale, la espera consulta `localhost` (`arrancar.bat:62`): es la trampa de M3 (§6.6) |
| Respaldo con error «no está levantada» habiendo base | El guion ya se corrigió para preguntar por el ID del contenedor; si se editó `docker compose ps` o el formato, revisar `plataforma\respaldar.bat` |

### 6.11 Checklist de aceptación de la vía local

| # | Comprobación | Esperado |
|---|---|---|
| 1 | `docker compose ps` | 3 contenedores del proyecto; `api` y `db` *healthy* |
| 2 | `GET http://127.0.0.1:8080/` | 200 |
| 3 | `GET http://127.0.0.1:8080/api/salud` | `{"vivo":true,"fecha_datos":"<hoy>"}` |
| 4 | `GET http://127.0.0.1:8080/api/estado` | 200, `fecha_datos` del último gold y 6 cadenas |
| 5 | Tarea «Cesta diaria» | última ejecución con resultado 0; próxima 06:00 |
| 6 | `data\gold\actual.json` | `publicado_en` del día |
| 7 | `.\respaldar.bat` (manual o programado) | `data\respaldos\cesta_<sello>.sql.gz` > 1 KB |
| 8 | (si se hizo §6.6) móvil con Tailscale | abre la app y se puede iniciar sesión |

---

## 7. Esquema mínimo de la vía B (la otra)

No ejecutado. Es el mínimo para que otro agente o David puedan montarla sin reinventar el orden.
Va con los números medidos del `servidor` de §2.2.

### 7.1 Requisitos

- Linux con Docker + Compose (el servidor tiene Docker 29.8.1 / Compose v5.5.1 [M]).
- 2 GB de RAM y ~2 GB de disco para el stack + gold **[E]**; el servidor tiene 10,8 GB de RAM
  disponibles y 125 GB libres, pero **carga 9,11 en 4 núcleos** [M].
- Acceso al repo privado (`https://github.com/ErDeivih/cesta`) y a `data/gold` del PC.
- Si se publica en internet: TLS (Caddy) + dominio o certificado de Tailscale; y
  `CESTA_REGISTRO=cerrado` **antes** de exponer.

### 7.2 Pasos mínimos

```bash
# en el servidor
ssh servidor
sudo mkdir -p /opt/stacks/cesta && cd /opt/stacks/cesta
git clone https://github.com/ErDeivih/cesta .
cd plataforma
cp .env.ejemplo .env && nano .env
#   CESTA_CLAVE_DB   = clave nueva y larga
#   CESTA_DATOS      = /opt/stacks/cesta/data
#   CESTA_ESCUCHA    = 127.0.0.1        (y delante un Caddy/`tailscale serve` con TLS)
#   CESTA_ORIGENES   = https://<dominio-o-nodo>
docker compose up -d --build
docker compose ps
```

El `Caddyfile` actual sirve `:8080` en **HTTP** y no tiene bloque de dominio: para HTTPS en
internet hay que añadir un sitio con el dominio (Caddy pide el certificado solo) y publicar 443 en
el compose; para HTTPS dentro de la tailnet basta `tailscale serve`/`tailscale cert` y dejar el
compose escuchando en loopback. **Ese cambio de `Caddyfile` es parte del trabajo de B, no está
hecho.**

### 7.3 El cruce de gold (la pieza nueva)

La API resuelve la versión con `actual.json` y sella `matching/` (§1.3). Opciones, de menos a más
piezas:

1. **Copia diaria de la versión vigente** desde el PC tras la recolección (~51 MB/día). Lo mínimo:
   `actual.json`, `manifiesto.json`, la carpeta `v*` que apunta y `matching/` (≈83 MB la primera
   vez). Con `scp`/`rsync` desde WSL o con una tarea de Windows que llame a `scp`. **Hay que
   sincronizar el puntero al final**, para que la API no lea una versión a medias.
2. **`data/gold` completo** (1.832,2 MB): más simple de razonar, más disco y más tiempo de copia;
   las 38 versiones viejas (1.507,0 MB) no se usan en el servidor.
3. **Montar `data/gold` del PC por red** (SMB/NFS) y montarlo en el contenedor en solo lectura, o
   sincronizar con una herramienta de ficheros (en el PC ya hay Resilio Sync instalado; su
   configuración no se ha inspeccionado, §9). Menos copias, más dependencia de la red.

El modo de fallo a vigilar es el mismo que ya existe: si el sync se para, la app sirve gold viejo y
`/api/estado` lo dice con `fecha_datos`; hay que añadir un aviso (el vigilante actual es del PC, no
del servidor).

### 7.4 Migrar la base y las SQLite

```powershell
# en el PC
cd F:\Proyectos\cesta\plataforma
docker compose exec -T db pg_dump -U cesta -d cesta --clean --if-exists > cesta_migracion.sql
# copiar el fichero al servidor (scp/rsync) y allí:
cd /opt/stacks/cesta/plataforma
docker compose exec -T db psql -U cesta -d cesta < cesta_migracion.sql
```

`recetas.sqlite` y `diario.sqlite` viven en el volumen `datos_api` (§1.1): hay que copiarlas del
volumen (el `respaldar.bat` ya genera copias coherentes con `VACUUM INTO`; sirven para esto).
Después, decidir si el PC deja de tener base propia (recomendado) para no tener dos bases que se
separan.

### 7.5 Verificación y lo que no cambia

Verificar con el mismo checklist de §6.11 contra la URL del servidor. **Lo que no cambia**: el
scraper sigue en el PC con sus tareas a las 06:00/vigilante (§3), y `ejecutar.bat` sigue
escribiendo en `F:\Proyectos\cesta\data`; la vía B solo mueve **la lectura** (API, base, web).

---

## 8. Decisiones que necesitan a David

| # | Decisión | Opciones | Recomendación | Si no se decide |
|---|---|---|---|---|
| 1 | ¿Se cierra la pregunta «local o servidor»? | A (local, como hoy) · B1 (VPS) · B2 (servidor propio) | **A hoy** (§5), con disparadores de §5.5 | Cesta sigue funcionando igual; la pregunta queda abierta en cada sesión |
| 2 | Móvil: cómo se expone | **M1** HTTPS con `tailscale serve` · **M2** `CESTA_ESCUCHA=0.0.0.0` · **M3** IP de Tailscale (rompe `arrancar.bat`) | **M1** (privacidad + PWA); M2 como plan B | El móvil no llega (§1.5); la app solo se usa en el PC |
| 3 | Nombre del nodo | renombrar `desktop-7j6lbk4` → `cesta` · dejarlo | renombrar: `http://cesta:8080` es lo documentado | Los comandos de `docs/TAILSCALE.md` no funcionan tal cual |
| 4 | ¿HTTPS/PWA en el móvil? | sí (M1) · no, acceso directo en HTTP | **sí**, con M1 | Sin service worker el móvil no puede abrir la app sin red (la lista abierta se guarda igual; el SW es lo que la sirve sin conexión) |
| 5 | `CESTA_REGISTRO` | abierto (hoy) · `cerrado` | **abierto** mientras solo se llegue por Tailscale; **cerrado antes** de cualquier URL pública o túnel | Si algún día se publica sin cerrarlo, cualquiera en internet puede crearse cuenta (`ajustes.py:53-54`) |
| 6 | Respaldo | programar `respaldar.bat` + copia fuera · dejarlo manual | **programar** (último respaldo: 14/10/2026 [M]) | La base —lo único irreemplazable— depende de que alguien se acuerde |
| 7 | Si algún día B: ¿VPS o el `servidor`? | B1 ~5 €/mes **[E]** · B2 compartir Facylf | B2, si Facylf y Cesta conviven sin cargarse (hoy: carga 9,11 [M]); B1 si se quiere 24/7 sin depender de casa | No hay que decidirlo hoy (§5.5) |
| 8 | Dominio propio | sí (solo si B1 público) · no (ts.net de Tailscale) | **no** para uso personal: Tailscale da nombre y TLS sin dominio | Comprar dominio solo tendría sentido si el servicio se publica |
| 9 | Cookie `secure` el día que haya HTTPS | dejarla · añadir `secure` | añadirla con TLS (una línea, `main.py:93/134`) | Cookie transmitible por HTTP si algún día conviven ambos |
| 10 | Podar versiones viejas de gold | sí (liberar 1.507,0 MB) · no | sí, cuando moleste el disco; no es urgente (F: tiene 149 GiB libres, 160,2 GB [M]) | `data/gold` crece ~51 MB/día |

---

## 9. Lo que no se ha podido medir (y por qué)

1. **Acceso real desde un móvil.** En esta sesión no hay teléfono. Lo medido es la prueba desde el
   PC a su propia IP de Tailscale, que **falla** hoy (§1.5); habilitarlo exige tocar `.env` o la
   tailnet, fuera del alcance de este encargo.
2. **Cortafuegos de Windows** con una publicación en `0.0.0.0` (M2): no probado; Docker Desktop
   suele añadir reglas, pero no se ha medido.
3. **HTTPS de Tailscale** (M1): no se ha ejecutado `tailscale serve --https` ni se ha comprobado si
   la tailnet tiene certificados habilitados. El puerto 443 de `serve` está libre; el 3080 no
   (§1.5).
4. **Precio de VPS y de dominio**: no se han consultado proveedores. El «5 EUR» es estimación del
   proyecto (`docs/OPERACION.md:550`).
5. **Tiempo de reconstrucción de la imagen de la API y de arranque en frío**: no se ha medido para
   no tirar el stack en marcha. Las imágenes ya construidas suman 229,1 MB.
6. **Fiabilidad 24/7 del `servidor`**: solo se sabe que llevaba 55 min arrancado a las 16:56 y que
   su carga era 9,11; no hay histórico.
7. **Copia de seguridad fuera del PC**: Resilio Sync está en el arranque de Windows, pero no se ha
   inspeccionado su configuración ni si sincroniza `data/`.
8. **Encendido del PC a las 06:00 en un día normal**: hoy no lo estaba (arrancó a las 09:52 y la
   recolección fue a las 09:59:54 [M]); no hay serie de días.
9. **PWA en teléfono** (registro del service worker, instalación): no probado. La limitación de
   contexto seguro es una regla del navegador, no una medición de esta sesión.
10. **Consumo eléctrico** del PC y del servidor: no medido.

---

## Anexo A. Comandos y salidas que sostienen las cifras

```text
$ docker version --format '{{.Server.Version}}'          -> 27.4.0
$ docker compose version                                  -> v2.31.0-desktop.2
$ docker compose ps
  cesta-api-1  Up 7 hours (healthy)  8000/tcp
  cesta-db-1   Up 7 hours (healthy)  127.0.0.1:5432->5432/tcp
  cesta-web-1  Up 7 hours            127.0.0.1:8080->8080/tcp
$ docker compose images
  cesta-api-1  cesta-api:latest        89.1MB
  cesta-db-1   postgres:16-alpine     116MB
  cesta-web-1  caddy:2-alpine          24MB
$ docker stats --no-stream
  cesta-api-1  0.17%  114MiB   ·  cesta-web-1  0.00%  20.87MiB  ·  cesta-db-1  0.00%  34.45MiB
$ docker system df -v  (volúmenes del proyecto)
  cesta_datos_db 77.12MB · cesta_datos_api 61.44kB · cesta_datos_caddy 143B
```

```text
GET http://127.0.0.1:8080/                  -> 200, 1715 bytes
GET http://127.0.0.1:8080/api/salud         -> 200, {"vivo":true,"fecha_datos":"2026-11-09"}
GET http://127.0.0.1:8080/api/estado        -> 200, 4805 bytes
   fecha_datos=2026-11-09  version_catalogo=20261109-113939  cadenas=6
GET http://100.110.114.10:8080/             -> FALLO (no se puede conectar)
```

```text
data                                 100.058 ficheros  16.646,4 MB
data/gold                                  475 ficheros   1.832,2 MB   (39 versiones v*)
data/gold/v20261109-113939                   6 ficheros      50,8 MB
data/gold/matching                         229 ficheros      32,4 MB
data/raw                                95.631 ficheros   4.190,8 MB
plataforma/web/dist                          48 ficheros       0,9 MB
actual.json: version 20261109-113939, publicado_en 2026-11-09T11:39:39
```

```text
Cesta diaria     06:00 + arrancar + iniciar sesión   último 09/11 09:59:54 res 0   próxima 10/11 06:00
Cesta vigilante  08:00 + 14:00 + 20:00 + iniciar sesión  último 09/11 14:00:01 res 0  próxima 09/11 20:00
PC arrancado 09/11 2026 09:52:20 · Docker Desktop en HKCU\...\Run · Tailscale servicio Automático
```

```text
Tailscale: self desktop-7j6lbk4.tail4263a0.ts.net 100.110.114.10
           peer  servidor 100.117.58.93 linux active (direct 192.168.1.149:41641)
           peer  poco-x4-pro-5g offline (10 días)
           serve http://desktop-7j6lbk4:3080 -> http://127.0.0.1:3080 (tailnet only)
servidor: Linux x86_64 · 4 núcleos · 15.907 MB RAM (10.876 disponibles) · / 211G (125G libres)
          Docker 29.8.1 · Compose v5.5.1 · uptime -s 2026-11-09 16:01:24 · load 9,11
          27 contenedores en docker ps (40 creados) · /opt/stacks · sin Cesta
```

## Anexo B. Mapa de ficheros para quien continúe

| Fichero | Para qué mirarlo |
|---|---|
| `plataforma/docker-compose.yml` | los 3 servicios, montajes RO, volúmenes, comentarios con el porqué de cada decisión (puertos loopback, volumen `datos_api`) |
| `plataforma/Caddyfile` | sitio `:8080` HTTP, proxy `/api/*`, `/aprende`, CSP, caché de `sw.js`/`assets` |
| `plataforma/Dockerfile` + `plataforma/entrar-api.sh` | imagen de la API y arranque (adopta el volumen, baja de privilegios) |
| `plataforma/arrancar.bat` | arranque/parada/cuentas y la espera a `/api/salud` (línea 62, trampa de M3) |
| `plataforma/.env.ejemplo` | las cinco variables y qué significa cada una |
| `plataforma/LEEME.md` | primera vez, problema→causa, y por qué el registro está abierto |
| `plataforma/respaldar.bat` + `scripts/respaldar_sqlite.py` | respaldo/restauración de base y SQLite |
| `ejecutar.bat` | la recolección diaria completa; marca del día; `--forzar` |
| `core/waf.py` | el porqué de Windows + Chrome real + ventana visible para Alcampo |
| `core/version_vigente.py` | cómo la API resuelve la versión de gold (puntero `actual.json`) |
| `plataforma/api/ajustes.py` | variables de entorno, puertos protegidos y `CESTA_REGISTRO` (línea 53) |
| `docs/DESPLIEGUE.md` | histórico (15/09/2026): reparto PC/Docker/móvil, Tailscale, Cloudflare, «cuando el PC está apagado» |
| `docs/TAILSCALE.md` | montaje de la red, ACL, nombre `cesta`, límites del plan Personal |
| `docs/OPERACION.md` | «sin VPS, sin proxies, sin pagar»; VPS de 5 EUR en la fase 4 (línea 550) |
| `docs/DIAGNOSTICO-ALCAMPO-2026-11-07.md` | el WAF de Alcampo medido el 7/11 |

## Anexo C. Qué se ha tocado en este trabajo

- **Solo** se ha creado `docs/DESPLIEGUE-VIAS-2026-11-09.md`.
- No se ha modificado `docs/DESPLIEGUE.md`, `docker-compose.yml`, `Caddyfile`, `.env`, los `.bat`
  ni ningún script. No se ha creado ningún fichero temporal.
- No hay commits ni push. No se ha hecho scraping ni se ha tocado GitHub Actions.
- Las comprobaciones con Docker, Tailscale y SSH han sido de **solo lectura**; en el `servidor` no
  se ha instalado ni escrito nada.
