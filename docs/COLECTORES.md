# Cesta — que deja cada colector sin coger, y como se anade una cadena

Auditado el 17 de septiembre de 2026, leyendo el crudo que ya tenemos en disco.

La conclusion, antes de los detalles: **el patron se repite por quinta vez**. Ya
paso con el precio por kilo de Alcampo, con la marca de Aldi, con los packs de
DIA y con las ofertas de Carrefour. **El dato estaba descargado y guardado, y no
lo pasabamos a bronze.**

Esta vez es mucho mas grande.

---

## 1. DIA publica una tabla nutricional completa y la tiramos

Medido sobre 800 fichas de producto del crudo:

    tabla nutricional (energia + proteina + el resto)   66 %
    dias de caducidad                                  100 %
    tipo de producto                                   100 %
    peso escurrido                                     100 %
    seccion / familia / categoria estructuradas        100 %
    formato del envase                                 100 %
    IVA numerico                                       100 %

De los campos nutricionales, treinta que no guardamos:

    energy        67 %      carbohydrate   60 %      protein        58 %
    salt          57 %      sugars         56 %      fat            54 %
    saturated_fat 50 %      dietary_fiber  20 %      calcium         4 %
    nutri_score    3 %      vitamin_b12/c/d/e, hierro, zinc, magnesio...

**DIA tiene 5.410 productos.** Un 66 % son unos 3.570 con tabla nutricional
propia — sin depender de Open Food Facts, sin depender de que el EAN cruce.

Hoy la cobertura nutricional del catalogo entero es del **22,6 %**. Esto la sube
de forma directa, y encima es **dato de la etiqueta**, no inferido.

### Lo que hay que anadir al contrato

Cuatro campos nuevos en `ESQUEMA_BRONZE` (`core/schemas.py`):

    nutricion         JSON: kcal, grasas, saturadas, hidratos, azucares,
                      fibra, proteinas, sal, por 100 g o 100 ml
    nutricion_por     "100g" | "100ml" | "porcion"   (DIA lo dice en nutri_size
                      y nutri_measurement_unit)
    dias_caducidad    entero. **Nadie mas publica esto.**
    peso_escurrido_g  entero

Y dos que mejoran lo que ya hay:

    envase            "brik", "botella", "paquete"   (DIA y Mercadona)
    tipo_producto     "Leche infantil"  (DIA, 100 %)

### Por que `dias_caducidad` vale mas de lo que parece

Es el unico campo del proyecto que ninguna otra app tiene. Con el:

- la despensa deducida (`FUNCIONALIDADES.md` D1) puede avisar **sin que nadie
  teclee una fecha**: se compro hace 12 dias, dura 15, se acaba el viernes
- la lista puede ordenar lo fresco al final del recorrido, que es como se compra
- y el panel puede decir que secciones generan mas desperdicio potencial

### Por que `tipo_producto` puede arreglar el emparejador

DIA clasifica cada producto en un tipo fino ("Leche infantil", no "Lacteos").
Eso es **una etiqueta gratis y limpia** para 5.410 productos, y el emparejador
hoy adivina el tipo a partir del nombre.

Dos usos, en este orden:

1. Como **senal de bloqueo**: dos productos de tipos distintos no se emparejan,
   ni aunque sus nombres se parezcan. Eso ataca directamente el problema de los
   grupos demasiado anchos (`BACKLOG.md` tarea 2).
2. Como **conjunto de entrenamiento** si algun dia se hace el clasificador.

---

## 2. Mercadona: seis campos gratis en la misma ficha

Medido sobre las 4.378 fichas maestras que ya tenemos guardadas:

    packaging            86,2 %    "Botella", "Paquete", "Brik"
    total_units          28,9 %    cuantas unidades lleva el pack
    main_feature         23,9 %    la caracteristica destacada
    pack_size            11,4 %
    is_pack              10,3 %    **Mercadona dice si es un pack. Nosotros lo
                                   adivinamos del nombre.**
    drained_weight        4,1 %    179 productos, y son justo las conservas
    previous_unit_price   3,8 %    precio anterior por unidad
    reference_format     100 %     "L", "kg" — la unidad de su precio de
                                   referencia, estructurada

**`is_pack` y `total_units` son importantes**: el 16 de septiembre arreglamos a
mano los packs que solo se anuncian en el nombre, con una regla que valida
contra el precio de la cadena. Para Mercadona **no hace falta adivinar**: lo
dice el campo. La regla del nombre se queda para las demas.

**`drained_weight`** son 179 productos, pero son atún, legumbres y conservas:
exactamente donde comparar por peso escurrido en vez de por peso total cambia
cuál es más barato. DIA publica un campo con ese nombre en el 100 % de sus fichas
y **no es el peso escurrido** (es la densidad del aceite: ver `docs/AUDITORIA.md`,
punto 6), así que `peso_escurrido_g` se queda a `None` para DIA: el único escurrido
de verdad del catálogo es el de Mercadona. Desde el 26 de septiembre de 2026 esos
179 productos se comparan **por el escurrido** (y la cifra lo dice: «€/kg
escurrido»), con la medición en `docs/DATOS-QUE-NO-COGEMOS.md`, punto 5 bis.

---

## 3. Lo que NO se puede sacar, para no perder el tiempo buscandolo

    Alcampo    su listado no trae EAN, ni ingredientes, ni nutricion. Solo el
               `sondear_fichas.py` puede decir si su ficha los trae, y sigue
               sin lanzarse.
    Aldi       igual, y ademas su catalogo es de 2.065 productos.
    Carrefour  trae EAN (93 %) pero ni ingredientes ni nutricion en el listado.

