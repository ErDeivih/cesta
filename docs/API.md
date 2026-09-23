# Cesta — la API

Referencia de las rutas: las que existen hoy y las que hay que anadir. Sirve para
que la interfaz y el servidor no se inventen contratos distintos.

La API es **la unica puerta a los datos**. Responde JSON y nunca HTML. La
interfaz se sirve aparte (Caddy) y llega a `/api/*` por el mismo origen, asi que
no hay CORS ni cookies que se pierdan entre puertos.

Se puede ver viva y probar en `http://localhost:8080/api/docs`.

---

## Como estan montadas las dos mitades

    catalogo.py   DuckDB sobre los parquet de gold. **Solo lee.** Cambia una vez
                  al dia, cuando termina el pipeline.
    almacen.py    PostgreSQL. Cuentas, listas y favoritos. Lo que escribis.

Una conexion de DuckDB **por hilo**: no es seguro compartir una entre hilos y
FastAPI atiende en un pool.

---

## Convenciones que valen para todo

**El dinero va en centimos, siempre, y en enteros.** `precio_cent: 345` son 3,45
EUR. Nunca decimales en euros: 0,1 + 0,2 no da 0,3 y una lista de la compra son
veinte sumas.

**Las fechas son ISO 8601 con zona.** `2026-09-17T10:04:00Z`.

**Toda respuesta que dependa del catalogo lleva `fecha_datos`**, que es el ultimo
dia que hay en el historico. Es lo que sostiene la regla de que un precio viejo
se ensena con su fecha pero no decide en que tienda comprar.

**Un dato que no tenemos es `null`, nunca cero ni cadena vacia.** Un producto sin
Nutri-Score tiene `nutriscore: null`, y la interfaz pone "no lo se". Un cero se
lee como "malo" y seria mentira.

**La sesion va en una cookie `cesta_sesion`**, `httponly`, `samesite=lax`, 30
dias. En la base se guarda **el hash del token**, nunca el token: si alguien lee
la tabla, no puede entrar con lo que ha leido.

**Los codigos de estado que se usan:**

    200  bien
    201  creado
    400  la peticion esta mal formada
    401  no has entrado
    403  has entrado pero no puedes hacer eso
    404  no existe, o no es tuyo (a proposito: no se distingue)
    409  conflicto que la otra persona tiene que resolver

Que 404 y "no es tuyo" den lo mismo es deliberado: si dieran distinto, se podria
averiguar que listas existen probando identificadores.

---

## Entrar y salir

### `POST /api/entrar`

    entra   {"usuario": "david", "clave": "...", "dispositivo": "..."}
    sale    {"usuario": {"id": "...", "usuario": "david", "nombre": "David"}}
            + la cookie de sesion
    mal     401 si el usuario o la clave no valen

Tarda lo mismo si el usuario no existe que si la clave es incorrecta, para no
delatar por el tiempo que ese usuario no esta dado de alta.

### `POST /api/salir`       borra la sesion y la cookie
### `GET /api/yo`           quien eres y tus preferencias; `{"usuario": null}` si no has entrado

### `POST /api/registrarse`

    entra   {"usuario": "ana", "nombre": "Ana", "clave": "...", "dispositivo": "..."}
    sale    201 + el usuario + la cookie de sesion, igual que `/api/entrar`
    mal     403 registro cerrado    (CESTA_REGISTRO=cerrado)
            409 ese usuario ya esta cogido
            422 el nombre o la clave no cumplen las reglas, con la frase
            429 mas de 10 altas en la ultima hora

**Crea la cuenta y entra en el mismo paso**, a proposito: quien llega aqui casi
siempre viene de un enlace de invitacion a una lista, y la invitacion solo se
aplica cuando ya hay sesion.

