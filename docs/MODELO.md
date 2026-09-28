# Cesta — modelo de datos de la plataforma

Rehecho el 15 de septiembre de 2026. La version anterior describia un paquete
JSON que se descargaba al movil; eso se descarto (`APP.md` punto 3). Ahora el
modelo tiene dos mitades que no se mezclan:

    lo que se LEE      parquet en gold, via DuckDB. Cambia una vez al dia.
                       Nadie lo escribe desde la app.
    lo que se ESCRIBE  PostgreSQL. Cuentas, listas, favoritos. Cambia cuando
                       vosotros lo cambiais.

Para lo que publica cada cadena, `docs/CADENAS.md`.

---

## 1. La mitad de lectura: lo que ya existe en gold

    grupos.parquet          51.781 filas   el catalogo con su grupo y su calidad
    enlaces.parquet         17.982         los pares identico/equivalente
    precio_diario.parquet  560.640         una fila por producto y dia
    precio_derivado.parquet 560.640        lo anterior + variacion, minimos,
                                           maximos, promo inferida
    resumen.parquet         71.409         el estado de hoy de cada producto
    promos_por_cadena.parquet    4         cuanto dura una promo en cada cadena

Los campos de `grupos.parquet`, que es el que mas se consulta:

    fuente, id_fuente          quien lo vende y su identificador
    nombre, marca              tal cual los publica la cadena
    cantidad, unidad_canon     el formato ya normalizado
    ean                        solo Carrefour, DIA y Mercadona
    precio_cent                lo que cuesta
    precio_unidad_cent         lo que cuesta por kilo, litro o unidad
    precio_ref_canon_cent      el precio de referencia que da la cadena
    unidad_ref_canon           en que unidad lo da
    grupo_id                   con quien se compara. Null si no se compara.
    calidad, calidad_origen    letra A/B/C y de donde sale
    calidad_nota               las senales que la formaron
    nutriscore, nova           de Open Food Facts
    comparacion_fiable         si su unidad se puede comparar entre cadenas

**`comparacion_fiable` es el campo mas importante de la tabla.** Es falso cuando
la unidad es `ud`, porque Mercadona vende un pack de 6 rollos como "1 ud" y
publica el precio por rollo. Medido: 24 % de diferencia mediana y 128 casos
imposibles de 550. Solo kg, l y m entran.

### Lo que hay que anadir a gold

1. **`imagen`**, que esta en bronze y no llega a gold. Desde el 15 de septiembre
   las cinco cadenas la guardan.
2. **`categoria_canon`**, que no existe. Es lo que bloquea "Explorar" y el
   analisis por linea de producto.
3. **`origen_espana`** con su procedencia, cuando se traiga `origins_tags` de OFF.

---

## 2. La mitad de escritura: PostgreSQL

Son siete tablas y no van a ser mas. Todo lo que se escribe desde la app cabe
aqui, y todo junto son unos pocos miles de filas.

    usuario          id, nombre, clave (Argon2id), creado_en
    sesion           token, usuario_id, expira_en, dispositivo
    lista            id, nombre, dueno_id, compartida, creada_en
    lista_linea      lista_id, grupo_id, cantidad, tachado, tachado_por,
                     tachado_en, anadido_por
    favorito         usuario_id, grupo_id o producto_id, anadido_en
    alerta           usuario_id, grupo_id, tipo, umbral, vista_en
    preferencia      usuario_id, clave, valor   (cadenas cercanas, cuantas
                     tiendas acepta el reparto, unidades)

Tres decisiones que conviene justificar:

**`lista_linea` apunta a `grupo_id`, no a un producto.** Se anade "leche entera
1 L", no "leche entera Hacendado". La cadena la decide la app al calcular el
reparto, y puede cambiar de un dia para otro si cambia el precio. Guardar el
producto concreto seria congelar una decision que deberia recalcularse.

**`tachado_por` y `tachado_en` existen porque hay dos personas.** Cuando tu madre
tacha la leche, quieres poder ver que fue ella y cuando. Sin eso, una lista
compartida es un sitio donde las cosas desaparecen solas.

**No hay tabla de productos ni de precios.** Ese lado vive en parquet y se
consulta con DuckDB. Un `grupo_id` en Postgres es una referencia a algo que vive
en otro sitio, y no hay integridad referencial entre las dos mitades. Es a
proposito: si manana se rehace el emparejador y cambian los `grupo_id`, hay que
poder migrar las listas con una consulta, no reconstruir una base de datos.

> **Eso no es una hipotesis: pasa en cada pasada.** El emparejador numera los grupos **en el orden
> en que aparecen los productos** (`core.matching.agrupar_enlaces`: el
> `renombre.setdefault(raiz(i), len(renombre))`), asi que cualquier cambio del catalogo mueve los
> numeros. Medido el 28 de septiembre de 2026 con los datos de casa y la lista de la cuenta de
> pruebas: **43 de sus 54 lineas apuntaban a un grupo que ya no era su producto** -- la leche
> entera salia en el pasillo «Higiene y belleza», porque el grupo 526 es hoy una barra de labios
> REVLON -- y la estimacion decia **298,71 EUR** cuando lo que se podia contar eran **10,56**: el
> resto era un pintalabios a 10,66 EUR/ud por linea de leche.
>
> Hasta que la migracion este, la aplicacion **no miente**: una linea cuyo grupo ya no es su
> producto se marca (`producto_movido`), se le quita el pasillo -- el pasillo tambien es del
> grupo --, no entra en la estimacion ni en el reparto, y la pantalla lo dice con la salida a
> mano: volver a buscarla. Ver `catalogo.lineas_movidas`, `tests/test_lineas_movidas.py` y la
> comprobacion del punta a punta.

