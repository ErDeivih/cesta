# Cesta — arquitectura, tecnologias y donde va cada cosa

Para que quien implemente no tenga que decidir de nuevo lo que ya esta decidido,
ni adivinar donde poner un fichero nuevo.

---

## 1. El sistema en una pantalla

    LAS WEBS DE LAS CADENAS
      Mercadona API abierta · DIA tras Akamai · Carrefour tras Cloudflare
      Alcampo tras AWS WAF (con Chrome de verdad) · Aldi a pelo
            |
            |  projects/cesta/collectors/*.py        un fichero por cadena
            v
    data/raw/fuente=X/fecha=Y/*.json.gz              la respuesta SIN TOCAR
            |                                        30 dias, 338 MB/dia
            |  projects/cesta/pipeline.py
            v
    data/bronze/                                     29 columnas iguales
            |                                        para las cinco cadenas
            v
    data/silver/                                     unidades canonicas,
            |                                        precio por kilo calculado
            |  projects/cesta/emparejar.py
            v
    data/gold/                                       grupos, enlaces, historico,
            |                                        calidad, nutricion
            |
            |  ===== FRONTERA: el scraper acaba aqui =====
            |       montado en SOLO LECTURA
            v
    plataforma/api/    FastAPI + DuckDB       lee gold, nunca escribe
    plataforma/api/    + PostgreSQL           cuentas, listas, favoritos
    plataforma/web/    Caddy                  la interfaz
            |
            |  Tailscale (sin direccion publica)
            v
    EL MOVIL DE DAVID        EL MOVIL DE SU MADRE

**La frontera del medio es lo mas importante del diseno.** Las dos mitades solo
se hablan por el disco, asi que se pueden parar, arreglar y arrancar por
separado. Si un dia la recoleccion falla, la app sigue sirviendo lo de ayer y lo
dice en pantalla.

---

## 2. Las tecnologias, y por que cada una

### Lo que se usa

    Python 3.12          el lenguaje. 3.10 es el minimo que declara pyproject.
    uv                   gestor de entorno y dependencias. Rapido y reproducible.
    curl_cffi            cliente HTTP con huella de navegador real. Sin esto,
                         Cloudflare y Akamai cortan a la primera.
    selectolax           parseo de HTML. Diez veces mas rapido que BeautifulSoup
                         y aqui se parsean miles de paginas al dia.
    Patchright           Chrome parcheado, SOLO para el WAF de Alcampo. Es la
                         pieza mas fragil y por eso esta aislada en core/waf.py.
    Polars               transformaciones del pipeline. Columnar, rapido, y con
                         un esquema explicito que evita sorpresas de tipos.
    PyArrow / Parquet    el formato de disco. Ver docs/DATOS.md punto 2.
    DuckDB               las consultas. SQL sobre los parquet sin copiarlos.
    Pydantic             validacion del contrato de bronze.
    FastAPI              la API. Tipada, con documentacion automatica en /api/docs.
    psycopg 3            PostgreSQL. Sincrono con pool: FastAPI corre las rutas
                         no-async en un pool de hilos y se lee mucho mejor.
    argon2-cffi          hash de contrasenas. Es el recomendado hoy.
    Caddy                sirve la interfaz y hace de proxy a /api. HTTPS
                         automatico cuando haga falta.
    Docker Compose       empaqueta la plataforma. NO el scraper.
    pytest               203 pruebas.
    ruff                 formato y avisos. Configurado en pyproject.toml.

### Lo que NO se usa, y por que

    ORM (SQLAlchemy)     ocho tablas y consultas que se leen mejor en SQL. Un
                         ORM aqui esconde lo que pasa sin ahorrar nada.
    Alembic              las migraciones son ficheros .sql numerados que se
                         aplican solos al arrancar y son idempotentes. Con dos
                         usuarios, una herramienta de migraciones es andamiaje.
    React / Vue          la interfaz son cuatro pantallas sin estado compartido
                         complicado. Un framework anadiria un paso de compilacion
                         y 150 KB para no ganar nada.
    PyYAML               `core/datos/secciones.yml` lo escribimos nosotros y su
                         forma es fija. Anadir una dependencia para leer un
                         fichero propio no sale a cuenta.
    Celery / colas       no hay trabajo asincrono. El pipeline es un proceso al
                         dia lanzado por una tarea de Windows.
    Redis                la unica cache es la del panel, en memoria, indexada por
                         la fecha de gold. Un servicio mas para eso, no.
    Nginx                Caddy hace lo mismo con cinco lineas de configuracion.
    ORM/ODM para DuckDB  DuckDB se usa con SQL a pelo y esta bien asi.

**La regla general**: con dos usuarios y un PC, cada pieza de infraestructura hay
que justificarla. Lo que no se justifica, no entra.

---

## 3. Donde va cada cosa

    scrap/
    |
    +- core/                    lo que comparten scraper y plataforma
    |  +- config.py             rutas, ritmos, dias de retencion
    |  +- fetch.py              el cliente HTTP unico
    |  +- waf.py                el navegador para el WAF de Alcampo
    |  +- storage.py            leer y escribir raw y parquet
    |  +- schemas.py            EL CONTRATO de bronze, 29 columnas
    |  +- normalize.py          formatos, unidades canonicas
    |  +- matching.py           el emparejador entre cadenas
    |  +- calidad.py            la letra A/B/C y su procedencia
    |  +- promos.py             las mecanicas de oferta
    |  +- secciones.py          la seccion comun entre cadenas
    |  +- off.py                Open Food Facts
    |  +- derive.py             variaciones, minimos, maximos
    |  +- runlog.py runlock.py state.py
    |  +- datos/
    |     +- secciones.yml      849 claves -> 19 secciones
    |
    +- projects/cesta/          el scraper y el pipeline
    |  +- collectors/           UN FICHERO POR CADENA
    |  |  +- mercadona.py dia.py carrefour.py alcampo.py aldi.py
    |  +- run.py                el orquestador diario
    |  +- pipeline.py           raw -> bronze -> silver
    |  +- emparejar.py          silver -> gold
    |  +- limpiar.py            tira el crudo de mas de 30 dias
    |  +- resumen.py            que quedo en disco
    |  +- verificar_docs.py     avisa si los numeros de los .md caducan
    |  +- sondear_fichas.py     sondeo de Alcampo y Aldi (sin lanzar)
    |  +- search.py reprocesar.py
    |
    +- plataforma/              la app. NO se mezcla con el scraper.
    |  +- api/
    |  |  +- ajustes.py         lo que cambia entre portatil y contenedor
    |  |  +- catalogo.py        DuckDB sobre gold. SOLO LEE.
    |  |  +- cesta.py           donde comprar la lista, con ofertas
    |  |  +- almacen.py         PostgreSQL: cuentas, listas, favoritos
    |  |  +- panel.py           las consultas del cuadro de mando
    |  |  +- main.py            las rutas
    |  +- sql/                  001_esquema.sql, 002_invitaciones.sql...
    |  +- web/                  index.html, estilo.css, app.js
    |  +- cuenta.py             dar de alta a una persona
    |  +- Dockerfile docker-compose.yml Caddyfile .env.ejemplo
    |  +- arrancar.bat respaldar.bat
    |
    +- tests/                   una prueba por fallo que ocurrio
    +- docs/                    25 documentos
    +- data/                    NO va a git
       +- raw/ bronze/ silver/ gold/ master/ externo/ respaldos/
    |
    +- ejecutar.bat             la recoleccion diaria
    +- pyproject.toml           dependencias y configuracion de ruff

### Donde poner un fichero nuevo

    ¿lo usan las dos mitades?            -> core/
    ¿es una cadena nueva?                -> projects/cesta/collectors/
    ¿es un paso del pipeline?            -> projects/cesta/
    ¿es una ruta de la API?              -> plataforma/api/, y si crece,
                                            plataforma/api/rutas/<tema>.py
    ¿es una tabla nueva?                 -> plataforma/sql/00N_<tema>.sql
    ¿es una tabla de datos a mano?       -> core/datos/
    ¿es una decision que hay que
      recordar dentro de seis meses?     -> docs/, y enlazada desde LEEME-AGENTE

---

## 4. Las reglas del codigo

**Castellano.** Nombres de funcion, variables, comentarios y mensajes. Es el
idioma de quien lo mantiene.

**Los comentarios explican POR QUE, no QUE.** Si hay un numero raro, al lado va
la medicion que lo justifica:

    MERMA_ACEPTABLE = 0.10   # el 9 de septiembre una captura parcial tiro
                             # 43.643 productos buenos por quedarse un 3 % corta

**Ninguna correccion de dato sin confirmacion independiente.** El patron esta en
`pipeline.py`: el nombre dice "pack 24 x 33 cl" pero solo se multiplica si el
precio resultante cuadra al 5 % con el que publica la cadena. De 211 candidatos
se corrigieron 110; los 101 que no cuadran se quedaron como estaban.

**Cada valor viaja con su procedencia.** `calidad_origen` dice si la letra salio
de leer ingredientes o de ordenar por precio. Sin eso, el estudio de marca
blanca habria salido publicado al reves.

**Un fallo se arregla con una prueba.** Las 203 que hay existen porque algo
fallo.

**El dinero en centimos enteros.** `precio_cent: 345`. Nunca decimales en euros.

---

## 5. Los tres contratos que no se rompen

### 5.1 `ESQUEMA_BRONZE` (core/schemas.py)

29 columnas iguales para las cinco cadenas. Si una empieza a publicar un campo
nuevo, **o entra en el contrato para todas o no entra**. Los tipos se fijan aqui
para que una columna que sale entera a None no se quede como Null y rompa la
union de esquemas al juntar dias o cadenas.

### 5.2 La frontera gold

El scraper escribe. La plataforma lee, **montada en solo lectura**. No hay
excepciones: si la app necesita escribir algo, va a PostgreSQL.

### 5.3 `calidad` contra `gama`

La API devuelve `calidad` **solo** si la letra viene de leer ingredientes, y
`gama` si viene de ordenar por precio. Nunca las dos. El 76,9 % son del precio.

---

## 6. Los comandos

    .\ejecutar.bat                  la recoleccion diaria (una vez al dia)
    .\ejecutar.bat --forzar         otra vez hoy, a proposito
    plataforma\arrancar.bat         levantar la plataforma
    plataforma\arrancar.bat logs    ver que pasa
    plataforma\arrancar.bat cuenta <usuario> "<Nombre>"
    plataforma\respaldar.bat        respaldar PostgreSQL

    uv run pytest                                   203 pruebas
    uv run ruff check .                             limpio
    uv run python -m projects.cesta.emparejar --medir   57 % de aciertos
    uv run python -m projects.cesta.verificar_docs      los .md cuadran

**El 57 % es el indicador de salud del proyecto.** Se mide antes y despues de
tocar el emparejador. La ultima vez que se cambio sin medir, la cobertura cayo
del 53 % al 43 % y costo dias entenderlo.

---

## 7. Lo que falta montar, y no es codigo

    git             el proyecto NO esta en control de versiones. El .gitignore
                    existe desde el 7 de septiembre pero no hay repositorio.
                    Hoy se tocan veinte ficheros sin poder ver que cambio.
    HTTPS           el escaner de codigo de barras necesita `getUserMedia`, que
                    solo funciona en HTTPS o localhost. Con Tailscale en http://
                    no va. Se resuelve con `tailscale cert`, y hay que
                    comprobarlo ANTES de programar el escaner.
    la primera
      ejecucion     la plataforma NUNCA se ha levantado con Docker. Todo lo
                    probado son las piezas por separado y la API contra gold
                    real, sin PostgreSQL.
