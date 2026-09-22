# Cesta — el plan, fase por fase

Cada funcionalidad desglosada desde lo alto hasta tareas que se pueden hacer de
una sentada. Escrito el 17 de septiembre de 2026.

**Como se lee esto.** Cada fase tiene un objetivo que se puede probar. Dentro,
tareas numeradas `F1.2` con lo que hay que tocar y como se sabe que esta bien.
Una tarea que no se puede probar sola es que esta mal partida.

**La regla de oro del orden**: nada que dependa de datos que no existen, y nada
que pueda dar una respuesta vergonzosa antes de arreglar la causa.

---

## Mapa de dependencias

    F0  Poner la casa en orden          nada depende de esto, pero todo lo demas
                                        es mas seguro despues
         |
    F1  Los datos que ya tenemos        <- desbloquea F2, F3, F5
      F1a  Secciones a gold
      F1b  Nutricion de DIA
      F1c  Packs de Mercadona
      F1d  Tipo de producto
         |
    F2  Los grupos, arreglados          <- desbloquea F5, F7
         |
    F3  La lista, como se usa           depende de F1a
         |
    F4  Las ofertas, visibles           independiente
         |
    F5  El escaner                      depende de F1b y F2
         |
    F6  El historial                    independiente, pero CUANTO ANTES
         |
    F7  El panel completo               depende de F1a y F2
         |
    F8  Mas datos y mas cadenas         independiente

Si hay que elegir tres, son **F0, F1 y F6**. F0 porque sin git cualquier error es
irreversible; F1 porque el dato ya esta pagado y no lo usamos; F6 porque es
barato hoy e imposible de recuperar manana.

---

# F0 · Poner la casa en orden

**Objetivo**: que un error se pueda deshacer, y que la plataforma arranque.

### F0.1 · Poner el proyecto en git

    por que   hoy se tocan veinte ficheros sin poder ver que cambio ni volver
              atras. El .gitignore existe desde el 7 de septiembre.
    hacer     git init; comprobar que `git status` no lista data/, .env ni .venv;
              primer commit con todo lo que hay
    listo     `git log` tiene un commit y `git status` sale limpio

### F0.2 · Levantar la plataforma por primera vez

    por que   NUNCA se ha levantado con Docker. Todo lo probado son piezas
              sueltas y la API contra gold real, sin PostgreSQL.
    hacer     copiar .env.ejemplo a .env, cambiar CESTA_CLAVE_DB,
              `plataforma\arrancar.bat`, crear las dos cuentas
    listo     http://localhost:8080 abre, se entra con la cuenta, se busca un
              producto y sale
    ojo       es la primera vez que corre `001_esquema.sql` y `002_*.sql`.
              Si fallan, se arreglan ahi mismo antes de seguir.

### F0.3 · Comprobar si Tailscale da HTTPS

    por que   el escaner (F5) necesita `getUserMedia`, que solo funciona en
              HTTPS o localhost. Con Tailscale en http:// NO VA.
              **Si esto falla, F5 entero cambia de forma.**
    hacer     `tailscale cert cesta.<tu-tailnet>.ts.net` y servirlo desde Caddy
    listo     https://cesta...ts.net abre desde el movil con candado
    si no     anotarlo en BACKLOG y decidir: o F5 solo funciona en el PC, o se
              busca otra via

### F0.4 · Primer respaldo

    hacer     `plataforma\respaldar.bat` y comprobar que el .sql.gz no esta vacio
    listo     existe data/respaldos/cesta_*.sql.gz con contenido
    luego     darlo de alta como tarea semanal

---

# F1 · Aprovechar los datos que ya tenemos

**Objetivo**: que todo lo que ya esta descargado llegue a la app. Ni una
peticion nueva a nadie.

Es el bloque con mejor relacion entre esfuerzo y resultado de todo el plan:
**el dato ya esta en `data/raw/`**. Es leer y mapear.

## F1a · La seccion comun llega a la app

### F1a.1 · `seccion` en gold

    hacer     en `projects/cesta/emparejar.py`, calcular `seccion` con
              `core.secciones.seccion_de(fuente, categoria)` y anadirla a
              grupos.parquet
    ojo       heredar por grupo: si un miembro tiene seccion y otro no, se la
              pasa. Medido: el 64,8 % podria heredar la de Alcampo.
    listo     `select count(seccion) from grupos.parquet` >= 99 % de las filas
    prueba    ya existe `tests/test_secciones.py` (13 pruebas)

