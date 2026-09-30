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

Aplica **todas las migraciones de `plataforma/sql`** (diez el 30 de septiembre de 2026; antes
decia «las seis», y ese número se quedó viejo al tercer fichero nuevo: por eso ahora se dice sin
contar), recorre las rutas nuevas y **falla con un mensaje claro** si
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

**Y mide tambien el material de aprendizaje pulsandolo**, no solo leyendolo: que cada bloque de
codigo tenga su boton de copiar y que al pulsarlo conteste (con el portapapeles o, por http, con
«Cópialo a mano» y el codigo seleccionado), que el capitulo traiga sus migas de pan, y que la
tarjeta de «siguiente» lleve al capitulo que anuncia. **Y con el teclado**, que es de lo que vive
un sitio de documentacion: «/» lleva el foco al buscador, `Escape` cierra la lista de resultados,
una busqueda sin resultados lo dice («Nada con esas palabras», la cara vacia que no medía nadie) y
el indice lateral esta plegado en el movil y desplegado en escritorio. Y desde el 28 de septiembre
de 2026 **una pasada de escritorio**, a 1440 x 900, porque hasta ese dia todo lo de esta puerta era
un movil: ahi se comprueba que la barra de secciones de arriba sale y lleva a los seis destinos, que
los resultados vuelven a ser **una tabla con sus columnas** en vez de filas apiladas, y que ninguna
de las cinco pantallas se desliza de lado.

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

## El material de aprendizaje: `plataforma/aprende.py`

El proyecto tiene 1,1 MB de documentos (el registro del día a día, los informes, la operación)
y, aparte, **un curso** en `docs/aprende/`: capítulos en orden que explican la parte técnica y
la teórica con los números medidos de aquí como caso práctico. `plataforma/aprende.py` los
junta y los pinta **con la forma de un sitio de documentación**: barra de arriba con buscador,
índice lateral por secciones, índice de la página a la derecha, migas de pan, tarjetas de
anterior/siguiente, botón de copiar en cada bloque de código, avisos destacados y modo oscuro.

### Añadir o cambiar un capítulo

Un fichero nuevo en `docs/aprende/`, con su cabecera:

```markdown
---
seccion: Algoritmos y evaluación
resumen: Una línea que sale en el índice, en la portada y en el buscador.
en_una_frase: La idea del capítulo en una frase, para quien llega con prisa o desde el móvil.
---

# 16 · El título del capítulo
```

**La sección tiene que estar en `SECCIONES`** (`plataforma/aprende.py`); si no, el capítulo sale
en «Otros» y el generador lo avisa por consola. El número del nombre del fichero manda en el
orden dentro de su sección. No hay que tocar el generador ni el índice: aparece solo, y lo
comprueban las 20 pruebas de `tests/test_aprende.py` (que un capítulo sin `seccion:` no pase, que
lleve su `en_una_frase:` y se pinte debajo del título, que los enlaces entre documentos se
reescriban, que el índice de la página apunte a anclas que existen, que no haya ni un script ni
un estilo en línea, y que la referencia liste los 60 documentos).

`en_una_frase` es la **mejora de legibilidad** del material, y por eso se vigila: sale en un
recuadro justo debajo del título, que es lo primero que se lee (y lo único que mucha gente va a
leer en el móvil). Va en la cabecera y no dentro del texto a propósito: así no puede quedarse
desfasada respecto al capítulo, porque se cambia donde se cambia el título.

### Los cuatro recuadros

Un `blockquote` cuya primera negrita sea una de las palabras conocidas sale destacado:

```markdown
> **Nota:** matiza algo que se podría malinterpretar.
> **Trampa:** un error que ya se cometió aquí.
> **La lección:** la idea que merece recordarse.
> **Regla:** una decisión del proyecto que no se salta.
```

Se hace **después** de pintar el markdown (markdown no tiene avisos) y el texto no se toca: solo
se le pone clase. El artículo («La lección:» / «Lección:») da igual.

### El botón de copiar, que por http no puede copiar

El botón lo pone `copiar.js` (en fichero y no en línea, porque el CSP de Caddy prohíbe los scripts
incrustados), y **el portapapeles solo existe en contexto seguro**: el material se sirve por http
(el 8080 del PC y la IP de Tailscale), así que `navigator.clipboard` no está. Medido con la puerta
de producción el 28 de septiembre de 2026: pulsar «Copiar» contestaba **«No puedo»** y ahí se
acababa — con el comando delante, en el móvil, la salida era seleccionar el texto a mano.

