# Operacion: sin VPS, sin proxies, sin pagar

Restricciones: nada de proxies residenciales, nada de VPS por ahora, GitHub Actions
como opcion cuando toque, y local mientras tanto.

## Antes de desplegar una imagen nueva: la prueba de punta a punta

Las pruebas de `tests/` sustituyen PostgreSQL a proposito, asi que **el SQL y las
migraciones no los ejecuta nadie** hasta que arranca el contenedor. Para eso esta
`plataforma/prueba_e2e.py`, que corre todo contra una base **desechable** (el 5434, que no
es el de casa: el de Cesta no publica su 5432) y con el gold de verdad:

    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    uv run python -m plataforma.prueba_e2e
    docker rm -f cesta-prueba-db

Aplica las seis migraciones, recorre las rutas nuevas y **falla con un mensaje claro** si
algo no cuadra. La primera vez que se corrio encontro dos fallos que las pruebas unitarias no
podian ver: `/api/bajadas?solo_mios=true` sin sesion contestaba que habia filtrado sin
filtrar, y **la API no arrancaba con dos listas de casa** (un indice que un fichero viejo
resucitaba en cada arranque). Salida esperada: **TODO BIEN**.

## Y despues de desplegar: la interfaz **servida**, no la de desarrollo

`prueba_navegador` mide la aplicacion en el servidor de desarrollo (`localhost:5173`, con el
proxy de Vite) y contra un PostgreSQL de pruebas. Eso **no es lo que se sirve**: lo que se
sirve es el paquete compilado (`web/dist`), con **las cabeceras de Caddy** -- incluido el
`Content-Security-Policy`, que en desarrollo no existe -- y contra la base de casa.

    uv run python -m plataforma.prueba_produccion

Abre `http://127.0.0.1:8080` (o lo que diga `CESTA_PRODUCCION`), y comprueba: que la
aplicacion monta y **el CSP no bloquea nada**, que el buscador encuentra y la ficha contesta
con su frase, las tres pantallas nuevas del panel, la primera vez con una cuenta de verdad
(la aplicacion funcionando, no un cartel), que al tachar salen **las dos secciones** con el
numero en la barra de abajo, y que la cuenta de prueba **se borra al final**
(`DELETE /api/yo`): la base de casa no se queda con basura.

Existe por un fallo concreto y del 24 de septiembre de 2026: el dia que se cambio el montaje
a `web/dist`, la API del contenedor devolvio **500** en `/api/ofertas-dudosas`

    File "/app/plataforma/api/movimientos.py", line 178, in _ventana_base
    ModuleNotFoundError: No module named 'polars'

porque un import **dentro de una funcion** de `core.derive` (que arrastra polars) si se
llamaba, y polars no esta en la imagen de la API. La prueba estatica de la imagen no lo vio
-- mira solo los imports de arriba -- y la puerta del navegador tampoco, porque corria contra
el uvicorn del PC, donde polars si esta. Las dos se han arreglado en el mismo sitio donde
estaba el fallo: el numero compartido se mudo a `core/comparacion.py` (que la API si puede
importar) y `tests/test_imagen_api.py` ahora mira **todos** los imports, esten donde esten.

## Y la interfaz, en un navegador de verdad

Lo de arriba comprueba el servidor. La pantalla se comprueba con
`plataforma/prueba_navegador.py`, que abre la aplicacion en un movil de 390 x 844 con
`has_touch` (el navegador de `patchright`, que ya esta puesto para los colectores), hace el
recorrido de las **cuatro preguntas** y mide cuanto tarda cada paso:

    docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
        -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run uvicorn plataforma.api.main:app --host 127.0.0.1 --port 8099
    cd plataforma/web/app; $env:CESTA_API='http://127.0.0.1:8099'; npm run dev
    uv run python -m plataforma.prueba_navegador

**La interfaz tiene que hablar con la API nueva**: la imagen que corre en el 8080 puede ser
mas vieja que el repositorio. La cuenta es **fija** (`prueba-navegador`) y no nueva en cada
pasada, porque la API limita cuantas se crean por hora (`ALTAS_POR_HORA`).

