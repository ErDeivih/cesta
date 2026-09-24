---
seccion: Ingeniería de datos
resumen: Las piezas del stack, por qué está cada una, qué cuesta y qué pasaría si se cambiara.
en_una_frase: Ocho piezas, tres lenguajes de configuración y ningún servicio de pago: cada una está porque resuelve un problema que existe hoy.
---

# 14 · El stack explicado: cada pieza, por qué está y qué costaría quitarla

Este capítulo es el inventario de la tecnología, y está escrito con un criterio: **de cada
herramienta se dice qué problema resuelve, cuánto cuesta mantenerla y qué se rompería si se
quitara**. Un stack no es una lista de cosas modernas: es la lista de cosas que alguien va a
tener que actualizar, entender y sustituir.

> **La lección:** una pieza entra en el stack cuando resuelve un problema **que ya tienes**, y se
> queda mientras su coste —aprenderla, actualizarla, depurarla— sea menor que el problema que
> resuelve. Todo lo demás es deuda disfrazada de currículum.

## 1. El mapa, de arriba abajo

    captura      Python + curl_cffi (+ Chrome empaquetado para el WAF)      capítulo 15
    almacén      Parquet en disco, cuatro capas (raw/bronze/silver/gold)     capítulo 02
    motores      Polars (transformar) y DuckDB (consultar)                   capítulos 02 y 06
    servicio     FastAPI + uvicorn, PostgreSQL para lo que se escribe        capítulo 11
    puerta       Caddy (un solo origen, CSP, HTTPS y estáticos)              capítulo 11
    interfaz     Vite compila la aplicación; el material es HTML generado    este capítulo
    orquesta     Programador de tareas de Windows, 06:00, un comando         capítulo 02
    empaquetado  Docker Compose, tres contenedores                           este capítulo

Ocho piezas, tres lenguajes de configuración (TOML, YAML, Caddyfile) y **ni un servicio de
pago**. Todo corre en un PC de casa.

## 2. El lenguaje y el entorno: Python y `uv`

Python sin discusión, porque es donde está todo lo que hace falta para esto: clientes HTTP con
huella de navegador, parsers de HTML, motores de columnas y una API decente. `requires-python` es
`>=3.10` y los contenedores usan `python:3.12-slim`.

`uv` hace dos cosas que aquí importan: resolver las dependencias de verdad (con un `uv.lock`
versionado) y **separar el proyecto en extras**, que es la decisión de ingeniería de este
apartado:

    base         11 dependencias   curl-cffi, httpx, selectolax, pydantic, polars, pyarrow,
                                   duckdb, python-dotenv, tenacity, tzdata, patchright
    [plataforma]  4                fastapi, uvicorn, psycopg, argon2-cffi
    [docs]        2                markdown-it-py, linkify-it-py
    dev           4                pytest, ruff, ipykernel, httpx
    extras        5                playwright, rapidfuzz, sentence-transformers, streamlit,
                                   dbt-duckdb   (el banco de pruebas, **fuera** de lo que corre)

El scraper no arrastra FastAPI, la API no arrastra el navegador del WAF y el generador del
material no arrastra ninguno de los dos. Con un proyecto que se ejecuta a diario en una máquina
de casa, **cada dependencia que no está es un sitio menos donde romperse**.

> **Trampa:** `uv sync --extra docs` **desinstala** los extras que no nombres. Se descubrió con
> 10 errores de colección en las pruebas (faltaba FastAPI) y, de propina, un `_ffi.pyd` bloqueado
> que dejó `argon2` sin importar. El comando correcto es acumulativo:
> `uv sync --extra plataforma --extra docs`. Y está escrito en `docs/OPERACION.md` porque el
> fallo no se parece a su causa: el error habla de contraseñas, no del entorno.

`tzdata` está en la lista por una razón que solo aparece en Windows: el sistema no trae la base
de zonas horarias y Polars revienta al convertir fechas. Es la clase de dependencia que no se
adivina: la trae el error, no el diseño.

## 3. La captura: cinco webs, cinco trucos