Ahora el guion **comprueba el portapapeles antes de usarlo** y, si no está (o lo niega), **deja el
bloque seleccionado** y dice «Cópialo a mano». Es la misma decisión que la cesta ya tomaba con el
enlace de invitación. Lo mide la puerta de producción ya pintado: que el botón conteste, y que en
el segundo caso haya texto seleccionado de verdad (166 caracteres la primera vez que se midió).

### Regenerar y leerlo

```bash
uv run --extra docs python -m plataforma.aprende          # escribe plataforma/web/aprende/
uv run --extra docs python -m plataforma.aprende --salida otra/carpeta
```

El extra `docs` son dos paquetes **puros de Python** (`markdown-it-py`, `linkify-it-py`); el
scraper y la API no los necesitan, y si faltan el comando lo dice con la instrucción exacta en
vez de reventar.

> **Trampa:** `uv sync --extra docs` deja el entorno con **eso y nada más**: quita el extra
> `plataforma` (FastAPI, argon2) y media suite empieza a fallar con `ModuleNotFoundError`. Hay
> que pedir los dos a la vez:
>
> ```bash
> uv sync --extra plataforma --extra docs      # o --all-extras
> ```
>
> Y si al sincronizar sale *«failed to remove file …_ffi.pyd: Acceso denegado»*, es que había
> un proceso del proyecto usando el entorno (una API de pruebas, el servidor de desarrollo).
> Se para ese proceso y se reinstala la pieza: `uv sync --reinstall-package
> argon2-cffi-bindings --extra plataforma --extra docs`. Un `.pyd` bloqueado deja el paquete a
> medias y el error que sale después («cannot import name 'ffi'») no dice nada de la causa.

Se lee de dos maneras, y las dos importan:

- **En el PC, sin servidor**: `plataforma/web/aprende/index.html`, con doble clic. El buscador
  lleva su índice en un fichero de al lado (`indice.js`), así que funciona desde `file://` y no
  pide nada por red.
- **Desde el móvil**: `http://<el-PC>:8080/aprende/`, servido por Caddy. El montaje está en
  `docker-compose.yml` (`./web/aprende:/aprende:ro`) y la ruta en el `Caddyfile`
  (`handle_path /aprende/*`). **Va fuera de `/srv` a propósito**: `/srv` está montado de solo
  lectura, y un montaje anidado dentro de otro de sólo lectura **no se puede crear** — el
  contenedor no arranca (`read-only file system`). Se descubrió al desplegarlo, y lo vigila
  `tests/test_aprende.py`.

Regenerar el material después de tocar un documento es volver a lanzar el comando: no hay que
reconstruir ninguna imagen, porque el sitio se monta. `docs/` es la fuente y el HTML es
desechable: si algo está mal, está mal en el markdown.

**Y desde el 27 de septiembre de 2026 lo regenera la pasada del día**, al final y protegido,
igual que `docs/CIFRAS.md`: antes había que acordarse, y medido ese día el sitio montado era
**de tres días antes** que los documentos que sirve. El sitio no inventa contenido —lo convierte
del markdown—, así que dejarlo atrás es contar algo que ya no es verdad. Un fallo ahí **no puede
tumbar la recolección de las 06:00** (el dato ya está escrito y el material es documentación), y
si al entorno le falta el extra `docs`, `aprende` lo dice y no revienta. Lo vigila
`tests/test_aprende.py`.

**Y nada de estilos en línea, tampoco en atributos.** `markdown-it` pinta la alineación de una
tabla (`|---:|`) como un atributo `style`, y la CSP de Caddy (`style-src 'self'`, sin
`'unsafe-inline'`) **bloquea los atributos `style` igual que un `<style>`**: medido el 27 de
septiembre de 2026, servido por Caddy **0 de 22 celdas** quedaban alineadas y con doble clic
22 de 22 — las columnas de números se leían a la izquierda justo donde el material se lee de
verdad, y sin dar ningún error. La alineación viaja en clases (`.num`, `.centro`, `.izq`). Lo
vigila `tests/test_aprende.py`, que caza las tres formas: `<script>` en línea, `<style>` y
atributos `style`.