Cubre las cuatro preguntas (con sus tiempos), el pasillo pegado, el «Deshacer», los cambios
sin cobertura, los avisos, **el escaner con un codigo de verdad**, **el enlace de invitacion
abierto por una segunda persona** (otra sesion, que entra o crea su cuenta en la propia
pantalla del enlace y acaba dentro de la lista), **las cuatro respuestas dentro de la primera
pantalla de un movil** (la banda util son 109..787 px de 844: lo que obligue a desplazar la
pantalla no se lee en quince segundos), **todo lo que se pulsa medido** en las ocho pantallas
donde se puede acabar de pie (incluidas la ficha del producto y el escaner, que entraron al
encontrar ahi cuatro objetivos de 19 px), **que ninguna pantalla se deslice de lado**, **que
con la API a 500 cada pantalla lo diga con palabras y deje reintentar** (la cesta era la unica
sin boton: escribia su error a mano) y **el contraste del texto pintado en los dos temas**,
tambien en la ficha del producto. En su primera pasada encontro tres cosas que
leyendo el codigo no se ven -- React Query pausando los cambios sin cobertura, la frase de
«¿esto esta caro?» ausente en la pantalla a la que se llega buscando, y el arranque roto con
dos listas de casa --, asi que **es lo que hay que correr cuando se toque la interfaz**. No
cierra la condicion (a) de la barra: eso es una persona con un movil
(`docs/PRUEBA-15-SEGUNDOS.md`).

Las **dos cuentas** de esta prueba son fijas (`prueba-navegador` y `prueba-invitada`), y por
el mismo motivo: cada pasada corre contra la misma base. Se ha corrido **tres veces seguidas**
con el mismo resultado (`TODO BIEN`), que es lo unico que hace fiable una puerta.

## Fase 1: todo en el PC, y el almacen tambien

Medido el 6 sep 2026 en F:\aprendizaje\scrap: **158 GB libres de 209 GB**.
Con eso el almacenamiento deja de ser un problema durante anos.

Consumo estimado, con las seis cadenas y catalogos completos:

    crudo comprimido (gzip)   ~25 MB/dia   ->  ~9 GB/ano
    bronze (parquet)           ~4 MB/dia   ->  ~1,5 GB/ano
    gold (historico + derivados)            ->  ~100 MB/ano
    ---------------------------------------------------------
    total                                      ~11 GB/ano

**Mas de diez anos de historico caben en el espacio libre de hoy.** Asi que la
decision es guardar el crudo entero y para siempre, que es exactamente lo que
permite reprocesar tres anos de datos en cinco minutos cuando cambies un parser.

Nada de Hugging Face, ni R2, ni Supabase en esta fase. Solo:

    F:\aprendizaje\scrap\data\
      raw\      fuente=<x>\fecha=<YYYY-MM-DD>\*.json.gz     inmutable
      bronze\   parquet 1:1 con el crudo, tipado
      silver\   normalizado y comparable
      gold\     precio_diario, precio_derivado, resumen
      warehouse.duckdb    vistas SQL sobre todo lo anterior
      runs.csv            una fila por ejecucion
      ejecuciones.log     salida del Programador de tareas