### F1a.2 · `seccion` en la API

    hacer     devolverla en `catalogo.buscar()` y en `catalogo.grupo()`
    listo     GET /api/buscar?q=leche trae "seccion": "lacteos-huevos"

### F1a.3 · La lista se agrupa por pasillos

    hacer     en `web/app.js`, dentro de "Por coger", subtitulos por seccion
              usando `core.secciones.ORDEN`, que ya esta en el orden de
              recorrer una tienda
    ojo       lo que no tenga seccion va al final bajo "otros". **No se inventa
              una seccion** para que no quede feo.
    listo     una lista de diez cosas variadas sale agrupada y en el orden en
              que se recorre el super

## F1b · La tabla nutricional de DIA

**Lo mas valioso de esta fase.** DIA publica una tabla completa en el 66 % de
sus fichas y la tiramos entera. Son ~3.570 productos con dato de etiqueta, no
inferido.

### F1b.1 · Cuatro campos en el contrato

    hacer     en `core/schemas.py`, anadir a ESQUEMA_BRONZE:
                nutricion         pl.Utf8    (JSON)
                nutricion_por     pl.Utf8    "100g" | "100ml" | "porcion"
                dias_caducidad    pl.Int32
                peso_escurrido_g  pl.Int32
    ojo       el contrato es de las CINCO cadenas: las que no lo tengan van a
              None, y eso esta bien
    listo     `vacio()` devuelve las cuatro claves nuevas

### F1b.2 · Leerlos en el colector de DIA

    hacer     en `_maestro_de_ficha()` de `collectors/dia.py`, sacar de la ficha:
                energy, fat, saturated_fat, carbohydrate, sugars, dietary_fiber,
                protein, salt   -> un dict a JSON
                nutri_size + nutri_measurement_unit -> nutricion_por
                days_to_expiration -> dias_caducidad
                drained_weight -> peso_escurrido_g
    ojo       los campos vienen como {"value": 3.1, "uom": "g"}. Guardar el
              numero, no el dict.
    listo     una prueba con una ficha de ejemplo devuelve la tabla completa
    medir     `select count(nutricion) from silver where fuente='dia'` >= 3.000

### F1b.3 · Que llegue a gold y a la ficha del producto

    hacer     anadir las cuatro a COLUMNAS en `emparejar.py`; devolverlas en
              `catalogo.grupo()`; pintarlas en la hoja de `web/app.js`
    ojo       la tabla nutricional va DESPUES de alergenos e ingredientes.
              El orden de la ficha esta en `docs/PANTALLAS.md` punto 6 y no es
              negociable: es el orden en que se mira algo en el pasillo.
    listo     un producto de DIA con tabla la ensena; uno de Alcampo no ensena
              una tabla vacia, no ensena nada

### F1b.4 · Reprocesar lo viejo

    hacer     `projects/cesta/reprocesar.py` sobre el crudo guardado
    por que   los 30 dias de raw ya tienen las fichas. No hay que pedir nada.
    listo     la cobertura nutricional del catalogo sube de 22,6 % a ~28 %

## F1c · Los packs de Mercadona, sin adivinar

### F1c.1 · Leer `is_pack` y `total_units`

    hacer     en `collectors/mercadona.py`, `a_registro()`:
                price_instructions.is_pack      -> es_pack
                price_instructions.total_units  -> unidades_pack
    por que   medido: is_pack en el 10,3 % y total_units en el 28,9 % de las
              fichas. **Mercadona lo dice y nosotros lo adivinamos del nombre.**
    listo     un pack de Mercadona trae unidades_pack sin pasar por el regex
    ojo       la regla del nombre (pipeline.py) se QUEDA para las otras cuatro.
              Solo deja de aplicarse cuando la cadena ya lo dijo.

### F1c.2 · Envase

    hacer     `packaging` (Mercadona, 86,2 %) y `package_format_description`
              (DIA, 100 %) -> campo `envase`
    listo     la ficha del producto dice "Brik" o "Botella"

## F1d · El tipo de producto de DIA

### F1d.1 · Guardarlo

    hacer     `product_type` -> campo `tipo_producto`. DIA lo da en el 100 %.
    listo     5.410 productos de DIA con tipo

### F1d.2 · Usarlo como senal de bloqueo en el emparejador

    hacer     en `core/matching.py`: dos productos con tipo conocido y distinto
              NO se emparejan, ni aunque sus nombres se parezcan
    por que   ataca directamente los grupos demasiado anchos (F2), con una
              etiqueta limpia y gratis en vez de con un umbral a ojo
    medir     **`emparejar --medir` antes y despues.** Si los aciertos bajan del
              57 %, se revierte y se piensa otra cosa.
    listo     los aciertos no bajan, y los grupos con dispersion imposible si