Y una regla que no se salta: **las cifras del material las vigila `verificar_docs`**, que desde
el 24 de septiembre de 2026 mira también las subcarpetas de `docs/` (antes solo miraba el
primer nivel, así que el curso habría quedado sin vigilancia justo cuando más crece). Y desde el
30 de septiembre de 2026 vigila además **las citas de código** —`almacen.py:287`,
`src/tipos.ts:173`—: saca las citas con número de línea de `docs/`, `README.md`, `.stitch/` y
`plataforma/LEEME.md` (713 el día que se escribió), y comprueba que el fichero esté donde la cita
dice y que la línea citada llegue. Se encontró con las tres formas de romperse (fichero que no
está, línea que no llega, ruta que apunta a otro sitio) metidas a mano en un documento de prueba,
y las tres salieron.

Lo que **no** puede ver es si la línea sigue tratando de lo mismo, y ese mismo día quedó un
ejemplo: al escribir la cabecera del control, `COMPROBACIONES` se fue de la línea 55 a la 68 y la
cita de `COMPETENCIA-IMPLANTABLE.md` se quedó apuntando a otro sitio. El control dice *dónde
mirar*, no *qué dice*; para lo segundo hay que leer.

Y lo tercero que vigila son **los comandos que los documentos mandan ejecutar** (`python -m
<módulo>`, `python <ruta>.py`, `npm run <script>` y `uvicorn <módulo>:<app>`): **134 hoy**, y esta
misma frase lo subió de 133 a 134 al nombrar `projects.cesta.pipeline`. El número sale en cada
pasada, así que aquí no hace falta escribirlo. Un documento que dice `uv run python -m
projects.cesta.pipeline` está prometiendo que ese módulo existe; si se renombra, el documento
sigue sonando igual de bien. Solo se miran los módulos de casa (lo primero es una carpeta del
repositorio); los que empiezan por `pytest`, `uvicorn` o `http.server` se dejan estar: avisar de
esos sería avisar de todo el rato y ninguno sería un fallo del repositorio. Las plantillas
(`python -m projects.cesta.<lo-que-sea>`) tampoco se miran.

**Este control se estrenó saltándose el comando de uvicorn sin medirlo.** Guardaba el comando ya
escrito (`"uvicorn plataforma.api.main:app"`) y luego lo partía por `:` para sacar el módulo, con
lo que la comprobación recibía `"uvicorn plataforma.api.main"`, contestaba «eso no es de casa» y
lo saltaba en silencio: el total decía 132 donde había 133. Ahora el dato que se busca viaja
pelado y el texto se compone al escribir el aviso. Es la misma lección de siempre en este
proyecto: *una comprobación que no puede medir tiene que decirlo, no aprobar*.

### La matriz de paridad: los campos, contra gold

`docs/PARIDAD-CAMPOS.md` se presenta como «el documento que hay que mirar antes de prometer una
funcionalidad», y sus porcentajes son una foto con fecha, que es como debe ser. Los **nombres** de
sus campos no son una foto: son columnas del contrato, y si una columna se renombra la matriz
sigue nombrando la vieja. La puerta saca los campos de la matriz y comprueba que sean columnas de
`data/gold/grupos.parquet`: los 23 lo son, medido el 30 de septiembre de 2026. Se comprobó que el
control caza un renombrado renombrando uno a mano en el documento —la puerta salió con 1 y el
documento se restauró— y el instrumento suelto es `data/debug/paridad_campos.py`.

**Solo se mira en esa dirección, y a propósito.** El primer intento avisaba además de las 31
columnas de gold que la matriz no nombra —`fuente`, `grupo_id`, `calidad`, los `promo_*`—, y era
un aviso falso: la matriz no promete ser el contrato entero, cuenta el dato que se puede tener de
cada cadena. Treinta y un avisos que no son fallos es la forma más rápida de que nadie mire los
avisos.

**Los cuatro controles de arriba pueden poner esta puerta en rojo, y la cadena de las 06:00 no se
entera.** `projects/cesta/run.py` llama a `verificar_docs.main()` dentro de un `try`, **sin mirar
lo que devuelve** —«esto avisa; no toca nada, y no hace fallar el día», dice allí mismo—, así que
una cita rota o un campo renombrado salen en el registro y el día sigue. Es a propósito: un
documento mal citado no es motivo para no recoger los precios de hoy.

### Ninguna ruta de la API se queda sin que nadie la llame