El detalle está en el capítulo 15; aquí solo el reparto de responsabilidades:

| Pieza | Qué hace | Por qué esa |
|---|---|---|
| `curl_cffi` | peticiones HTTP con la huella TLS de un Chrome real | el filtro de Akamai (DIA) mira la huella, no las cabeceras |
| `httpx` | cliente HTTP normal, en pruebas y sondeos | cuando no hay WAF que engañar, es el más cómodo |
| `selectolax` | parsear HTML rápido | DIA y Mercadona publican parte del dato en HTML, no en JSON |
| `pydantic` | validar el esquema del origen | el contrato de la fuente se declara y se comprueba, no se supone |
| `tenacity` | reintentos con espera creciente | un 503 a las 06:00 no puede tumbar el día |
| `patchright` | Chrome parcheado, con sesión y cookies | el WAF de Alcampo exige un navegador de verdad |

Cinco cadenas, cinco técnicas distintas, y **una sola pieza compartida**: `core/fetch.py` (ritmo,
reintentos, guardar el crudo antes de parsear) y `core/waf.py` (un navegador por día, cookies
reutilizadas, validadas *por resultado* y no por nombre de cookie). Esa es la abstracción que
sí merece la pena: no «el conector genérico» que nunca funciona con cinco webs distintas.

## 4. Los motores: Polars transforma, DuckDB consulta

La regla es simple y se sostiene en el 100 % de las consultas de este proyecto:

    Polars    transformar por lotes: normalizar, calcular columnas, reescribir el histórico
    DuckDB    preguntar: SQL sobre los parquet de `gold`, tanto en los análisis como en la API

Y ninguna de las dos es un servidor. Un motor **sin proceso servidor** significa que `gold` es un
directorio de ficheros que se puede copiar, comprimir y abrir en otro PC, y que no hay nada
escuchando en un puerto. El precio: el día que haya varios escritores a la vez, esta decisión se
cae, y entonces tocará hablar de otro motor. Ese día no ha llegado (hay un lector y una escritura
al día).

`pyarrow` está porque Parquet lo escribe él, y `duckdb` lee esos ficheros directamente sin
cargarlos en memoria. `polars` y `duckdb` conviven porque el proyecto usa **los dos** a
propósito: el motor se elige por lo que se va a escribir, no por moda (capítulo 02, apartado 3).

## 5. El servicio: FastAPI, PostgreSQL y Caddy

    FastAPI + uvicorn   la API: 38 endpoints, 23 sin sesión y 15 con sesión
    psycopg 3 (pool)    el acceso a PostgreSQL desde la API
    argon2-cffi         las contraseñas: Argon2id, nunca reversibles
    PostgreSQL 16       lo que se escribe: cuentas, listas, avisos, favoritos, invitaciones
    Caddy 2             el único origen (`:8080`), proxy a la API y estáticos con CSP estricta

Las razones de fondo están en el capítulo 11. Aquí interesa el **por qué de Caddy** y no Nginx:
su configuración son 41 líneas legibles, saca TLS automático si algún día hace falta, y el
`handle_path` con `try_files` es exactamente lo que se necesita para servir la aplicación, el
material de aprendizaje y la API en el mismo origen. Un Nginx equivalente serían más líneas y
más trampas de `location`, sin ganar nada a esta escala.

## 6. El material de aprendizaje: un generador propio, y por qué

El sitio de este curso no usa MkDocs, Sphinx ni Docusaurus. Se genera con
`plataforma/aprende.py` a partir de `docs/aprende/*.md`, con dos dependencias **puras de Python**
(`markdown-it-py` y `linkify-it-py`) y cero JavaScript de terceros. Las tres razones, por orden de
peso:

1. **La CSP prohíbe el script y el estilo en línea** (`script-src 'self'`). Los temas de esos
   generadores inyectan su JavaScript y su CSS dentro del HTML, y aquí eso **no se ejecuta**: el
   buscador ya se quedó muerto una vez en producción por exactamente eso (capítulo 12).