O sea: **la mejora de este documento es de DIA y Mercadona**, que ya eran las dos
cadenas mas completas. La brecha con Alcampo y Aldi se hace **mas grande**, no
mas pequena. Eso hay que tenerlo presente al ensenar nutricion en la app: sera
aun mas frecuente que un producto de Alcampo no tenga nada al lado de uno de DIA
que lo tiene todo.

---

## 4. Como se anade una cadena nueva

Esto no estaba escrito en ningun sitio y es lo primero que va a preguntar quien
venga detras.

### 4.1 Antes de escribir una linea de codigo

    1. robots.txt      leerlo entero y respetarlo. Lidl tiene `Disallow: *id=*`
                       y eso cubre casi cualquier listado util.
    2. ¿publica precios de alimentacion en la web?
                       Lidl NO: sus fichas de comida llevan una fecha donde
                       deberia ir el precio. Se comprobo y se dejo escrito en
                       docs/LIDL.md antes de escribir codigo.
    3. una peticion    UNA. A mano, con curl. Y mirar que trae.
    4. ¿hay EAN?       decide si esa cadena podra tener nutricion o no
    5. ¿hay precio por unidad?
                       decide si entra en las comparaciones o solo en el catalogo

**Si el paso 2 falla, se para y se deja escrito por que.** `docs/LIDL.md` es el
modelo: tres pantallas explicando por que no hay colector, con las pruebas.

### 4.2 El colector, pieza a pieza

Un fichero en `projects/cesta/collectors/<cadena>.py` con:

    FUENTE = "<cadena>"
    a_registro(p) -> dict      traduce SU vocabulario al nuestro (29 columnas)
    main() -> int              recorre el catalogo y escribe bronze

Y tres reglas que no se negocian, aprendidas a base de perderlas:

1. **Guardar el crudo antes de interpretarlo.** `save_raw()` con la respuesta
   tal cual. Es lo que permitio arreglar diez dias de Alcampo sin pedirle nada.
2. **No guardar nunca un reto de WAF como si fuera catalogo.** El 6 de
   septiembre, 114 de 352 ficheros de Alcampo eran paginas de desafio guardadas
   como si fueran productos. Ver `_cache_limpia()` en `collectors/alcampo.py`.
3. **Punto de control cada N productos.** Si el proceso muere a las dos horas,
   no se pierden las dos horas. `PASO_MAESTRO = 250` en mercadona y dia.

### 4.3 El ritmo

`core/config.py`, diccionario `RITMO`, peticiones por segundo:

    mercadona  2,0     API abierta, sin defensas
    aldi       2,0     web publica, sin defensas
    dia        1,0     Akamai
    carrefour  1,0     Cloudflare
    alcampo    0,15    AWS WAF. Seis por minuto. Y aun asi corta a veces.

**Empezar siempre por el mas lento que sea tolerable** y subir si va bien. Al
reves se aprende una sola vez.

### 4.4 Lo que hay que medir antes de darla por buena

    productos capturados      comparado con lo que dice su propia web
    % con precio por unidad   si es bajo, no entra en las comparaciones
    % con EAN                 si es cero, nunca tendra nutricion
    % con formato legible     `formato_parseado` en silver
    desviacion_ref            cuanto discrepa nuestro precio por kilo del suyo.
                              Si es alta, hay un formato mal leido.
    aciertos del emparejador  `emparejar --medir` ANTES y DESPUES. Si baja, la
                              cadena nueva esta ensuciando los grupos.

Ese ultimo punto es el importante: **una cadena que baja el 57 % de aciertos
hace mas dano que bien**, por muchos productos que traiga.

### 4.5 Candidatas, por lo que se sabe hoy

QueFalta tiene catalogo de 19 cadenas espanolas, asi que **son scrapeables por
alguien**. Por orden de lo que aportarian:

    Lidl          el que mas falta hace por cuota de mercado. La via NO es su
                  web (ver docs/LIDL.md) sino la API movil de Lidl Plus:
                  stores.lidlplus.com y offers.lidlplus.com. **Sin verificar**:
                  puede que solo de las ofertas de la semana y no el surtido,
                  lo que seria una cobertura sesgada. Una llamada real lo dice.
    Consum        cooperativa, fuerte en Levante
    Eroski        fuerte en el norte, y crece en online
    Ahorramas     fuerte en Madrid, y crece en online
    Bonpreu       Cataluna
    HiperDino     Canarias, donde los precios son distintos de verdad

**No anadir por anadir.** Cinco cadenas que se comparan entre si valen mas que
diez que no. La pregunta antes de cada una es: *¿sus productos van a emparejar
con los que ya tenemos?* Si trae 20.000 referencias que no casan con nada, ha
ensanchado el catalogo y no ha mejorado el comparador.

---

## 5. Lo que hay que hacer, en orden

    1. Tabla nutricional de DIA        ~3.570 productos, dato de etiqueta
    2. is_pack y total_units de
       Mercadona                       deja de adivinar lo que la cadena dice
    3. tipo_producto de DIA            senal de bloqueo para el emparejador,
                                       ataca los grupos demasiado anchos
    4. dias_caducidad de DIA           nadie mas lo tiene; alimenta la despensa
    5. envase y peso escurrido         la ficha del producto se completa
    6. Lanzar sondear_fichas.py        puede desbloquear Alcampo y Aldi
    7. Lidl, con una llamada real
       antes de escribir nada

Las cinco primeras **no requieren ni una peticion nueva a nadie**: el dato ya
esta en `data/raw/`. Es leer y mapear.