---

# F2 · Los grupos, arreglados

**Objetivo**: que "equivalente" signifique algo. Hoy el grupo de agua con gas
mete Perrier (2,40 EUR/l) con la marca blanca de Carrefour (0,28), **con todos
los formatos bien leidos**.

Mientras siga asi, cualquier cifra de diferencia por seccion mide lo ancho que
es el grupo, no el ahorro. Y la funcion de "hay uno mejor y mas barato"
propondria patatas congeladas como alternativa a patatas de bolsa.

### F2.1 · Medir el estado de partida

    hacer     un script que saque, a `data/debug/grupos_anchos.parquet`:
              grupo, n de miembros, n de cadenas, dispersion, y los nombres
    hoy       405 grupos con mas del 200 % de dispersion
    listo     existe el fichero y se puede mirar a mano

### F2.2 · Freno por dispersion

    hacer     si anadir un producto hace que el grupo pase de cierta relacion
              entre el mas caro y el mas barato, no entra como equivalente
    ojo       el umbral se elige MIDIENDO, no a ojo: probar varios y quedarse
              con el que no baje los aciertos
    medir     aciertos >= 57 % y grupos con +200 % por debajo de 150

### F2.3 · Freno por tipo de producto

    depende   F1d.2
    hacer     usar `tipo_producto` como bloqueo duro donde se conozca
    medir     igual

### F2.4 · Umbral por seccion

    depende   F1a.1
    hacer     en refrescos hace falta mas parecido que en legumbres, porque los
              nombres se parecen mas entre si
    medir     igual

### F2.5 · La cola de revision

    hacer     dejar los que sigan anchos en `data/debug/` y una pantalla del
              panel para mirarlos
    listo     se pueden revisar veinte en diez minutos

**Aviso serio**: la ultima vez que se toco el emparejador sin medir, la
cobertura cayo del 53 % al 43 % y costo dias entenderlo. **Medir antes y despues
de cada uno de estos cuatro cambios, por separado.**

---

# F3 · La lista, como se usa de verdad

**Objetivo**: que anadir algo cueste un toque y que la lista se lea con una mano.

### F3.1 · Mosaico de lo habitual

    depende   nada; el dato ya esta en lista_linea (anadido_por, anadido_en)
    hacer     ruta `GET /api/habituales` con los grupos que ese usuario mas ha
              anadido en 90 dias; pintarlo en cuadricula de 3 columnas cuando
              el buscador esta vacio
    ojo       **lista vacia si no hay historial**, y no se pinta nada. No se
              rellena con "populares": no es lo mismo y no sirve.
    listo     anadir algo desde ahi son dos toques

### F3.2 · Voz

    hacer     `SpeechRecognition` del navegador; rellena el campo de busqueda
    ojo       **si el navegador no lo soporta, el boton no se dibuja.** No se
              dibuja y falla al pulsarlo: no se dibuja.
    ojo       en iOS solo Safari, y pide permiso
    listo     "dos litros de leche entera" rellena el buscador

### F3.3 · Notas por linea

    hacer     el campo `nota` ya existe en lista_linea; falta la interfaz.
              Toque largo sobre la linea, o un lapiz.
    listo     "la de cristal" se guarda y se ve bajo el nombre

### F3.4 · Cerrar la compra

    ver       F6.1, que es lo mismo mirado desde el historial

---

# F4 · Las ofertas, visibles

**Objetivo**: que la oferta cambie lo que se ve, no solo lo que se calcula.
La pieza dificil ya esta hecha: `core/promos.py`, 10 pruebas en verde.

### F4.1 · La mecanica, en el resultado de busqueda

    hacer     el sello de oferta ya sale; anadir el texto traducido
              ("3x2", "2a unidad -50%")
    listo     se ve sin abrir el producto

### F4.2 · "Llevate una mas"

    hacer     si una linea tiene oferta aprovechable y llevas menos unidades de
              las que compensan, una linea pequena debajo:
              "llevando 3 en vez de 2, la tercera sale gratis"
    ya existe `unidades_optimas()` lo calcula
    ojo       un producto con "Club Alcampo ... acum en tu tarjeta" NO la
              ensena: ese dinero no se descuenta en caja
    listo     sube de 2 a 3 unidades en un 3x2 y el total de la lista baja

### F4.3 · Filtro "solo con oferta"

    hacer     un chip mas en la busqueda
    listo     filtra y el contador cuadra

---

# F5 · El escaner de codigo de barras