Lo unico que conviene desde el primer dia: que `data\` **no** este dentro de una
carpeta sincronizada con OneDrive o Drive. Sincronizar miles de ficheros pequenos
cada madrugada es la forma mas rapida de que el PC vaya lento y de que la nube se
llene sin que te enteres.

Copia de seguridad, cuando haya algo que perder: el crudo es lo unico irrecuperable.
Un `robocopy` semanal de `data\raw` a un disco externo cubre el riesgo entero.

## Cuando pasar a GitHub Actions (fase 2)

### El numero que decide el reparto

Plan Free de GitHub: **2.000 minutos/mes en repos privados, ILIMITADO en repos
publicos** con runners estandar.

Presupuesto diario estimado:

    Mercadona    ~6 min    API, 2 req/s
    Aldi         ~8 min    API por lotes
    Alcampo     ~12 min    SSR, paginas grandes
    DIA         ~20 min    SSR + ritmo lento por Akamai
    Carrefour   ~90 min    Crawl-delay 60 -> 1 req/min
    transformar  ~5 min
    ------------------------------
    total       ~141 min/dia = ~4.230 min/mes

En repo privado eso son **el doble del limite**: no cabe, y ni siquiera por poco.
En repo publico no cuesta nada. Solucion: **repo publico con el CODIGO, datos fuera
del repo**. Publicar el codigo no tiene ningun problema; publicar un volcado del
catalogo ajeno si lo tendria (derecho sui generis de bases de datos).

### El problema que casi nadie preve: la IP

Los runners de GitHub salen por IPs de datacenter de Azure. Cloudflare (Carrefour) y
Akamai (DIA) las tienen fichadas. Es muy probable que esas dos cadenas devuelvan 403
desde Actions aunque funcionen perfectamente desde tu casa.

Sin pagar proxies, la solucion es un **self-hosted runner en tu PC**: el mismo YAML,
ejecutandose en tu maquina, con tu IP residencial, con minutos ilimitados porque no
consume del plan. Se instala desde Ajustes del repo, corre como servicio de Windows
y se registra con etiquetas.

De ahi salen los dos trabajos de `.github/workflows/diario.yml`:

    abiertas    -> ubuntu-latest        Mercadona, Aldi, Alcampo
    protegidas  -> [self-hosted, casa]  DIA, Carrefour

Si el PC esta apagado, el trabajo `protegidas` queda en cola y esas dos cadenas se
saltan el dia. El trabajo `transformar` lleva `if: always()` y sigue adelante con lo
que haya; la interfaz marca esos precios como "de ayer". Degradacion honesta en vez
de fallo total.

Y cuando quieras VPS, mueves el runner al VPS y no tocas ni una linea del workflow.

### Dos trampas de los cron de GitHub

1. **Los workflows programados se desactivan solos tras 60 dias sin commits.**
   Resuelto con `.github/workflows/keepalive.yml`, que hace un commit vacio
   dos veces al mes.
2. **El cron se retrasa en horas punta**, a veces bastante. Por eso el horario es
   `17 4 * * *` y no `0 5 * * *`: los minutos en punto son los mas saturados. Si el
   dato tiene que estar si o si a una hora, el cron no es la herramienta; para este
   caso, con que este "por la manana", sobra.

### Donde viven los datos cuando salgan del PC (fase 3)

| Que | Donde | Limite | Por que ahi |
|---|---|---|---|
| Codigo | GitHub, repo publico | — | minutos ilimitados |
| raw + historico Parquet | dataset PRIVADO en Hugging Face | de sobra | git-lfs, versionado, gratis, y el dia que quieras publicarlo es un interruptor |
| Estado de la app | Supabase free | **500 MB de BD**, 5+5 GB de egress | ya lo tienes; da auth y Postgres |
| Web | Vercel hobby | — | ya lo tienes |

Cuentas de tamano, que es lo que decide el reparto:

    6 cadenas x ~3.000 productos x 365 dias = ~6,5 M filas/ano
    en Postgres con indices  ~700 MB - 1 GB  -> NO cabe en el free (500 MB)
    en Parquet comprimido     ~40 - 80 MB    -> cabe en cualquier sitio

Por tanto: **el historico completo NUNCA entra en Supabase.** En Postgres van solo
usuarios, listas, favoritos, grupos, la tabla de "precios de hoy" y los agregados ya
calculados (percentil, min/max, tendencia). Eso son unas decenas de MB y cabe de
sobra. El historico entero vive en Parquet y se consulta con DuckDB — desde el
backend, o directamente desde el navegador con DuckDB-WASM cuando quieras un grafico
de dos anos sin tocar el servidor.

Detalle: **los proyectos free de Supabase se pausan tras 7 dias de poca actividad.**
El job diario escribe todos los dias, asi que no se pausa nunca. Pero si paras el
proyecto un mes, hay que reactivarlo a mano.

## Escalera de ejecucion, por fases

    Fase 1   todo en tu PC: recoleccion, pipeline y almacen. Cero configuracion.
    Fase 2   repo publico + Actions para las tres abiertas; las dos protegidas
             siguen en tu PC via self-hosted runner.
    Fase 3   web en Vercel + Supabase. Sigue sin haber VPS.
    Fase 4   si algun dia molesta depender del PC: VPS de 5 EUR, mueves el runner.

No hay ningun punto de esta escalera en el que haga falta pagar proxies. Si algun
dia Carrefour bloquea tambien tu IP domestica, la respuesta antes de pagar es bajar
el ritmo y scrapear menos categorias, no comprar IPs.

## Que hago yo cuando algo se rompe

Sin preguntar: repetir el reconocimiento en la web afectada, ver si cambio la
estructura, ajustar el parser, y si el problema es de bloqueo subir un peldano de la
escalera (curl_cffi -> impersonate distinto -> ritmo mas lento -> Patchright con
perfil persistente). Solo te consulto si la unica salida que queda cuesta dinero o
cambia el alcance del proyecto.

---

# Rehacer el pasado sin tocar la red (17 de septiembre de 2026)

Dos herramientas, y la diferencia entre ellas importa.

## `reprocesar.py` — rehace **bronze** desde `data/raw`

```
uv run python -m projects.cesta.reprocesar --fuente aldi
uv run python -m projects.cesta.reprocesar --fuente dia --fecha 2026-09-17
uv run python -m projects.cesta.reprocesar --fuente mercadona --forzar
```

Para esto se guarda el crudo: cuando cambia el parser, el historico entero se
rehace en segundos. Funciona con las **cinco** cadenas desde hoy; hasta esta
tarde Carrefour y DIA (el 42 % del catalogo) no se podian reprocesar porque
guardan HTML con extension `.json.gz`.

**Se niega a escribir si el bronze nuevo pierde datos.** Compara columna a
columna con el anterior y avisa:

```
  fecha=2026-09-17: NO se escribe, el bronze nuevo pierde datos:
      ean: 4317 -> 0
      origen: 1443 -> 0
      (si es lo que quieres, repite con --forzar)