2. **El sitio tiene que abrirse desde un fichero**, con doble clic y sin servidor: `file://` y
   cero peticiones externas. Un generador con fuentes de Google y CDN de iconos no cumple eso.
3. **Cada capítulo tiene que caber en la cabeza de quien lo mantiene**: un fichero de Python de
   882 líneas frente a un tema, un fichero de configuración, plugins y una versión de Node.

Lo que se pierde, dicho claro: **no hay ecosistema**. Un resaltado de sintaxis en condiciones o
un diagrama bonito hay que escribirlos o integrarlos a mano, y eso es trabajo futuro, no una
línea de configuración.

## 7. La orquesta: el Programador de tareas, y ningún Airflow

La cadena diaria son seis pasos que corren a las 06:00 con **un comando**
(`ejecutar.bat` → `projects/cesta/run.py`). El orquestador es el Programador de tareas de
Windows, y la verdadera orquestación está dentro del propio programa:

    core/runlock.py     una sola ejecucion a la vez (dos pasadas a la vez se pisarian)
    ThreadPoolExecutor  las cinco cadenas en paralelo (esperan a la red: I/O, no CPU)
    core/runlog.py      cada pasada a `data/runs.csv`, con deteccion de deriva
    ejecutar.bat        el unico punto de entrada; la tarea solo lo llama

**Por qué no Airflow** (ni Dagster ni Prefect): aportan planificador, base de datos de estado,
interfaz web y reintentos por tarea — para seis pasos diarios en una máquina, con `run.py` que ya
es idempotente y ya reintenta el día fallido al arranque siguiente. Sería un servicio más que
mantener, con su propio PostgreSQL, para no ganar ni una comprobación. La respuesta cambiaría con
dos condiciones concretas: **más de un día de relleno hacia atrás con dependencias** (rehacer el
histórico a mano es hoy un comando explícito) o **varias máquinas**.

## 8. Los contenedores: tres, y el scraper fuera

    db    postgres:16-alpine      volumen propio; puerto publicado solo en 127.0.0.1
    api   python:3.12-slim        imagen propia (plataforma/Dockerfile), usuario sin privilegios
    web   caddy:2-alpine          sirve la aplicación compilada y `/aprende`, y hace de proxy

Dos decisiones que valen más que el `docker-compose.yml` entero:

- **El scraper no está en un contenedor**, y no es un olvido: necesita Windows y un Chrome de
  verdad para el WAF de Alcampo, y meterlo dentro rompería lo que hoy funciona. Se empaqueta lo
  que se sirve, no lo que captura.
- **`gold` va montado de solo lectura** (`:ro`) en la API. Es lo que hace que un día sin scraper
  no tumbe la web: se sigue sirviendo lo de ayer y la respuesta lo dice con la fecha del dato.

> **Trampa:** la imagen de la API instala **seis** paquetes, no once: no lleva Polars. Un import
> perezoso de un módulo que lo arrastra devolvió **500** en producción con todas las pruebas en
> verde en local, porque el servidor de desarrollo sí tiene Polars. La lección no es «no usar
> imports perezosos»: es que **el entorno de producción es parte del contrato**, y hay que
> probar contra lo que se sirve (`plataforma/prueba_produccion.py`).

## 9. Lo que NO está, y cuándo cambiaría la respuesta

| No está | Para qué se suele poner | Por qué no aquí | Cuándo sí |
|---|---|---|---|
| Spark / Dask | volumen grande | el catálogo entero cabe en memoria decenas de veces | cuando el *working set* no quepa |
| Kafka / colas | flujo continuo | hay una pasada al día, no un flujo | con datos en tiempo real |
| Airflow | orquestar | seis pasos, un comando, ya idempotente | varios días de relleno o varias máquinas |
| dbt | modelar y probar en SQL | está apuntado como extra, **no instalado**: no aporta aún nada que no haga el SQL de `pipeline.py` | cuando las transformaciones no quepan en la cabeza (`docs/PLAN.md`) |
| Kubernetes | desplegar | tres contenedores en un PC | con más de un servidor |
| Redis | caché | la API responde en 9-16 ms en caliente | cuando la latencia se mida y no cuadre |
| Almacén vectorial | búsqueda semántica | el canal de vectores se midió y se apagó (capítulo 10) | si un análisis lo justificara |
| Nube / CDN | escala | los datos son de casa y no salen de casa | con usuarios fuera de la red propia |