Medido el 30 de septiembre de 2026 con `data/debug/rutas_sin_prueba.py`: de las **46 rutas** de
`plataforma/api/main.py`, **siete no las tocaba ninguna prueba** — las tres de `/api/favoritos`,
`/api/preferencias`, `/api/producto/{cadena}/{id_fuente}`, `/api/invitacion/{codigo}` y
`/api/salud`. Son funciones del encargo (seguir productos, invitaciones, ajustes, la ficha por el
id de la cadena que usa la extensión), así que se escribieron las pruebas que faltaban en
`tests/test_rutas_sin_prueba.py`, por HTTP y con el almacén sustituido —en `tests/` no hay
PostgreSQL, eso lo ejecuta `prueba_e2e.py`—: trece pruebas que fijan la forma de lo que sale, la
ventana de días, el favorito que ya no está en el catálogo, el 400 de seguir algo sin decir qué,
el 404 de la invitación caducada y que `/api/salud` **no pida sesión**, que es lo único que la
hace útil para un vigilante de fuera.

Y como trece pruebas que pasan a la primera no son prueba de nada, se rompió el código a
propósito tres veces (el id de la cadena, el 400 de la línea sin destino, el `desconocido` del
favorito que ya no está): las tres veces falló la prueba que tenía que fallar.

**Lo que el instrumento mide es que nadie las llama, no que no estén comprobadas.** El orden de
los favoritos ya lo fijaba `test_favoritos_orden.py`, llamando a `_orden_de_favoritos`; lo que no
miraba nadie era la ruta. Es la diferencia entre probar la cuenta y probar el mostrador.

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
pantalla del enlace y acaba dentro de la lista), **el papel de «solo mirar»** (el dueno se lo
cambia por su usuario a la persona que ya esta dentro, ella ve el aviso de por que no puede tocar
nada -- 50 casillas apagadas -- y la API le contesta **403** si lo intenta igual, y volver a
dejarle escribir le devuelve los controles), **las novedades** (una toca una linea, la otra abre
su lista y se entera -- «Invitada cogio Leche entera» --, y al volver a abrir desaparece, porque
un aviso que no se apaga es ruido), **las cuatro respuestas dentro de la primera pantalla de un
movil** (la banda util son 109..787 px de 844: lo que obligue a desplazar la pantalla no se lee en
quince segundos), **todo lo que se pulsa medido** en las ocho pantallas donde se puede acabar de
pie (incluidas la ficha del producto y el escaner, que entraron al encontrar ahi cuatro objetivos
de 19 px), **que ninguna pantalla se deslice de lado**, **que con la API a 500 cada pantalla lo
diga con palabras y deje reintentar** (la cesta era la unica sin boton: escribia su error a mano)
y **el contraste del texto pintado en los dos temas**, tambien en la ficha del producto. En su
primera pasada encontro tres cosas que leyendo el codigo no se ven -- React Query pausando los
cambios sin cobertura, la frase de «¿esto esta caro?» ausente en la pantalla a la que se llega
buscando, y el arranque roto con dos listas de casa --, asi que **es lo que hay que correr cuando
se toque la interfaz**. No cierra la condicion (a) de la barra: eso es una persona con un movil
(`docs/PRUEBA-15-SEGUNDOS.md`).

**«Ya los he visto» apaga el punto y no borra el aviso**: la chapa del icono y la pantalla tienen
que decir el mismo numero (`useAvisosSinVer` y el boton leen la misma regla), al pulsarlo el punto se
apaga y **el aviso sigue ahi** -- son dos relojes distintos (`vista_en` y `salto_en`) y es aqui donde
se ve que no se confunden --, y al volver a abrir sigue apagado.

Las **dos cuentas** de esta prueba son fijas (`prueba-navegador` y `prueba-invitada`), y por
el mismo motivo: cada pasada corre contra la misma base. Se ha corrido **tres veces seguidas**
con el mismo resultado (`TODO BIEN`), que es lo unico que hace fiable una puerta.

**Y su lista se poda a las 20 lineas mas recientes.** Cada pasada anade una linea desde la ficha
(es la pregunta 1), asi que crecia sola: el 28 de septiembre de 2026 tenia **63**, 43 de ellas
«Leche entera» de pasadas anteriores. Una lista que crece cambia lo que se mide -- la respuesta 4 de
la primera pantalla se va al fondo -- y la pasada siguiente se pone roja por el estado que dejo la
anterior, que es el defecto de instrumento que este proyecto ya ha pagado tres veces. Se poda antes
de medir y se dice por consola cuantas lineas se han quitado.