```

El margen es del 10 %: que un dia haya un 5 % menos de productos es normal, que
una columna se quede a cero no.

## `rehacer_maestro.py` — rehace **las fichas maestras** desde `data/raw`

```
uv run python -m projects.cesta.rehacer_maestro --fuente dia
uv run python -m projects.cesta.rehacer_maestro --fuente mercadona --ver
uv run python -m projects.cesta.rehacer_maestro --fuente dia --segundos 90
```

El EAN, los ingredientes, los alergenos, el origen, la tabla nutricional y la
caducidad **no vienen del listado**: vienen de la ficha de cada producto y viven
en `data/master/<cadena>.json.gz`. Ese fichero solo lo escribia el colector al
scrapear, asi que mejorar el lector de fichas no servia de nada hasta la
siguiente pasada completa: **5.410 peticiones a DIA (Akamai) y 4.378 a
Mercadona**.

Paso de verdad: el 16 de septiembre se enseno a `dia.py` a leer la tabla
nutricional, los dias de caducidad, el envase y el tipo de producto. Cinco
campos, cero productos con ellos, porque el maestro seguia siendo el del dia 7. Y
las fichas del dia 7 estaban guardadas enteras en `data/raw` todo el tiempo.

Con esta herramienta, el 17 de septiembre, sin una sola peticion:

```
dia: 5.533 fichas leidas del crudo
    + nutricion             0 -> 3.737
    + tipo_producto         0 -> 5.533
    + envase_txt            0 -> 5.533
    + dias_caducidad        0 -> 4.261
    + peso_neto_g           0 -> 4.756

mercadona: 4.378 fichas leidas del crudo
    + conservacion          0 -> 1.804
    + descripcion           0 -> 4.378
    + envase_txt            0 -> 3.772
    + grado_alcohol         0 ->   183