**Objetivo**: apuntar a un producto en la tienda y saber si esta mas barato al
lado. Es la funcion que nadie mas tiene.

**Depende de F0.3 (HTTPS) y conviene despues de F1b y F2.**

### F5.1 · La ruta

    hacer     `GET /api/ean/{codigo}` segun el contrato de `docs/API.md`
    ojo       `comparacion` es `null`, no lista vacia, cuando solo esta en una
              cadena. Vacia se lee como "he mirado y no hay nada mas barato";
              `null` como "no puedo comparar". No es lo mismo.
    listo     cuatro pruebas: conocido multicadena, conocido de una sola,
              desconocido, y codigo mal formado (400)

### F5.2 · La camara, con el nativo

    hacer     `if ('BarcodeDetector' in window)` -> usarlo. Cero dependencias.
    ojo       Chrome Android si. **Safari iOS NO lo soporta.** Firefox tampoco.
    listo     en Chrome Android reconoce un EAN-13 en menos de dos segundos

### F5.3 · El respaldo para iPhone

    hacer     cargar `zxing-wasm` (variante solo lectura, ~1,04 MiB, MIT/Apache)
              **perezosamente**, solo cuando el nativo no existe
    listo     el wasm NO se descarga en Chrome Android

### F5.4 · Las cuatro respuestas

    hacer     las cuatro pantallas de `docs/PANTALLAS.md` punto 6:
              1  lo conozco y puedo comparar      (42 % de los codigos)
              2  lo conozco, una sola cadena
              3  no lo conozco                    (lo normal en Alcampo y Aldi)
              4  sin nutricion                    (54 % de los que conozco)
    ojo       la 3 y la 4 son la mitad del trabajo. **El escaner falla mas veces
              de las que acierta, y eso no es un fallo: es el dato.** La OCU
              critica exactamente esto en Yuka y El CoCo.
    listo     escanear un codigo inventado ensena la 3, con salida al buscador

### F5.5 · Los detalles que lo hacen usable

    hacer     vibracion al reconocer (`navigator.vibrate`, si existe);
              el boton NO SE DIBUJA sin camara, sin permiso o sin HTTPS
    listo     en un navegador sin camara no hay boton que falle

---

# F6 · El historial de compra

**Objetivo**: que dentro de tres meses haya algo que mirar.

**Esto va cuanto antes aunque no se note.** Es barato hoy e imposible de
recuperar despues: sin la tabla, en diciembre no habra historial.

### F6.1 · La tabla y el boton

    hacer     `plataforma/sql/003_compras.sql`:
                compra        id, lista_id, cerrada_por, cerrada_en,
                              cadena_elegida, total_estimado_cent
                compra_linea  compra_id, grupo_id, producto_id, cantidad,
                              precio_cent
              y `POST /api/listas/{id}/cerrar`
    hacer     boton "He terminado la compra" al final de la lista
    ojo       **idempotente por lista y minuto**: pulsar dos veces no crea dos
              compras
    listo     cerrar vacia "en el carro" y deja "por coger"

### F6.2 · Ver el historial

    hacer     `GET /api/compras` y `/api/compras/{id}`; una pantalla simple
    listo     se ven las ultimas compras con su total

### F6.3 · Lo que viene solo, meses despues

    a los 30 dias   sugerencias: "sueles comprar leche y hace once dias que no
                    la pones"
    a los 60        despensa deducida: se compro hace 12 dias, dura 15
                    (`dias_caducidad` de F1b), se acaba el viernes
    a los 90        cuanto gastais al mes y en que secciones

    **Nada de esto se programa ahora.** Se programa cuando haya datos. Lo unico
    que hay que hacer hoy es F6.1.

---

# F7 · El panel completo

**Depende de F1a y F2.** Antes de eso, las cifras por seccion miden la anchura
de los grupos.

### F7.1 · Pantalla de secciones
### F7.2 · Analisis por linea de producto
### F7.3 · "Hay uno mejor y ademas mas barato"

    ojo       hoy propondria "Patatas fritas Hacendado (E) -> Patatas Golden
              McCain (A)", que son patatas de bolsa contra congeladas. Es el
              error que la OCU le achaca a Yuka.

### F7.4 · La nota de salud, rehecha

    hacer     adoptar la formula de Yuka, que esta publicada:
              60 % Nutri-Score · 30 % aditivos (tope 49/100 si hay uno de riesgo
              alto) · 10 % ecologico
    por que   es ABSOLUTA, no una posicion dentro del grupo. Nuestra letra
              actual sale de ordenar por precio el 76,9 % de las veces.
    ojo       un producto sin datos saca **"no lo se"**, nunca un cero
    ojo       nuestro contador de aditivos NO cuenta los aromas (comprobado: 2
              falsos positivos en 400). Si tocas `core/calidad.py`, vuelve a
              comprobarlo.