**Que ninguna pantalla se quede sin medir lo dice un instrumento, no la memoria**:

    uv run python data/debug/rutas_vs_puerta.py

Lee las rutas de `App.tsx` y todas las que recorren las tres puertas, y ensena las pantallas que
existen y **por donde no ha pasado ninguna**. El 30 de septiembre de 2026 se hizo a mano y salieron
**tres** (`/buscar`, `/favoritos` y la de «esa pantalla no existe»): la lista de la puerta se habia
quedado atras segun crecian las pantallas. Ahora dice 0 en las dos direcciones -- y lo mismo al
reves, que la puerta no visite una ruta que no es ninguna pantalla, que seria una prueba
apuntando a un sitio que ya no existe.

## La tercera puerta: **cada funcion de la aplicacion, hecha de verdad**

Las dos puertas del navegador de arriba miran lo que el encargo pide -- las cuatro preguntas y
lo que se sirve -- y entre las dos **se recorren las pantallas, pero no se ejercita todo lo que
la aplicacion sabe hacer**. El 27 de septiembre de 2026 se midio lo que quedaba sin tocar: el
alta y la baja de una cuenta, varias listas a la vez, cambiarles el nombre, los favoritos, las
vistas guardadas, las busquedas recientes, las cadenas cercanas, los pesos del «que te importa»
y elegir tienda por linea. Para eso esta la tercera puerta:

    uv run python -m plataforma.prueba_funciones
    uv run python -m plataforma.prueba_funciones --guardar-capturas

Abre la aplicacion **servida** (la misma `CESTA_UI`, por defecto `http://127.0.0.1:8080`) en el
mismo movil de 390 x 844, con una cuenta **desechable** (`prueba-funciones`: se crea al empezar y
se borra al terminar **desde la pantalla**, no por API -- ver abajo), y hace **115 comprobaciones**
tocando lo que toca una persona: el boton, el campo, el deslizador. Cada una dice que se miro y si
contesto; el numero lo pone la propia cuenta atras de la puerta, para que un `FALLO` se pueda
citar. Salida esperada:

    TODAS LAS FUNCIONES CONTESTAN.

Lo que entro el 28 de septiembre de 2026, y por que cada cosa:

- **Las diez pestañas del panel**, una por una y **pulsando la pestaña** (no navegando por la
  direccion): las puertas median cuatro (`bajadas`, `indice`, `posicion`, `dudosas`) y las otras
  seis -- `hoy`, `donde`, `cadenas`, `marcas`, `historico`, `movidos` -- no las habia abierto
  nadie con un navegador. Y en la del indice, **la pantalla comparada con la API**: si
  `/api/indice` trae eslabones que cubren mas de un dia, la pantalla lo dice (`dias_del_salto`
  viajaba desde el primer dia y no lo pintaba nadie).
- **Ordenar los resultados**, que no lo media nada: que el orden cambie de verdad y que el
  control diga el sentido **con palabras**. Al medirlo salio que **pulsar el que ya estaba puesto
  no le daba la vuelta** (ver el commit), asi que la comprobacion mira lo unico que no se puede
  fingir: el primer resultado de un orden es el ultimo del otro.
- **Compartir por su usuario**, la otra via que no es el enlace, con sus dos caras: un usuario que
  no existe lo dice, y compartir **contigo mismo** no te quita la lista (abajo, el fallo que
  encontro).
- **Darme de baja desde la pantalla.** Hasta hoy esta puerta borraba su cuenta con un `fetch` a
  `DELETE /api/yo`: medía la API, no la pantalla. Ahora la hace como se hace de verdad -- abrir la
  tarjeta, comprobar que el boton **esta apagado** sin escribir tu usuario, que «No, déjalo»
  vuelve a dejarlo como estaba, y que con el tuyo se enciende y la cuenta desaparece. Deja una red
  de seguridad por API para que la base de casa no se quede con basura si la pantalla falla.