```

### Como encuentra las fichas si el nombre esta hasheado

`save_raw` guarda cada respuesta como `sha1(clave)[:12]-sha256(cuerpo)[:12]`, asi
que la clave no se puede leer del nombre. Pero si se puede ir al reves: la clave
de una ficha es `product-<id>`, los ids estan en bronze, se calcula el hash de
cada clave posible y se busca el prefijo. De los 5.411 productos de DIA aparecen
5.410.

### Es reanudable

Leer 5.410 ficheros pequenos tarda varios minutos si `data/` esta en un disco
lento o en un recurso de red. Con `--segundos N` se para, guarda el avance en
`data/master/<cadena>.parcial.json.gz` y al volver a lanzarlo continua. Sin ese
`--segundos` va de una tirada.

### La regla

> `data/master` guarda **lo que dice la cadena**. Normalizar es trabajo de
> `a_registro`, que es la frontera del contrato.

Por eso el envase se guarda como `envase_txt` ("frasco", "Tarro") y se traduce al
vocabulario comun en bronze. Cambiar el vocabulario no obliga a releer 5.410
fichas.

## El orden completo de una recuperacion

```
1. rehacer_maestro --fuente <cadena>     # si el cambio afecta a la ficha
2. reprocesar --fuente <cadena>          # bronze
3. python -m projects.cesta.pipeline     # silver + gold historico
4. python -m projects.cesta.emparejar    # grupos, calidad, enlaces
5. python -m projects.cesta.verificar_docs
```

Los pasos 3 y 4 tardan un par de minutos cada uno con el catalogo completo.

---

## Los avisos en la cadena: `projects/cesta/avisos.py`

```
uv run python -m projects.cesta.avisos
```

Es el paso que pide el §6 del encargo (*"evaluarlas en la cadena diaria, despues del
pipeline"*): mira las alertas pendientes contra gold y deja en `data/avisos.json` lo que el
resumen tiene que contar. `run.py` lo llama solo, entre `emparejar` y el resumen, asi que
**no hay que cambiar `ejecutar.bat`** ni la tarea de las 06:00.

**De donde saca la base.** Si hay un `CESTA_POSTGRES` en el entorno, ese manda. Si no, lee
`plataforma/.env` -- el fichero de Docker Compose -- y arma el DSN con la clave de ahi, contra
`127.0.0.1:5432` (que es donde la publica `docker-compose.yml`, **solo en el PC**). Asi la
cadena no necesita una segunda copia de la clave, que se quedaria vieja el dia que se cambie
la de verdad. Si no hay ni entorno ni fichero, dice "no lo se" y sigue.

Con la base delante, medido el 24 de septiembre de 2026 sobre el gold del 23:

```
[avisos] avisos: 0 saltaron hoy | 0 en esta pasada de 0 miradas (11:03)        1,1 s
```

Y sin ella (por ejemplo con la base parada, que es como estaba antes de publicar el puerto):

```
[avisos] avisos: no lo se -- la base de datos no se alcanza desde aqui (mirada en
         `plataforma/.env` y en `CESTA_POSTGRES`: ...): ConnectionTimeout         6,5 s
```

**Devuelve 0 en los dos casos**, y eso es a proposito: detras van el resumen, la comprobacion
de precios y `verificar_docs`, y una linea de resumen no puede contar un dia bueno como
fallido.

Para verlo funcionando de verdad esta la prueba de punta a punta, que corre contra un
PostgreSQL de verdad:

```
docker run --rm -d --name cesta-prueba-db -e POSTGRES_PASSWORD=prueba \
    -e POSTGRES_USER=cesta -e POSTGRES_DB=cesta -p 127.0.0.1:5434:5432 postgres:16-alpine
uv run python -m plataforma.prueba_e2e
docker rm -f cesta-prueba-db
```

Esa misma prueba cronometra **abrir la pantalla de avisos**, y ahi hay una trampa que conviene
conocer antes de medir nada por `TestClient`: el andamio de la prueba (httpx en el mismo
proceso) tarda **409 ms en un endpoint que no hace nada**, asi que los 469 ms que se midieron
primero eran la prueba midiendose a si misma. Lo que cuesta la aplicacion:

```
en frio (gold recien cambiado)     47 ms
en caliente (lo que vive alguien)  13 ms (0-16)
```

---

## El banco de ejes contra un modelo: `projects/cesta/laya_ejes.py`

```
uv run python -m projects.cesta.laya_ejes --sin-modelo     # solo el banco, sin nada instalado
```

Eso ultimo no necesita ni modelo ni red: lee el gold, coge hasta 8 nombres por cada
(eje, valor) que las listas a mano de `core/atributos.py` **ya declaran**, y enseña el
banco. Es la mitad barata del experimento de `docs/LAYA.md`, y sirve para cualquier
modelo al que se le quiera preguntar lo mismo.

El dia que haya un modelo instalado, la receta entera esta en la cabecera del modulo.
En corto, y **fuera del entorno del proyecto**:

```powershell
$d = "$env:TEMP\laya-prueba"
uv venv "$d\venv" --python 3.12
uv pip install --python "$d\venv\Scripts\python.exe" laya duckdb tzdata
$env:USE_TF='0'; $env:HF_HOME="$d\hf"     # USE_TF=0: sin el, transformers busca TensorFlow
& "$d\venv\Scripts\python.exe" -m projects.cesta.laya_ejes --por-valor 8 --json data\laya_ejes.json
```

**`laya` no entra en `pyproject.toml`**, y no es un descuido: son 2,1 GB con torch y la
cadena de las 06:00 no puede depender de eso. Por eso se importa **dentro** de la
funcion que mide, y `tests/test_laya_ejes.py` comprueba que importar el modulo no lo
arrastra. Los tres paquetes de arriba son el minimo medido: `tzdata` es lo que pide
`core/config.py` en un entorno sin la zona horaria del sistema.

Con el modelo delante, medido el 24 de septiembre de 2026 (gold del 24, 215 nombres,
316 declaraciones, CPU):

```
acuerdo sobre lo declarado   231  (73.1 %  -- la barra pide 97 %)      2,16 s por peticion
generosidad del enunciado: 12 de 27 valores llevan dentro un patron de la lista
    donde el enunciado copia el patron       135 pares,  68.1 % de acuerdo
    donde el enunciado no copia nada         181 pares,  76.8 % de acuerdo