**Lo que se guarda de las personas**: un nombre, una contrasena cifrada y unas
preferencias. Ningun dato de pago, ninguna direccion, ningun correo salvo el de
recuperacion si algun dia lo hay.

---

## 3. Las consultas

Todas contra DuckDB salvo donde se diga. Los tiempos son sobre los datos de hoy.

### Buscar

    entra    un texto, y los filtros activos del usuario
    sale     hasta 50 grupos, cada uno con su precio minimo y en que cadena

Se busca en `nombre` y `marca` normalizados (sin acentos, plurales fuera, que es
lo que ya hace `core.matching.raiz`). Los productos sin grupo salen como fila
suelta, marcados, porque son 31.853 de 51.781 y esconderlos seria esconder el
61 % del catalogo.

El filtro de cadena sale de `preferencia`: si el usuario no tiene Aldi cerca, sus
resultados no lo incluyen.

### Ficha de grupo

    entra    un grupo_id
    sale     los productos identicos, los equivalentes, la calidad, la
             nutricion y la curva

Son tres consultas: los miembros del grupo, los enlaces de nivel `equivalente`, y
la serie de `precio_diario` de los ultimos 90 dias.

### La cesta: donde comprarla

La consulta interesante, y la unica que no es trivial.

    entra    una lista (n grupos con cantidades), las cadenas del usuario,
             cuantas tiendas acepta
    sale     el total en cada cadena sola, y la mejor combinacion de dos

Para "todo en una tienda" es una suma por cadena, diciendo que falta en cada una
**por su nombre**, no como un numero. Para el reparto, con cinco cadenas y un
maximo de dos tiendas son diez combinaciones: se calculan todas y se coge la
mejor. No hace falta nada mas listo que eso.

**Los precios de mas de tres dias no deciden.** Se ensenan con su fecha, pero no
entran en la suma que elige tienda. `APP.md` punto 6.

### Favoritos

Un `join` de `favorito` con `resumen.parquet`, ordenado por lo que ha cambiado y
no alfabeticamente: lo que ha bajado arriba, lo que ha subido debajo, lo quieto
al final.

### El cuadro de mando

Consultas de agregacion sobre `precio_diario` y `grupos`. Estan en
`docs/DASHBOARD.md` con los numeros que dan hoy.

---

## 4. La API

Una sola puerta, en `cesta-api`. Responde JSON y nunca HTML.

    POST  /entrar                     usuario y clave -> token
    GET   /buscar?q=&filtros=         los resultados
    GET   /grupo/{id}                 la ficha completa, **con la curva dentro**
    GET   /listas                     las mias y las compartidas conmigo
    POST  /listas                     crear
    POST  /listas/{id}/lineas         anadir un grupo
    PATCH /listas/{id}/lineas/{n}     tachar, cambiar cantidad
    POST  /listas/{id}/compartir      con la otra cuenta
    GET   /listas/{id}/donde          el calculo de donde comprarla
    GET   /favoritos                  con el estado de hoy de cada uno
    POST  /favoritos                  anadir
    GET   /estado                     de que dia es cada cadena, y que falta
    GET   /panel/...                  el cuadro de mando

`/estado` es la que sostiene la regla de las fechas: la interfaz la pide al abrir
y con ella sabe que precios puede dar por buenos.

**Sincronizacion sin conexion**: `PATCH /listas/{id}/lineas/{n}` tiene que ser
idempotente y aceptar el momento en que se hizo el cambio, para que el movil
pueda subir de golpe lo que tacho en el supermercado. Si dos personas tachan la
misma linea, gana quien la tacho antes y no pasa nada.

---

## 5. Tamanos, medidos

    gold entero                        ~18 MB
    grupos.parquet                     2,1 MB
    precio_diario.parquet, 9 dias      ~4 MB
    lo mismo en un ano (19 M filas)    ~250 MB
    PostgreSQL con dos usuarios        unos pocos MB
    raw, 30 dias                       ~10 GB (lo limita limpiar.py)

Todo cabe de sobra. El unico que crece sin parar es `precio_diario`, y a 250 MB
al ano DuckDB lo consulta sin despeinarse. El unico que hay que respaldar es
PostgreSQL: gold se regenera desde raw.

---

## 6. Por orden de construccion

1. Anadir `imagen` a gold. Es una columna y ya esta en bronze.
2. `cesta-api` con `/buscar` y `/grupo/{id}`, leyendo gold. Sin usuarios.
3. Tailscale y comprobar que se abre desde el movil.
4. PostgreSQL, las siete tablas, y las dos cuentas.
5. Listas y favoritos.
6. `/listas/{id}/donde`, que es la consulta que justifica el proyecto.
7. `categoria_canon` y `origen_espana`.
8. El cuadro de mando.