Esta tabla es la parte del capítulo que más veces se va a releer, porque **cada «no» tiene su
condición de cambio escrita**. Un «no» sin condición es solo una opinión.

## 10. El coste real de lo que hay

Un stack se paga en tres monedas: disco, CPU y atención. Las dos primeras se miden:

    raw      72.426 ficheros, 2.874,6 MB   (30 dias de retencion, ~338 MB por pasada)
    bronze   86 ficheros, 65,6 MB
    silver   86 ficheros, 84,0 MB
    gold     67 ficheros, 219,5 MB

Y dentro de `gold`, el desglose cuenta una historia incómoda:

    embedding.parquet          190,9 MB   52.567 vectores de un canal **apagado**
    precio_diario.parquet        9,9 MB   872.650 observaciones (19 dias x 5 cadenas)
    precio_derivado.parquet      4,6 MB   el mismo histórico con 14 columnas calculadas
    grupos.parquet               4,5 MB   57.603 ofertas, 53 columnas
    resumen.parquet              1,1 MB   los agregados que sirve la aplicación
    enlaces.parquet              0,3 MB   los pares que decidió el emparejador
    promos_por_cadena.parquet    0,0 MB   el recuento de promociones del día

**El 90,3 % de `gold` es un experimento que no se adoptó** (190,9 MB de 211,3 MB de tablas). La
lección de ingeniería no es «bórralo»: es **mide lo que guardas**. Un directorio de salida es un
coste que crece todos los días, y el día que alguien mire cuánto ocupa, tiene que poder ver de
qué es.

La tercera moneda, la atención, no se mide con un `du`: se mide en **cuántas cosas hay que
actualizar cuando algo cambia**. Aquí son tres contenedores, una tarea programada, un lockfile y
cinco extras. Si esa lista crece, el proyecto se vuelve más frágil aunque los datos sean los
mismos.

## 11. Cómo se cambia una pieza (la prueba de la sustitución)

La razón por la que este stack se puede discutir sin miedo es que **los acoplamientos son
ficheros**:

- Entre capas, el contrato es **Parquet en un directorio**. Cambiar DuckDB por Polars, o por
  Spark el día que haga falta, es cambiar el motor que lee los mismos ficheros.
- Entre la captura y el resto, el contrato es el **crudo en disco**: el parser se puede reescribir
  y reprocesar 30 días sin volver a tocar la web (`reprocesar.py`).
- Entre la API y el dato, el contrato es **SQL en un módulo**: los endpoints no saben qué motor
  hay debajo.
- Entre el material y el sitio, el contrato es **Markdown con cabecera**: el generador se puede
  sustituir sin tocar un solo capítulo.

Lo único que **no** es sustituible de un día para otro son los cinco colectores, porque cada uno
es el resultado de descubrir cómo funciona una web concreta. Es el coste reconocido de este
proyecto, y está escrito en `docs/CADENAS.md` y en el capítulo 15.

## 12. Lo que se aprende en este capítulo

- Un stack se justifica **pieza a pieza**, y cada pieza dice qué problema resuelve hoy.
- Los **extras** de dependencias son una herramienta de diseño: el scraper no necesita FastAPI y
  la API no necesita un navegador.
- Menos piezas móviles es más fiabilidad: dos motores sin servidor valen más que un clúster para
  57.603 productos.
- **El entorno es parte del sistema**: el fallo de `uv sync --extra` y el 500 por Polars ausente
  son el mismo aprendizaje con dos caras.
- Todo «no lo usamos» necesita su **condición de cambio**, o es solo una preferencia.
- Y mide lo que guardas: el 90,3 % de `gold` es un experimento apagado.