- **La aplicacion con el teclado, y lo que anuncia una casilla.** Ninguna puerta miraba el
  teclado: se medía el dedo (44 px, contraste, que nada se deslice) y la aplicacion tambien se usa
  en el ordenador. Ahora se tabula por la pantalla y se comprueba que el foco llega a lo que se
  usa (24 controles, incluida la casilla de una linea), que **se ve donde esta** (`:focus-visible`
  pintado en todos), que cada casilla **se anuncia con el nombre de su linea** -- un `input` sin
  nombre se lee «casilla, activada» y quien no ve la pantalla no sabe que esta tachando -- y que
  una linea **se tacha con la barra espaciadora**, que es la tarea de verdad sin dedo.
- **Una linea que apunta a otro producto.** El emparejador numera los grupos en el orden en que
  aparecen los productos, asi que una pasada puede renumerarlos y una linea guardada acaba
  apuntando a otra cosa. La puerta siembra el caso (una linea con el nombre de una cosa y el grupo
  de otra) y comprueba que la pantalla **lo dice** en vez de ponerle el pasillo y el precio del
  producto equivocado, que no entra en la cuenta de lo que cuesta la lista, y que al quitarla todo
  vuelve a estar como estaba. Lo mide tambien el punta a punta contra PostgreSQL y gold de verdad.

Y las dos cosas que esa ampliacion **encontro, que eran de la aplicacion**:

1. **Compartir contigo mismo te quitaba la lista.** Escribir tu propio usuario en «Compartir con
   quien ya tiene cuenta» actualizaba tu fila de `lista_acceso` a `escribe`: al invitar y al
   borrar contestaba **403** («solo quien la creo puede invitar», «Solo quien la creo puede
   borrarla»), la tarjeta de Compartir desaparecia -- solo se pinta para el dueno -- y no habia
   forma de volver. La base ya no deja bajar al dueno de su papel (`almacen.comparte`, con un
   `WHERE` en el `DO UPDATE`), la pantalla dice «Esa lista ya es tuya», y lo mide el punta a punta
   (`plataforma/prueba_e2e.py`), que es lo unico que ejecuta el SQL de verdad.
2. **El orden no se le podia dar la vuelta.** El boton de ordenar tenia `desc: !arriba` con
   `arriba = orden[0]?.desc === false`, o sea `desc: false` otra vez: pulsar «Precio» dos veces
   dejaba el mismo sentido y el boton parecia no hacer nada.

Entre las demas esta la que entro antes y no se ve leyendo: **lo que se despliega tiene que
notarse que se despliega**. Los diez desplegables de la aplicacion (el «Estado de las cadenas» de
la cabecera, los filtros del buscador, el orden de los resultados, el «por que» de un
emparejamiento, los ingredientes de una ficha...) salian como **texto suelto**, porque el
triangulo que el navegador pinta en un `<summary>` **desaparece en cuanto se le pone
`display: flex`** -- que es justo lo que hace falta para que mida los 44 px de pulsar. En una
captura del 27 de septiembre de 2026, «Estado de las cadenas» parecia un encabezado sin nada
debajo y la caja de filtros parecia un segundo campo de texto. Lo arregla `Resumen`
(`componentes/ui.tsx`), que pinta la flecha, y una regla de `estilos.css` que la gira al
abrirse; la puerta lo mide **ya pintado** en tres pantallas y en los dos estados.

**Su primera pasada encontro cuatro cosas, y las cuatro eran de la puerta, no de la
aplicacion** (un favorito no se puede pasar a una lista que no existe; «LO QUE HAS BUSCADO» se
pinta en mayusculas desde el estilo, asi que el texto del documento dice otra cosa; el
interruptor de cadenas cercanas guarda lo contrario de lo que uno supone al leerlo; el escaner
contesta «No tengo ese codigo» con otras palabras). Esta escrito aqui porque es la leccion: una
puerta nueva falla primero por lo que ella misma da por hecho.

La quinta fue mas fina y **tambien era de la puerta**: al borrar la lista seleccionada, el
desplegable de listas se queda sin opciones durante un momento mientras se vuelve a pedir la
lista de listas, y medir en ese hueco daba un fallo. La verdad se comprobo con
`data/debug/borrar_lista.py`: en ese mismo instante la API ya contestaba `[('Casa', 1)]` y al
recargar la pantalla enseñaba `['Casa (1)']`. O sea, el borrado estaba bien; la comprobacion
ahora **recarga antes de mirar** y lo que mide es el estado asentado.

Esta puerta **no** sustituye a las otras ni cierra la barra (a): mide si las funciones
contestan, no si se entienden. Eso sigue siendo una persona con un movil en quince segundos
(`docs/PRUEBA-15-SEGUNDOS.md`), y esa la cierra el dueño.

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