```

Lo que hay que mirar de esa salida, en este orden: el **acuerdo**, las **abstenciones**
(no es lo mismo decir «no lo dice» que decir otro valor), las **declaraciones donde la
lista calla** —que son las que cortarian comparaciones si entraran como guarda—, y por
ultimo los dos listados enteros del JSON (`desacuerdos` y `todas_las_invenciones`), que
estan para poder auditar uno a uno sin volver a correr el modelo. **Un desacuerdo es o
un fallo del modelo o un fallo de la lista**, y en la primera pasada 27 de los 85 eran
nuestros.

---

## `pipeline --rehacer-historico` — rehace **la serie de precios** desde bronze

```
uv run python -m projects.cesta.pipeline --rehacer-historico
```

El pipeline normal se queda con la instantanea mas reciente de cada cadena y la
**anade** a `gold/precio_diario.parquet`. Es lo correcto a diario, pero significa
que el historico no se calcula: se acumula, y sólo existe en ese fichero. Con
esto se recorre bronze dia a dia y se reescribe entero.

Cuando usarlo:

- `gold/precio_diario.parquet` se ha corrompido, borrado o quedado a medias.
- Ha cambiado la logica de `a_silver` y se quiere una serie coherente, calculada
  toda con el codigo de hoy. Ojo: el historico acumulado tiene cada dia escrito
  por la version del codigo de ese dia, y eso se nota en decenas de filas por
  cadena y dia.

Tarda un par de minutos con trece dias de bronze. **Reescribe el fichero entero**:
lo que no este en bronze, no sobrevive. Si el resumen avisa de filas huerfanas
(ver abajo), esas filas se pierden — apartalas antes si hacen falta.

## Una cadena termina bien y no deja bronze

Lo dice la propia ejecucion, **antes** del pipeline, que es cuando todavia tiene
arreglo barato. Y distingue los dos casos:

```
[alcampo] termino bien pero su bronze de hoy esta apartado en data/debug/descartados (sin frescos).
[alcampo]   arreglo:  uv run python -m projects.cesta.reprocesar --fuente alcampo --fecha 2026-09-18
```

```
[alcampo] TERMINO BIEN PERO NO HAY BRONZE DE HOY (2026-09-18), ni en su sitio ni entre los descartados.
[alcampo]   arreglo:  uv run python -m projects.cesta.reprocesar --fuente alcampo --fecha 2026-09-18
```

El segundo no deberia pasar nunca, porque bronze no se borra. Si sale, es que algo
de fuera del proyecto ha tocado la carpeta.

Esa cadena deja de contar como buena, asi que sale en `fallaron:` y en el
veredicto del dia. El arreglo que imprime funciona mientras el crudo del dia siga
en disco (`data/raw`, treinta dias de retencion), y hay que lanzarlo **antes** de
que el crudo caduque.

Una cadena que se nego a escribir a proposito -- porque el control de cobertura
vio media tienda desaparecida -- ya devuelve error por su cuenta y no pasa por
aqui.

## Filas del historico sin bronze en su sitio

El resumen diario lo dice solo, y distingue apartado de perdido:

```
  historico: 593509 filas, 13 dias acumulados
  nota: 20559 filas de alcampo del 2026-09-18 vienen de una captura apartada
        (sin frescos); el bronze esta en data/debug/descartados
```

Eso es informacion, no alarma: la captura se rechazo a proposito, el dato esta
guardado y el historico conserva los precios que si se capturaron.

Lo otro si es alarma:

```
  AVISO: 20559 filas del historico sin bronze y sin rastro en descartados.
         No se pueden recalcular desde nada:
      alcampo    2026-09-18  20559 filas