El `detail` de los errores esta escrito para leerlo una persona ("Ese usuario ya
esta cogido. Elige otro."), y la interfaz lo ensena tal cual. Las reglas viven en
`plataforma/api/registro.py`, que es lo mismo que usa la consola.

### `GET /api/personas`     quien tiene cuenta y desde cuando. Pide sesion.

Con el registro abierto, esta es la ventana que hace vigilable la puerta: si
aparece un nombre que no conoces, se ve aqui.

**El registro esta ABIERTO** (`CESTA_REGISTRO=abierto`, por defecto). Hoy eso
esta acotado porque a la pagina solo se llega desde Tailscale. **Hay que cerrarlo
el dia que el servicio se publique con Cloudflare Tunnel.** La consola sigue
existiendo para el registro cerrado:
`docker compose exec api python -m plataforma.cuenta <usuario> "<Nombre>"`.

---

## Catalogo

### `GET /api/buscar`

    q             el texto. Menos de dos letras no busca.
    cadenas       "alcampo,dia". Por defecto, las del usuario.
    limite        40 por defecto
    comparables   solo los que se pueden comparar por kilo o litro
    con_nutricion solo los que tienen Nutri-Score

    sale  {"fecha_datos": "2026-09-17", "resultados": [{
             "grupo_id": 4125 | null,      null = producto suelto, sin comparar
             "nombre", "marca", "cadena_mas_barata", "precio_cent",
             "precio_unidad_cent", "precio_unidad_max_cent", "unidad",
             "cadenas", "productos", "nutriscore", "imagen", "con_oferta",
             "comparable", "ahorro_pct"}]}

**Los productos sin grupo salen igual, marcados.** Son 32.486 de 51.781: el 63 % del
catalogo. Esconderlos seria esconder casi todo.

**`marca` se añadió el 22 de septiembre de 2026** y es la del miembro **más
barato** del grupo, que es el que la fila enseña. No estaba, y la tabla del
buscador la pedía: la única forma de sacarla sin el campo era adivinarla a partir
del nombre, y eso es inventarse un dato.

**Ojo**: `grupo_id` NUNCA es null. El emparejador se lo pone a todo, aunque el
grupo sea de un solo producto. Lo que hace comparable a un grupo es tener
**dos cadenas o mas**, y eso es lo que devuelve `comparable`.

### `GET /api/grupo/{grupo_id}`

    sale  {"grupo_id", "nombre", "imagen", "unidad", "cadenas",
           "ahorro_pct", "ahorro_cent",
           "productos": [{
              "producto_id": "dia:12345",   <- "fuente:id_fuente"
              "fuente", "nombre", "marca", "cantidad", "unidad",
              "precio_cent", "precio_unidad_cent", "comparable",
              "calidad",     <- SOLO si sale de leer ingredientes
              "gama",        <- SOLO si sale de ordenar por precio
              "nutriscore", "nova", "ean", "imagen", "alergenos",
              "ingredientes", "origen", "promo", "url"}],
           "serie": [{"producto_id", "fuente", "fecha", "precio_unidad_cent"}],
           "explicacion": {              <- SOLO si hay algo que explicar
              "ejecucion", "nivel", "metodo", "pares",
              "confianza_minima", "confianza_media", "par_mas_flojo", "features"}}

**`explicacion`: por que esos productos acabaron juntos.** Se añadió el 23 de
septiembre de 2026 y **no se recalcula nada**: sale de `equivalencia.parquet` de
la última pasada del matching, que ya trae un par aceptado por fila con su
método, su confianza y sus `features`. Deducir el parecido otra vez aquí daría
una segunda versión de la misma verdad, y la ficha enseñaría una que no es la que
formó el grupo.

**El campo se omite cuando no hay nada que decir**: un grupo de un solo producto,
uno sin ningún par directo entre sus miembros (los grupos se forman por
transitividad, así que eso es normal), o un gold sin ninguna pasada. Un
`{"pares": 0}` se leería como "se emparejaron por nada", que no es lo mismo que
"no lo sabemos". La pantalla sabe decir que ahí no hay nada que enseñar.

Ejemplo real (grupo 11580, 22 productos):

    "explicacion": {"ejecucion": "20260922-170833", "pares": 42,
                    "nivel": "ean+equivalente+identico", "metodo": "ean+nombre",
                    "confianza_minima": 0.5877, "confianza_media": 0.8738,
                    "par_mas_flojo": "alcampo:99238 · dia:1917",
                    "features": "{\"parecido\": 0.5877, \"ean_igual\": false, ...}"}

`nivel` y `metodo` llevan los valores separados por `+` cuando en un mismo grupo
no son los mismos en todos los pares. `par_mas_flojo` es el par con la confianza
más baja, que es lo primero que hay que mirar para decidir si el grupo es de
fiar. `features` es JSON en texto; la pantalla lo abre y lo enseña como filas.

**`producto_id` en cada punto de la serie se añadió el 22 de septiembre de 2026.**
Antes iba solo `(fuente, fecha)`, y eso hace que un grupo con dos productos de la
misma cadena dé dos series que empiezan igual y **ninguna se pueda pintar**: no se
sabe de cuál de los dos es cada precio. No es un caso raro: medido ese día, hay
grupos con 8 productos de 2 cadenas, 6 de ellos de la misma. La interfaz decía
"no lo puedo dibujar" en pantalla en vez de mezclar dos productos.

**`calidad` y `gama` nunca vienen los dos.** Es la regla mas importante de toda
la API: una letra sacada del precio no se llama calidad. El 77 % de ellas lo son.

### `GET /api/estado`

De que dia es cada cadena y si esta al dia. La interfaz la pide al abrir.

    sale  {"fecha_datos", "dias_precio_valido": 3,
           "cadenas": [{"cadena", "productos", "ultimo_dia", "al_dia"}]}

---

## Listas

### `GET /api/listas`     las mias y las compartidas conmigo
### `POST /api/listas`    `{"nombre": "Casa", "es_de_casa": true}`

### `GET /api/listas/{id}`

    sale  {"papel": "dueno" | "escribe" | "mira",
           "lineas": [...],
           "estimacion": {"total_cent", "en_carrito_cent", "por_recoger_cent",
                          "lineas", "sin_precio"},
           "novedades": [...],      lo que ha tocado el otro desde tu ultima visita
           "personas": [...],
           "fecha_datos"}

Cada linea de `lineas` lleva ademas **su pasillo**, que es lo que permite pintar la
lista por tandas con el pasillo delante:

    {"id", "grupo_id", "producto_id", "nombre_visto", "cantidad", "nota",
     "tachado_en", "anadido_en", "en_carrito", "anadido_por", "tachado_por",
     "seccion": "lacteos-huevos",         el slug, para agrupar
     "pasillo": "Lácteos y huevos",       lo que se lee
     "pasillo_orden": 3}                  su punto en el recorrido de la tienda

Las tres claves son **opcionales y no viajan con `null`**: si gold no trae la columna
`seccion` (la plataforma se despliega por separado del scraper) o si el grupo no esta
en el catalogo, la linea sale sin ellas y la pantalla la pinta al final y sin
encabezado. Un dato que no tenemos no se rellena.

**El pasillo es del producto, no del grupo**, y un grupo tiene miembros de varias
cadenas: cuando no coinciden gana el que mas miembros comparten, y los empates se
rompen por el orden del recorrido (`catalogo.pasillo_de_grupos`). **El orden de
`lineas` no cambia**: lo decide PostgreSQL (`en_carrito, anadido_en`), y quien reparte
en tandas y las coloca en el recorrido es la pantalla, que es la que sabe cuantas
secciones tiene la lista.

`estimacion` es **el numero que se mira mientras se anaden cosas**: coge cada
cosa donde este mas barata. No es el calculo de "donde la compro", que pide
elegir tienda. Tiene que salir siempre y rapido.

### `POST /api/listas/{id}/lineas`

    entra  {"id": "<uuid generado EN EL MOVIL>", "nombre": "...",
            "grupo_id": 4125, "cantidad": 2, "nota": "la de cristal"}

**El identificador lo genera el movil.** Asi se puede anadir sin cobertura y
subirlo despues con la identidad con la que nacio. Si llega dos veces, no se
duplica: se actualiza.

### `PATCH /api/listas/{id}/lineas/{linea_id}`

    entra  {"tachado": true, "en_carrito": true, "cantidad": 3,
            "nota": "...", "borrado": true,
            "momento": "2026-09-17T18:04:00Z"}   <- la hora DEL MOVIL

**`momento` es la hora del movil, no la de llegada.** Tachar sin cobertura a las
18:04 y subirlo a las 18:20 cuenta como las 18:04, que si no el orden de los
hechos se lo inventa el servidor. Nunca se acepta una hora futura.

**Tachar es idempotente**: tachar algo ya tachado no hace nada y no es un error.
Si los dos tachais a la vez, gana quien lo hizo antes y el otro ve lo que queria
ver. **La cantidad es el unico caso con conflicto real**: gana el ultimo, y se
avisa de quien fue.

`tachado` y `en_carrito` son la misma accion vista de dos formas y se mantienen
coherentes en el mismo UPDATE.

### `GET /api/alertas`

    sale  {"fecha_datos",
           "alertas": [{"id", "grupo_id", "tipo", "umbral_cent", "creada_en",
                        "vista_en", "salto_en", "salto_texto"}],
           "saltan":  [{"grupo_id", "nombre", "cadena", "precio_unidad_cent",
                        "unidad", "alerta_id", "tipo", "por_que"}]}

Los tres tipos son los del `CHECK` de la tabla: `baja_de` (con `umbral_cent`),
`minimo_90d` y `cualquier_bajada`. `saltan` trae las que se cumplen hoy, **con la frase
que las explica**, y viene de `alertas.evalua`, que es el unico sitio que sabe de
precios.

**`salto_en` y `vista_en` son dos relojes distintos, y por eso son dos columnas**:

    salto_en      cuando se cumplio la condicion. Lo pone el **vigilante**
                  (`api/vigilante.py`) en cuanto cambia gold, sin que nadie abra nada.
    vista_en      cuando esta persona lo ha visto. Lo pone ella, con
                  `POST /api/alertas/vistas`.

`salto_texto` es la frase **guardada en el momento en que salto**: se mide contra el gold
de ese dia, y gold se reescribe cada manana, asi que recalcularla haria que el aviso que
alguien vio ayer contara hoy otra cosa. Una alerta **salta una vez** (el `UPDATE` lleva
`AND salto_en IS NULL`): un aviso que se repite todos los dias deja de leerse.

    POST   /api/alertas              {"grupo_id", "tipo", "umbral_cent"}
    DELETE /api/alertas/{alerta_id}
    POST   /api/alertas/vistas       {"ids": [...]}   marca `vista_en`

`POST` es una alerta por persona, grupo y tipo; repetirla la actualiza y **limpia
`vista_en` y `salto_en`**: pedir otra vez la misma alerta es volver a empezar.

### `POST /api/listas/{id}/sincronizar`

La cola de lo que se hizo sin cobertura, de golpe. Cada cambio con su hora.
**Un cambio malo no impide que suban los demas**: se devuelve `fallidos` y se
sigue. El movil manda lo que tenga guardado, y alguno puede referirse a una linea
que la otra persona ya borro.

### `GET /api/listas/{id}/donde`

    max_tiendas   2 por defecto
    cadenas       las del usuario por defecto

    sale  {"una_tienda": [{"cadena", "total_cent", "total_sin_ofertas_cent",
                           "encontrados", "faltan": ["Cafe en grano 1 kg"],
                           "productos": [...]}],
           "repartido": {"cadenas", "total_cent", "reparto", "faltan",
                         "ahorro_cent", "merece_la_pena"},
           "lineas", "fecha_datos"}

**`faltan` va por nombre, no como numero.** "le faltan 2" no sirve para decidir;
"en Mercadona no encuentro: cafe en grano 1 kg, atun pack 6" si.

**`merece_la_pena`** es falso si el reparto ahorra menos de 1,50 EUR. Ir a dos
tiendas cuesta media hora.

### Invitar

    POST   /api/listas/{id}/invitacion   -> {"codigo", "ruta": "/unirme/abc123"}
    POST   /api/invitacion/{codigo}      -> entra en la lista
    DELETE /api/listas/{id}/invitacion   -> anula las que haya

Caduca a los 7 dias y sirve para 3 personas, por defecto. Un enlace que dura para
siempre acaba reenviado en un grupo que no era.

---

## Favoritos y preferencias

    GET    /api/favoritos    con el estado de hoy de cada uno
    POST   /api/favoritos    {"grupo_id": 4125}
    DELETE /api/favoritos
    PUT    /api/preferencias {"clave": "cadenas_cerca", "valor": ["dia","alcampo"]}

---

## Panel

    GET /api/panel/hoy         estado de la ingesta, precios movidos, alarmas
    GET /api/panel/cadenas     quien es mas barato, cuanto se mueve, dispersion
    GET /api/panel/marcas      marca propia contra marca, **con su aviso**
    GET /api/panel/historico   dias guardados y que analisis faltan, con fechas
    GET /api/panel/movidos     lo que se ha movido hoy

Todas cacheadas hasta que gold cambie de fecha, que es una vez al dia.

`/panel/marcas` devuelve un campo `aviso` que **hay que ensenar siempre**: dice
que porcentaje de las letras de calidad salen del precio. Sin el, el estudio se
lee al reves.

---

# Lo que hay que anadir

Contratos propuestos para las tareas de `BACKLOG.md`. Si al implementarlas
conviene cambiarlos, **se cambian aqui tambien**.

### `GET /api/panel/matching` — el panel de auditoría · **HECHO** (22 sep 2026)

    ?limite=20                      cuantos pares de muestra (1 a 200)

    {"fecha_datos",
     "ultima": {"ejecucion_id", "version_modelo", "productos", "umbral",
                "huella_catalogo"},
     "metricas": [{"metrica", "valor"}],
     "anterior": {"ejecucion_id"} | null,
     "cambios": [{"metrica", "antes", "ahora", "delta"}] | null,
     "pares": [{"producto_a", "producto_b", "nombre_a", "nombre_b",
                "fuente_a", "fuente_b", "nivel", "metodo", "confianza",
                "features": {...}}],
     "ejecuciones": ["20260922-150351", ...]}

Lee de `data/gold/matching/`, el modelo versionado de la Fase 1: cada pasada en su
carpeta, con sus métricas y sus pares con `features`, y nada sobrescrito. Por eso
`cambios` puede existir: se compara la última pasada con la anterior, que es la
medida de **estabilidad** que pide el plan.

`features` es lo que hace auditable un par sin que nadie apruebe nada: si el EAN
coincide y si está en los dos lados, si coinciden marca, cantidad, unidad y
sección, el parecido y el **ratio de precio por unidad**. Y se ve cosas reales:
en un par de Milka con el mismo EAN aparece `cantidad_igual: false` con un ratio
de 1,5, que es una diferencia de dato que merece mirarse; y `seccion_igual: false`
sale a menudo entre productos idénticos, porque **la sección es el pasillo de cada
cadena, no una taxonomía del producto**.

`nombre_a` o `nombre_b` pueden ser `null`: la equivalencia guarda claves estables
y el nombre se pide al catálogo, así que si una cadena no capturó ese día, el par
se sigue pudiendo auditar aunque falte un lado.

**Este endpoint no escribe nada, y no hay ninguno que lo haga.** No hay botones de
aprobar ni rechazar: el encargo dice que no hay validación humana, nunca. Hay una
prueba (`test_el_panel_solo_lee`) que comprueba que mirar el panel no cambia ni un
fichero.

### `GET /api/ean/{codigo}`  — tarea 8, el escaner · **HECHO** (22 sep 2026)

Se implementó en `plataforma/api/catalogo.py` (`normaliza_ean` y `por_ean`) y en
`main.py`. Dos cosas que el contrato de abajo no decía y la implementación sí:

- **El código se acepta como lo lea el lector**: con espacios, con guiones y con
  ceros de más (`84000001`, `840-000-01` y `084000001` son el mismo número, que es
  lo que pasa de verdad entre EAN-13 y UPC-12). Se guarda y se busca sin ceros a
  la izquierda, para que las dos formas encuentren lo mismo.
- **El `motivo` `sin_ean_en_esa_cadena` todavía no se da nunca**, porque necesita
  un parámetro `cadena` que no se ha implementado. Sin él, un código bueno que no
  conocemos sale siempre con `motivo: "desconocido"` y la pista de Alcampo y Aldi.

    sale (lo conozco)
      {"encontrado": true,
       "producto": {...},              el mismo formato que en /grupo
       "grupo_id": 4125 | null,
       "comparacion": [{"fuente", "precio_cent", "precio_unidad_cent",
                        "diferencia_pct"}] | null,
       "nota": {...} | null,           ver /api/nota mas abajo
       "fecha_datos"}

    sale (no lo conozco)
      {"encontrado": false,
       "motivo": "desconocido" | "sin_ean_en_esa_cadena",
       "sugerencia": "Puede ser marca propia de Alcampo o Aldi, que no publican
                      codigo de barras",
       "fecha_datos"}

    400 si el codigo no tiene 8 a 14 digitos

**`comparacion` es `null`, no una lista vacia**, cuando el producto solo esta en
una cadena. Vacia se lee como "he mirado y no hay nada mas barato"; `null` se lee
como "no puedo comparar". No es lo mismo.

### `GET /api/habituales`  — el mosaico · **HECHO** (23 sep 2026)

    limite   24 por defecto (1..60)
    pide     sesion
    sale     {"origenes": ["tuyo" | "de todos" | "basico", ...],
              "habituales": [{"grupo_id", "nombre", "imagen",
                              "precio_unidad_cent", "unidad",
                              "cadena_mas_barata", "fiable",
                              "origen",              en CADA tarjeta
                              "veces", "ultima_vez"}],   solo en las de "tuyo"
              "fecha_datos"}

Los grupos que esa persona ha anadido mas veces, **lo reciente pesando mas**, con lo
justo para pintar una tarjeta y anadirla de un toque. La especificacion que se siguio
es `Claude outputs/ENCARGO-UX-23SEP.md` (§5).

**`origen` va en cada tarjeta, y hay tres escalones.** Esto es un **cambio de criterio**
respecto a lo que decia aqui antes, asi que se cuenta en vez de borrarse:

    "tuyo"       lo que ha anadido esta persona. Manda `veces` y `ultima_vez`.
    "de todos"   lo mas anadido en toda la casa, que es un recuento agregado y no lleva
                 datos personales. **No manda `veces` ni `ultima_vez`**: son de todo el
                 mundo, y mandarlos con el mismo nombre que los tuyos seria otra vez dos
                 numeros llamandose igual -- el error que este proyecto ya pago con
                 "imposible".
    "basico"     una compra basica fija, para que la cuadricula **no se vea vacia** el
                 primer dia.

**Se rellena hasta `limite`, bajando escalones en ese orden**, y el mosaico **no repite
un grupo**: si lo que compras es "leche entera" y ademas esta en la compra basica, sale
una vez, en el escalon de mas arriba. Antes se bajaba un escalon solo si el de arriba no
daba **ni una** tarjeta, y eso dejaba el caso peor sin resolver: medido contra la base
viva el 23 de septiembre, con **una** linea propia la respuesta era un mosaico de **una**
tarjeta. Casi vacio se ve casi vacio.

`origenes` dice, una vez por respuesta, que escalones han entrado -- para que la pantalla
sepa si tiene que explicar algo --, pero **cual es cual lo dice cada tarjeta**: una
cuadricula puede tener tarjetas tuyas y basicas a la vez, y con un solo campo por
respuesta no habria como decirlo.

**Antes este documento decia que con historial vacio la lista sale vacia y que no se
rellena con "populares".** El encargo del 23 de septiembre pide lo contrario, y su
razon esta en `docs/PANTALLAS.md`: una pantalla en blanco es el peor momento de la
aplicacion y el unico que todo el mundo ve. Lo que **no** se hace es mezclar los
escalones sin decirlo: para eso esta `origen` en cada tarjeta, que permite que la
pantalla diga *«todavia no se lo que sueles comprar»* sin renunciar a llenar la
cuadricula.

Sin foto no viaja la clave `imagen` (nunca `null`, ni `""`, ni `0`). `fiable` es
unidad comparable (kg/l/m; "ud" no) **y** dos cadenas o mas **y** sin contradiccion
de precio mayor de 30x dentro del grupo: con una sola cadena no hay comparacion que
hacer, asi que es `false`.

### La nota, dentro de la ficha  — tarea 9

No es una ruta aparte: se anade a cada producto de `/api/grupo` y `/api/ean`.

    "nota": {"valor": 72,             0 a 100, o null si no hay datos
             "de_que": ["nutriscore", "aditivos"],   en que se ha basado
             "aditivos": 3,
             "aditivos_riesgo": 0,
             "ecologico": false,
             "tope_por_aditivo": false}   true si un aditivo de riesgo alto la topo

    "nota": null    cuando no hay con que calcularla (el 76,9 % de los casos)

**`nota: null` es una respuesta, no un fallo.** La interfaz pone "no lo se". Un
cero se leeria como "malisimo" y seria mentira. Es justo lo que la OCU critica de
Yuka y El CoCo.

### Cerrar la compra  — tarea 10

    POST /api/listas/{id}/cerrar
      entra  {"cadena": "alcampo", "momento": "..."}
      sale   {"compra_id", "lineas_guardadas", "quedan_por_coger"}

    GET /api/compras            las ultimas, con su total
    GET /api/compras/{id}       el detalle

Guarda lo que estaba en el carro, lo quita de la lista y deja lo que no se cogio.
**Idempotente por lista y minuto**: pulsar dos veces no crea dos compras.

---

## Lo que la API no hace, y no debe hacer

- **No escribe en `data/gold/`.** Lo escribe el pipeline, se monta en solo
  lectura, y esa frontera es lo que permite arreglar una mitad sin tocar la otra.
- **No sirve HTML.** Eso es Caddy.
- **No tiene registro abierto.**
- **No guarda datos de pago ni direcciones.** La app no compra nada.
- **No manda notificaciones push.** Necesitan un servidor siempre accesible y el
  PC se apaga. Las novedades al abrir cubren el caso.

---

# Filtros de la busqueda (17 de septiembre de 2026)

## `GET /api/buscar`

| parametro | tipo | que hace |
|---|---|---|
| `q` | texto | lo que se busca. Obligatorio, minimo 2 letras |
| `cadenas` | lista separada por comas | `alcampo,dia`. Si falta y el usuario tiene cadenas cerca guardadas, se usan las suyas |
| `limite` | entero | grupos devueltos, por defecto 40 |
| `comparables` | bool | solo unidades comparables entre cadenas (kg, l, m) |
| `con_nutricion` | bool | solo con Nutri-Score **o** tabla de la etiqueta |
| `sellos` | lista separada por comas | `sin-gluten,vegano`. Ver abajo |
| `conservacion` | texto | `refrigerado` \| `congelado` \| `ambiente` |
| `marca_propia` | bool | solo marca blanca |
| `ofertas` | bool | solo con promocion hoy |

Sellos aceptados:

    sin-gluten   sin-lactosa   vegano   vegetariano
    ecologico    sin-azucar    sin-sal  sin-aceite-palma

**Un sello que no este en esa lista se ignora en silencio.** No se interpola
nunca lo que llega del cliente: se valida contra la lista y el `LIKE` se monta
con parametro. Hay una prueba que intenta un `DROP TABLE` por ahi.

### La regla que hay que respetar al tocar esta consulta

> El **texto** se puede cumplir a nivel de grupo. Un **atributo** tiene que
> cumplirlo cada producto que se ensena.

La busqueda entra por grupos: basta con que un miembro case con el texto para que
el grupo entre, y eso esta bien (si buscas "leche", el grupo entero es de leche
aunque un miembro se llame "L.R. Desnatada"). Pero los atributos se aplican
**tambien** al reconstruir el grupo, en el CTE `miembros`. Si se quitan de ahi,
"galletas sin gluten" vuelve a contestar con galletas normales. Ver
`docs/AUDITORIA.md`, pasada del 17 de septiembre, punto 3.

## `GET /api/grupo/{id}` — campos nuevos en cada producto

```json
{
  "sellos": ["sin-lactosa"],
  "sellos_origen": "certificado",
  "certificados": ["adilac", "origen-espana"],
  "conservacion": "refrigerado",
  "es_marca_propia": true,
  "nutricion": {"energia_kcal": 46, "grasas": 1.5, "proteinas": 3.2, "sal": 0.1},
  "nutricion_por": "100ml",
  "envase": "brik",
  "descripcion": "De origen nacional y de bienestar animal.",
  "tipo_producto": "Leche desnatada",
  "dias_caducidad": 180,
  "peso_neto_g": 1030,
  "grado_alcohol": null,
  "promo_hasta": "2026-09-20"
}
```

`sellos_origen` vale `certificado`, `etiqueta`, `nombre` o `mixto`, y la interfaz
**lo dice en pantalla**. Un certificado auditado y una palabra en el nombre del
producto no valen lo mismo, y dar a entender lo contrario es lo peor que puede
hacer esta app.

`nutricion` llega ya como objeto, no como texto JSON.

## Tolerancia a un gold viejo

La plataforma monta `data/gold` en solo lectura y las dos mitades del sistema se
actualizan por separado. Las columnas nuevas se piden con un `DESCRIBE grupos`
previo: si el ultimo gold no las tiene, llegan como `NULL`. **Nunca se cae la
app por eso**, porque la conexion se crea al arrancar y un Binder Error ahi
tumbaba el servicio entero, no una busqueda.