---

# F8 · Mas datos y mas cadenas

### F8.1 · Lanzar `sondear_fichas.py`

    esfuerzo  una ejecucion y una decision
    puede     desbloquear la nutricion de Alcampo y Aldi, que son el 49,5 % del
              catalogo. **Es la tarea con mejor relacion de todo el plan.**
    ojo       NO tirar 25.000 peticiones a ciegas contra el WAF de Alcampo.

### F8.2 · Traer de Open Food Facts lo que falta

    hacer     tres lineas en `CAMPOS` de `core/off.py`:
              nutriments (11.723), categories_tags (10.209), labels_tags (8.055)
    los sellos  sin gluten 2.667, ecologico 1.205, vegano 763, sin lactosa 717.
                Son filtros que la gente busca de verdad.

### F8.3 · Heredar el EAN por grupo

    hacer     3.375 productos de Alcampo estan enlazados como *identicos* a uno
              con EAN de otra cadena y podrian heredarlo
    ojo       marcado como **inferido**, nunca como leido
    no vale   para Aldi: todos sus enlaces son *equivalentes*

### F8.4 · Lidl

    ojo       **no por su web**: sus fichas de comida llevan una fecha donde
              deberia ir el precio (`docs/LIDL.md`). La via es la API movil de
              Lidl Plus.
    antes     UNA llamada real y mirar que trae. Lo mas probable es que de solo
              las ofertas de la semana, no el surtido: eso seria cobertura
              sesgada y hay que saberlo antes de invertir, no despues.

### F8.5 · Otra cadena

    ver       `docs/COLECTORES.md` punto 4, que tiene el metodo entero
    la pregunta antes de cada una: *¿sus productos van a emparejar con los que
    ya tenemos?* Si trae 20.000 referencias que no casan con nada, ha ensanchado
    el catalogo sin mejorar el comparador.

---

# F9 · Que la puedan usar amigos

**Objetivo**: que la app funcione para alguien que no la construyo y que no vive
en la misma casa. `docs/AMIGOS.md` tiene el analisis completo y
`docs/USABILIDAD.md` los seis sitios donde un amigo se quedaria colgado.

### F9.1 · Lo barato, ya hecho el 17 de septiembre

    hecho   el indice de "lista de casa" pasa a ser por dueno. Era UNICO EN TODA
            LA BASE: el tercero que la creara se llevaria un error de clave
            duplicada que no entiende nadie.
    hecho   `invitado_por` se rellena al aceptar una invitacion
    hecho   tope de tres invitaciones vivas por lista
    hecho   `DELETE /api/yo` y el boton de darse de baja, con confirmacion
            escribiendo el propio usuario
    hecho   plural() en los contadores, el aviso de precios bajo el total, los
            tres ejemplos pulsables al abrir, y los ocho mensajes de error
            reescritos para que digan que ha pasado

### F9.2 · Antes de dar la primera cuenta a alguien de fuera

    decidir  que pasa cuando el PC esta apagado. Con tu madre se resuelve
             encendiendolo; con un amigo en otra ciudad, la app simplemente no
             funciona. Tres salidas en AMIGOS.md punto 3.2.
    decidir  si van a ser mas de seis, Tailscale deja de ser gratis y toca
             mirar Cloudflare, que llega a 50 pero **publica el servicio en
             internet**
    decir    donde viven sus datos. Una linea al crear la cuenta.

### F9.3 · Cuando sean cinco o mas

    buscar gente por @usuario        hoy descartado "porque sois dos"
    varias listas con una activa     lista de casa, del piso, de la barbacoa
    pantalla de actividad            con cinco personas, `anadido_por` en cada
                                     linea deja de bastar

### F9.4 · El repaso de accesibilidad

    recorrer la app entera con el tabulador y ver que el foco se ve siempre;
    medir el contraste del ambar sobre papel claro; comprobar el movil al 200 %
    de texto. **Tu madre va a usar esto durante anos y la vista cansa.**

---

## Como saber que una fase esta terminada

    uv run pytest                                   todo en verde
    uv run ruff check .                             limpio
    uv run python -m projects.cesta.emparejar --medir   >= 57 %
    uv run python -m projects.cesta.verificar_docs      los .md cuadran

Y el criterio de aceptacion propio de cada tarea. Si una tarea no tiene forma de
probarse, esta mal partida: se parte otra vez.