```

Si sale esto y el crudo del dia sigue en `data/raw` (treinta dias de retencion),
`reprocesar --fuente <cadena> --fecha <dia>` devuelve el bronze a su sitio.

---

# Que hacer cuando una captura sale mal (18 de septiembre de 2026)

El orden importa, y el paso 2 es el que se olvida.

## 1. Apartar el bronze malo, no borrarlo

**Bronze no se borra nunca.** Es el original tipado de cada dia: el crudo caduca a
los treinta dias y gold se puede recalcular, pero bronze no se recupera de ningun
sitio. Desde el 18 de septiembre de 2026 eso no es solo una costumbre, lo dice el
codigo: `storage.comprueba_borrable()` revienta con `BorradoProhibido` si algo
intenta borrar dentro de `bronze` o de `gold`.

La forma correcta:

```
uv run python -c "from core import storage; from pathlib import Path; \
  print(storage.aparta(Path('data/bronze/fuente=alcampo/fecha=2026-09-18'), 'sin frescos'))"
```

o, a mano, lo mismo:

```
mv data/bronze/fuente=alcampo/fecha=2026-09-18 \
   data/debug/descartados/alcampo-2026-09-18-sin-frescos
```

Apartado y con el motivo en el nombre, que **no es decoracion**: el resumen lo lee
de vuelta (`cobertura.apartados()`) y por eso sabe distinguir un dia apartado a
proposito de un dia perdido de verdad. Sin el motivo en el nombre, el aviso diario
no puede decirte cual de las dos cosas es.

El crudo **no se toca**: sigue en `data/raw` y de ahi se puede reprocesar el dia
que se entienda que paso.

### Lo que este paso NO hace, y hay que saberlo

Apartar el bronze y tirar el silver huerfano **no quita las filas de gold**. Si el
pipeline ya habia corrido con la captura mala, el historico se queda con ellas.

Casi siempre eso es lo que se quiere: son precios reales de ese dia para los
productos que si se capturaron, y tirarlas abriria un hueco para toda la cadena en
vez de solo para lo que falto. Pero hay que **saberlo**, y por eso el resumen lo
dice cada dia en una linea. Si algun dia se quiere una serie limpia del todo:
`pipeline --rehacer-historico`, que reconstruye desde bronze y deja fuera lo
apartado.

## 2. Tirar el silver huerfano (esto es lo que se olvida)

El pipeline escribe el silver bajo la fecha **de su bronze**. Al rehacerlo tras
apartar el bronze del 18, el silver bueno se escribe bajo el 17... y el silver
roto del 18 sigue ahi. Y el emparejador coge **el mas reciente de cada cadena**.

Resultado: el catalogo vuelve a salir roto y parece que el arreglo no funciono.

Desde hoy lo hace el pipeline solo:

```
  se tira el silver huerfano de alcampo fecha=2026-09-18: su bronze ya no esta
```

Si se hace a mano, es `rm -rf data/silver/fuente=<cadena>/fecha=<la mala>`.

## 3. Rehacer y comprobar

```
uv run python -m projects.cesta.pipeline
uv run python -m projects.cesta.emparejar
uv run python -m projects.cesta.resumen
```

En el pipeline tiene que salir la cadena con su fecha vieja y el aviso
`<- de otro dia`. En el resumen, `SIN REFRESCAR HOY: alcampo (2026-09-17)`.

## 4. Comprobar que la forma del catalogo ha vuelto

```python
import polars as pl, collections
g = pl.read_parquet("data/gold/grupos.parquet")
d = g.filter(pl.col("fuente") == "alcampo")
print(collections.Counter(c.split(" > ")[0] for c in d["categoria"].to_list()).most_common(8))
```

Comparar con el dia anterior. Es lo mismo que hace `core/cobertura.py`
automaticamente, pero conviene mirarlo con los ojos una vez.

## El atajo para iterar

`emparejar` tarda minuto y medio porque recorre 16,7 millones de pares. Cuando el
cambio **no toca ninguna** de las seis columnas que mira el emparejador (fuente,
nombre, marca, cantidad, unidad_canon, ean):

```
uv run python -m projects.cesta.emparejar --reusar-enlaces
```

De 90 s a 9 s. Y no hay riesgo de colar enlaces de otro catalogo: se guarda una
firma de la secuencia entera de (cadena, id) en `data/gold/enlaces_huella.json` y
si no coincide se recalculan. La primera version solo comprobaba que el indice
mas alto cupiera, y eso **no basta**: un catalogo de otro dia con el mismo numero
de filas pasa esa prueba y tiene los productos en otras posiciones.