## Cuando el motor de Docker no arranca (30 de septiembre de 2026)

La aplicacion entera vive en tres contenedores (`cesta-api-1`, `cesta-db-1`, `cesta-web-1`), y por
debajo hay **WSL2**. Este dia el motor se quedo mudo, y por la tarde se separaron **dos fallos
distintos** que la primera lectura habia mezclado.

### Fallo 1: la red de la maquina virtual de WSL (arreglado)

Lo que se veia al empezar:

    wsl -d Ubuntu -e /bin/true
      wsl: Error interno.
      Codigo de error: CreateInstance/CreateVm/ConfigureNetworking/0x8007054f
      wsl: No se pudo configurar la red (networkingMode Mirrored), revirtiendo a networkingMode None.

**La causa era `networkingMode=mirrored`** en `C:\Users\David\.wslconfig`: WSL no conseguia montar
la red de la VM y no llegaba a arrancar. Con `networkingMode=nat` (el modo por defecto) arranca:
medido, `wsl -d Ubuntu -e /bin/true` sale con **0**. `nat` es algo menos eficiente y puede dar
guerra con el cortafuegos, que es por lo que estaba en `mirrored`, asi que **si algun dia se
vuelve a poner, hay que acordarse de esto**.

Y los dos avisos que salian siempre —`Clave 'wsl2.autoMemoryReclaim' desconocida`, `Clave
'wsl2.sparseVhd' desconocida`— **no eran de una version de WSL mas nueva**: eran claves puestas en
la seccion que no es. Van en `[experimental]`, no en `[wsl2]`. Movidas alli, los avisos
desaparecen (medido). Estas dos claves tienen ademas fama de romper Docker dentro de WSL
([ddev#5356](https://github.com/ddev/ddev/issues/5356),
[docker/docs#18329](https://github.com/docker/docs/issues/18329)), asi que dejarlas bien puestas
no es solo estetica.

**La leccion, porque costo una tarde:** la primera version de esta receta decia que `wsl --update`
lo arreglaria. Era falso —WSL es la 3.0.1.0 y Docker Desktop 4.37.1 la acepta ("WSL version
(3.0.1.0) meets ECI requirement")— y el error no era de version sino de red. Un diagnostico
escrito a partir del mensaje de error, sin probar la hipotesis, manda a la persona equivocada.

### Fallo 2: el motor de Docker Desktop (sin arreglar)

Con WSL ya arrancando, el motor sigue sin levantar. Lo medido:

    docker ps / docker info        se quedan colgados: 16 intentos de 15 s, ni una respuesta
    \\.\pipe\dockerDesktopLinuxEngine   existe (el named pipe esta), pero nadie contesta detras
    wsl -l -v                      solo Ubuntu: la distro `docker-desktop` ya no esta registrada
    %LOCALAPPDATA%\Docker\wsl\disk\docker_data.vhdx   72 GB, sin tocar desde las 12:56
    com.docker.backend             arriba y ocioso (9 s de CPU), con `forwards/list` caducando
    registro                       `WSL2MonoDistroMigrationP2_1_1` cambia a true en cada arranque

O sea: Docker Desktop abre, pero **no crea su maquina** (la distro `docker-desktop` desaparecio) y
su backend se queda esperando. `DockerCli.exe -Shutdown` + relanzar, `wsl --shutdown`, matar todos
los procesos de Docker y volver a empezar: nada de eso lo arregla, y **ya no es un fallo de red**:
WSL arranca.

**Lo que NO hay que hacer mientras tanto: un "reset to factory defaults" de Docker Desktop.**
`docker_data.vhdx` son **72 GB** y ahi vive el PostgreSQL de la aplicacion: un reset se lo lleva
por delante. Es la salida que ofrece la propia aplicacion cuando el motor no arranca, y en esta
maquina es la peor.

**Lo que queda, y necesita a una persona:** reiniciar Windows (que es lo que se dijo el primer dia,
y sigue siendo el paso que falta) y, si vuelve a pasar, **actualizar Docker Desktop** antes que
resetear nada.

### Mientras el motor esta parado

La ingesta y las herramientas de linea de orden (`pipeline`, `emparejar`, `verificar_ingesta`,
`verificar_docs`, `pytest`) **no necesitan Docker**: solo la aplicacion servida, los contenedores y
`prueba_e2e` (que levanta su propio PostgreSQL desechable en el 5434) lo necesitan. Con el motor
parado se puede seguir midiendo el dato y escribiendo pruebas; lo que no se puede es **medir la
interfaz**, que es justo lo que pide el encargo.

**Lo que se toco en esta maquina, para poder deshacerlo:** `C:\Users\David\.wslconfig`
(`networkingMode` a `nat`; `autoMemoryReclaim` y `sparseVhd` movidas a `[experimental]`). La copia
de antes esta en `data/debug/wslconfig.antes.txt`.

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

## Comprobar que la cosecha del dia llego entera: `verificar_ingesta.py`

Los controles de la cadena diaria miran el total, las ramas que caen y los precios contra la web.
Ninguno miraba lo mas tonto: **de lo que la cadena dio hoy, que llego a bronze**. Eso lo contesta

```
uv run python -m projects.cesta.verificar_ingesta                 # el dia de hoy
uv run python -m projects.cesta.verificar_ingesta --fecha 2026-09-23
uv run python -m projects.cesta.verificar_ingesta --fuente dia
```

Compara el crudo del dia contra bronze y saca, por cadena: productos declarados/guardados,
categorias declaradas, paginas declaradas/pedidas y el estado de los enlaces (sin url, sin su
propio id, fuera de su dominio, repetidos). **Sale 0 si todo cuadra** y, si no, cuantos problemas
hay. Es de solo lectura: no pide nada a las cadenas.

**Y lee tambien el estado que va dentro del HTML.** Medido el 28 de septiembre de 2026 con la
cosecha de ese dia delante: el informe daba **18 productos de Alcampo que «sobran»** y sospechaba
de bronze (*«¿bronce de otro dia?»*). No era bronze: los 18 salian de un `.json.gz` que no es JSON,
es la pagina `Resultados de la busqueda para papel multiusos`, con el estado incrustado. El
**barrido del buscador** es un camino de descubrimiento documentado (`collectors/alcampo.py`,
`productos_de_busqueda`) y lo que encuentra se guarda, asi que la comparacion tenia que leerlo --
con **el mismo `js_object`** que usa el colector, porque un control que lee de otra forma que el
colector no puede discrepar de el. Con eso, la cosecha del 28 da **0 problemas**. Lo vigila
`tests/test_verificar_ingesta.py`, que tiene los dos casos: la pagina con estado (no sobra nada) y
la pagina sin estado (lo que hay en bronze si sobra).

Lo que cuenta como problema y lo que no esta razonado en el propio modulo, y es la parte que hay
que respetar si se toca:

- Un producto declarado y no guardado es un problema **si nadie puede explicarlo**. Hoy los 13 que
  faltan tienen su razon medida (3 de Aldi sin precio en su API, 7 de Carrefour en bloques de
  recomendaciones fuera de la rejilla, 3 en paginas que Carrefour sirve sin rejilla).
- **El enlace tiene que llevar su id donde lo construimos nosotros** (Alcampo, Aldi). Donde el
  enlace lo da la cadena — Carrefour publica `R-<referencia>` y su `product_id` no aparece — el
  id de dentro puede ser otro a proposito, y exigirlo daria 1.212 falsas alarmas al dia.
- Una categoria del sitemap sin pedir **no es un problema por si sola**: la cadena puede estar
  devolviendo 404 (DIA publica 3 direcciones muertas). El registro del dia lo dice, y
  `auditar_recorrido.py` es quien mira las categorias del arbol.

El informe del 24 de septiembre esta en `docs/VERIFICACION-INGESTA.md`, con los dos puntos ciegos
de `verificar_precios` medidos (Aldi pinta el precio con JavaScript; la pagina de Alcampo
devuelve el reto del WAF) y con la comprobacion en vivo de las 34 categorias de Alcampo que no se
piden.

> **Aviso:** una comprobacion **no puede escribir en lo que esta midiendo**. La pasada en vivo de
> esas 34 categorias guardo 34 respuestas dentro de `raw/2026-09-24` (los colectores cachean ahi
> lo que piden), y eso cambiaba la evidencia del dia: el recorrido de hoy no las pidio y el crudo
> tiene que seguir diciendo eso. Se movieron a `data/debug/verificaciones/<fecha>/`. Si algun dia
> se automatiza esa pasada, hay que pedirle al `Fetcher` que no guarde.

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
