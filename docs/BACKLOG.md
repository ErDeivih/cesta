# Cesta — trabajo pendiente, listo para ejecutar

Escrito el 17 de septiembre de 2026 para quien coja el proyecto a partir de
aqui, sea persona o agente. Cada tarea trae **por que**, **que hay que hacer**,
**donde**, y **como se sabe que esta bien**.

Los numeros son medidos, no estimados. Si al ejecutar una tarea el numero no
sale, es que algo ha cambiado: hay que volver a medir antes de seguir.

---

## El orden, de un vistazo

    1   Secciones comunes                  M    desbloquea 4 cosas. EMPEZAR AQUI.
    2   Grupos demasiado anchos            M    desbloquea otras 3. Medir siempre.
    3   Anadir sin escribir                S    mosaico + voz
    4   La oferta mientras anades          S    la pieza dificil ya esta hecha
    5   Notas por linea y aviso legal      XS   dos ratos
    6   Traer de Open Food Facts           S    nutrientes, categorias, sellos
    7   Sondear fichas de Alcampo y Aldi   XS   una ejecucion y una decision
    8   Escaner de codigo de barras        M    la funcion diferencial
    9   La nota del producto, rehecha      M    arregla un problema de raiz
    10  Guardar el cierre de compra        S    barato ahora, imposible despues

Las tareas 1 y 2 van primero porque **bloquean a las demas**, no porque sean las
mas vistosas. La 10 va pronto aunque no se note: sin ella, en diciembre no habra
historial que mirar.

`docs/FUNCIONALIDADES.md` tiene el catalogo entero con veredicto, incluido lo
descartado y por que, para no volver a discutirlo.

---

## 0. Rehacer el matching y la interfaz (encargo del 22 de septiembre)

**Por que.** Hay un encargo nuevo del dueno: migrar la interfaz a un stack
especializado y arreglar el matching, **sin ninguna validacion humana**. El plan
maestro es `docs/PLAN-UI-MATCHING.md` y su informe es
`docs/DIAGNOSTICO-MATCHING.md`.

**Lo que ya esta hecho (22 sep 2026).**

    docs/DIAGNOSTICO-MATCHING.md            el informe, con todos los numeros
    projects/cesta/diagnostico_matching.py  lo reproduce en un comando
    tests/test_diagnostico_matching.py      11 pruebas, en verde
    core/normalize.py                       la etiqueta de 100 g/ml, por cadena
    projects/cesta/pipeline.py              cantidad_fiable, la unidad que se
                                            contradice, respaldo por el nombre
    core/matching.py                        asignacion hungara 1-a-1, la
                                            etiqueta identico veraz, veto de
                                            precio y freno de grupo
    core/equivalencias.py                   Fase 1: producto_id estable y cada
                                            pasada versionada, con su motivo
    tests/test_equivalencias.py             10 pruebas
    projects/cesta/collectors/carrefour.py  cat11729677 en ROTAS_EN_ORIGEN
    git                                     el proyecto YA tiene control de
                                            versiones; no tenia .git

**Los numeros, antes y despues, medidos sobre el mismo bronze.**

    aciertos de emparejar --medir       57 %   ->  65 %    (el liston es 57 %)
    productos comparables               19.834 ->  23.047  (+16 %)
    grupos comparables                  6.431  ->  7.925   (+23 %)
    enlaces aceptados                   18.001 ->  22.702
    grupo mayor                         329    ->  97
    etiqueta identico que dice verdad   70 %   ->  100 %
    fallos por "otra unidad"            172    ->  39
    grupos con el mas caro >200 %       369    ->  448     (tasa 6,5 % -> 6,3 %)

**Lo que queda mal, con las dos causas ya identificadas y medidas.**

Los grupos anchos NO vienen de un par malo: de los 22.702 enlaces, **0** violan el
veto de precio de 30x. Vienen de dos sitios distintos:

1. **Un grupo es lo que queda conectado, y eso se propaga.** Y no por muchos
   enlaces flojos, sino por **uno solo**: dentro del grupo 92 (97 productos, 181
   enlaces internos) el parecido mediano es **1,00** y lo que lo sostenia eran dos
   puentes de 0,55 (`Mahou tostada 0,0` <-> `Saer Brau tostada 0,0` <-> `Mahou
   tostada`). Ya hay un freno (`core.matching.agrupar_enlaces`, union 0,80: un
   enlace flojo puede meter a un producto suelto pero no pegar dos grupos) que
   baja el mayor de 329 a 97 y sube los comparables de 6.589 a 7.925. Se probo
   una version mas dura (un flojo solo entre dos sueltos): frena el error a la
   mitad, pero **hunde la letra de calidad de 12.996 a 5.546 productos** y se
   descarto midiendo.
2. **El IDF se calcula sobre el catalogo entero**, y ahi "cerveza" parece una
   palabra rarisima (600 cervezas entre 52.567 productos) cuando entre cervezas no
   distingue nada. El arreglo es calcular los pesos **dentro de la seccion**, y
   obliga a recalibrar el umbral 0,55 entero contra `--medir`. Es la tarea 2.
3. Y el grupo 30054 no es de emparejamiento: DIA publica **1 g** para unos filetes
   de dorada de "300 g aprox". Es el mismo roto que los 33 detergentes "de 61
   litros": el dato de cantidad de lo que se vende al peso.

El criterio del BACKLOG (**menos de 150 grupos con mas del 200 %**, hoy 448) no se
cumple y no se va a cumplir con frenos. **Esto sustituye a la tarea 2**, con las
dos pistas medidas en `docs/DIAGNOSTICO-MATCHING.md` §16.

Y una cosa que ya no cuesta nada: `uv sync --extra plataforma` esta hecho, asi
que `pytest` completo pasa de 545 a **585 en verde** (los 30 de mas son las
pruebas de la API, que no corrian por falta de fastapi). Quedan 2 fallos, los dos
de `test_verificar_precios`, que van de contar bien el caso "no hubo conexion" y
"la pagina no trae precio" — no tienen que ver con el matching.

**Las decisiones que se tomaron, y por que.**

1. **git**: hecho. Habia dos agentes escribiendo en los mismos ficheros sin red.
2. **El front se rehace con Vite + React + TS, y Caddy lo sigue sirviendo.** Nada
   de FastAPI sirviendo HTML: `docs/API.md:336` sigue valiendo. Se actualizo
   `docs/APP.md:318`. Cambio pendiente para el dia del front: en
   `docker-compose.yml:61`, `./web:/srv:ro` pasa a `./web/dist:/srv:ro`.
3. **Ningun veto duro por unidad ni por categoria.** Medido: los 266 enlaces con
   unidad distinta eran, los 266, el mismo producto (mismo EAN). Y
   `docs/MODELO.md:42-45` ya decia que en un grupo manda una unidad pero a nadie
   se le expulsa.
4. **El umbral de precio es 30x, no el 60 % del plan.** Con el 60 % habria marcado
   3.191 de 17.789 enlaces; con 30x, 13.
5. **Hay dos topes de referencia, no uno**: la sonda del EAN (precision) y el
   bloque canonico (40.303 productos, 32.873 pares). "El tope del EAN" sale hoy
   100 % por construccion y no mide nada.

**Consecuencia para este BACKLOG.**

1. La tarea 2 ("Grupos demasiado anchos") **sigue siendo el bloqueo numero uno**,
   con el diagnostico afinado: freno de grupo, no de par. Sus criterios siguen
   valiendo (>= 57 % de aciertos, de 405 grupos >200 % a menos de 150).
2. **N8 ("el boton *esto no es lo mismo*") queda anulado**: es validacion humana,
   que el encargo nuevo prohibe. Las colas de revision a mano de la tarea 2 y de
   `docs/FASES.md` tambien. Se sustituyen por un panel de auditoria que explica
   cada par sin que nadie apruebe nada.

---

## Antes de tocar nada

Lee, por este orden:

    docs/DATOS.md         que es parquet, DuckDB y las cuatro capas
    docs/CADENAS.md       que publica de verdad cada supermercado
    docs/COMPETENCIA.md   que hacen las otras apps y que nos llevamos
    plataforma/LEEME.md   como se levanta y que hay dentro

Y respeta estas cuatro reglas, que estan metidas en el codigo y **deshacerlas
rompe cosas que ya hemos aprendido por las malas**:

1. **Una letra de calidad sacada del precio no se llama calidad.** El 77 % de
   ellas salen de ordenar por precio, no de leer una etiqueta. La API devuelve
   `calidad` solo si viene de ingredientes, y `gama` si viene del precio.
   Mezclarlas produce la conclusion falsa de que lo barato es peor.
2. **Una oferta es una regla, no un precio.** "2a unidad -50%" no abarata el
   producto, abarata el par. Y los descuentos de tarjeta **no bajan el total**:
   no se descuentan en caja.
3. **Ninguna correccion de dato se aplica sin que algo independiente la
   confirme.** El patron esta en `pipeline.py`: el nombre dice "pack 24 x 33 cl"
   pero solo se multiplica si el precio resultante cuadra al 5 % con el que
   publica la cadena. De 211 candidatos se corrigieron 110; los 101 que no
   cuadran se quedaron como estaban.
4. **Cada precio lleva su fecha**, y uno de mas de tres dias se ensena pero no
   decide en que tienda comprar.

Comprobacion antes de dar nada por hecho:

    uv run pytest                    180 pruebas, todas en verde
    uv run ruff check plataforma/    limpio

---

## 1. Secciones comunes entre cadenas  ← EMPEZAR POR AQUI

**Por que.** Es lo que mas desbloquea de todo el proyecto: la lista ordenada por
pasillos (la mejora que mas se nota en el supermercado, y que tienen las tres
apps de lista), el "Explorar" de la app, la pantalla de secciones del panel y el
analisis por linea de producto. Hoy cada cadena tiene su arbol y no hay uno
comun.

**Lo que se creia y era falso.** Que esto pedia un clasificador de texto. No:
son **849 claves** en total, y ya hay un fichero con **el 97 % propuesto**.

**Lo que YA esta hecho** (17 de septiembre):

    core/datos/secciones.yml    849 claves, **todas asignadas**. Cobertura
                                medida: 99,9 % de los productos.
                                Alcampo, Carrefour, DIA y Mercadona al 100 %;
                                Aldi al 96,7 %.
    core/secciones.py           `seccion_de(fuente, categoria)`, `orden_de()`
                                y `sin_asignar()`. Sin dependencias.
    tests/test_secciones.py     13 pruebas, incluida una que avisa si una cadena
                                cambia su arbol y aparecen claves sueltas.

**Lo que falta:**

1. En `projects/cesta/emparejar.py`, anadir la columna `seccion` a
   `grupos.parquet`. **Y heredarla por grupo**: si un miembro del grupo tiene
   seccion y otro no, se la pasa. Medido: el 64,8 % de los productos que estan
   en un grupo podrian heredar la seccion del miembro de Alcampo.
2. En `plataforma/api/catalogo.py`, devolver `seccion` en buscar y en la ficha.
3. En la lista del movil, agrupar por seccion **dentro de "Por coger"**, usando
   `core.secciones.ORDEN`, que ya esta en el orden en que se recorre una tienda.
   Lo que no tenga seccion va al final, bajo "otros": **no se inventa una
   seccion** para que no quede feo.

**Como se sabe que esta bien.**

    - `uv run pytest tests/test_secciones.py` en verde (13 pruebas)
    - la columna `seccion` llega a grupos.parquet con >= 99 % de cobertura
    - la lista del movil se agrupa y el orden es el de recorrer la tienda
    - un producto sin seccion aparece bajo "otros", al final, y no desaparece

**Lo que NO hay que hacer.** Un clasificador. Si al final quedan restos sin
seccion, se miran y se anaden al fichero. El aprendizaje automatico aqui es una
red de seguridad para mas adelante, no el plan.

---

## 2. Grupos demasiado anchos

**Por que.** Es el bloqueo numero uno del panel y ensucia el comparador. El grupo
de agua con gas mas disperso mete Perrier (2,40 EUR/l) con la marca blanca de
Carrefour (0,28), **con todos los formatos bien leidos**. No es un fallo de
formato: es que "equivalente" se esta estirando demasiado.

Mientras siga asi, cualquier cifra de "diferencia de precio por seccion" mide lo
ancho que es el grupo y no el ahorro.

**Que hay que hacer.**

1. Medir primero: cuantos grupos tienen mas de N miembros y mas de X % de
   dispersion. Hoy hay 405 con mas del 200 %.
2. Probar dos frenos, por separado y midiendo cada uno contra el 57 % de
   aciertos de `emparejar --medir`:
   - **Tope de dispersion dentro del grupo**: si anadir un producto hace que el
     grupo pase de cierta relacion entre el mas caro y el mas barato, no entra
     como equivalente.
   - **Umbral por seccion** (necesita la tarea 1): en refrescos hace falta mas
     parecido que en legumbres, porque los nombres se parecen mas entre si.
3. Dejar una cola de revision: `data/debug/grupos_anchos.parquet` con los que
   quedan, para mirarlos a mano.

**Como se sabe que esta bien.**

    - los aciertos de `emparejar --medir` NO bajan del 57 %
    - los grupos con mas del 200 % de dispersion bajan de 405 a menos de 150
    - el grupo del agua con gas ya no mete Perrier con la marca blanca

**Cuidado.** La ultima vez que se toco el emparejador sin medir, la cobertura
bajo del 53 % al 43 % y costo entenderlo. Mide antes y despues, siempre.

---

## 3. Anadir sin escribir

**Por que.** Es lo que separa una lista que se usa de una que se abandona. Las
tres apps de lista lo tienen resuelto y nosotros no: hoy hay que escribir en un
buscador. En el pasillo, con una mano, eso es demasiado.

**Tres cosas distintas, en este orden de valor.**

### 3.1 Mosaico de lo habitual

Una cuadricula con lo que esa persona ha puesto mas veces en sus listas, con su
foto, a un toque. Es lo primero que se ve al abrir la pestana de buscar cuando
el campo esta vacio.

    dato        ya lo tenemos: lista_linea tiene anadido_por y anadido_en
    consulta    los 24 grupos que mas veces ha anadido ese usuario en 90 dias
    donde       plataforma/api/main.py (ruta nueva /api/habituales)
                plataforma/web/app.js (se pinta al vaciarse el buscador)

### 3.2 Voz

`SpeechRecognition` del navegador. Gratis, sin servidor y sin dependencias.
**No es un asistente**: es un atajo para no escribir. "dos litros de leche
entera" rellena el campo de busqueda y, si detecta cantidad, la propone.

Ojo: en iOS solo funciona en Safari y pide permiso. Si no esta disponible, el
boton del microfono **no se dibuja**, en vez de dibujarse y fallar.

### 3.3 Sugerencias del historial

"Sueles comprar leche y hace nueve dias que no la pones." Necesita unos meses de
listas hechas para no decir tonterias. **Anotado para diciembre**, no ahora.

**Como se sabe que esta bien.**

    - con el buscador vacio se ve el mosaico, y anadir algo desde ahi son dos
      toques (el producto y ya)
    - el boton de voz no aparece en un navegador que no lo soporta
    - las sugerencias no salen hasta tener 30 dias de listas

---

## 4. La oferta mientras anades

**Por que.** Es la idea buena de Tiendeo: *"puedes hacer la lista y al mismo
tiempo ver las promociones de los productos que estas anadiendo"*. Nosotros
podemos hacerlo mejor que ellos porque sabemos el precio **y la mecanica**: no
"hay una promo", sino "llevando dos, 1,50 EUR menos por unidad".

La pieza dificil ya esta hecha (`core/promos.py`, 10 pruebas en verde). Falta
ensenarla.

**Que hay que hacer.**

1. En el resultado de busqueda, el que tiene oferta lleva su sello (ya se hace)
   **y el texto de la mecanica traducido**: "3x2", "2a unidad -50%".
2. En la lista, si una linea tiene oferta aprovechable y llevas menos unidades
   de las que compensan, una linea pequena debajo: *"llevando 3 en vez de 2, la
   tercera sale gratis"*. `unidades_optimas` ya lo calcula.
3. Una pestana o filtro "solo con oferta" en la busqueda.

**Como se sabe que esta bien.**

    - un producto con "3x2" ensena la sugerencia cuando llevas 2
    - un producto con "Club Alcampo ... acum en tu tarjeta" NO la ensena,
      porque ese dinero no se descuenta en caja
    - el total de la lista baja al subir de 2 a 3 unidades en un 3x2

---

## 5. Notas por linea, y el aviso legal

Dos cosas pequenas que no cuestan casi nada.

**Notas.** El campo `nota` existe en `lista_linea` y la interfaz no lo usa.
"la de cristal", "si hay del grande". Un toque largo sobre la linea, o un lapiz.

**El aviso.** Copiar el de QueFalta porque es correcto y hay que decirlo:
*"Los precios son orientativos y pueden variar"* y *"Cesta no esta afiliada,
asociada ni patrocinada por ninguno de estos supermercados"*. En ajustes, y una
linea pequena bajo el total de la lista.

---

## 6. Traer de Open Food Facts lo que no traemos

**Por que.** Medido contra el volcado entero (7,9 GB, ya esta en
`data/externo/food.parquet`). De nuestros 12.835 productos que cruzan por codigo
de barras:

    nutrientes completos (kcal, grasas, azucares, sal)   11.723   <- no lo traemos
    categorias                                           10.209   <- no lo traemos
    sellos                                                8.055   <- no lo traemos
      sin gluten 2.667 | ecologico 1.205 | vegano 763
      sin lactosa 717 | sin aceite de palma 267
    origen                                                1.248   (solo 635 "en:spain")

**Que hay que hacer.** Tres lineas en `CAMPOS` de `core/off.py`
(`nutriments`, `categories_tags`, `labels_tags`) y llevarlas a gold.

Los **sellos** son el hallazgo util: dan filtros que la gente busca de verdad
("sin gluten", "sin lactosa", "vegano") y tienen entre dos y cuatro veces mas
cobertura que el origen.

**Lo que NO hay que prometer.** El filtro de producto nacional. Techo realista:
unos 1.900 productos de 52.575, el 3,7 %. No hay fuente que lo arregle — BEDCA
describe alimentos genericos, no productos con codigo de barras. Se queda
escondido y se dice por que.

---

## 7. Sondear las fichas de Alcampo y Aldi

**Por que.** Son el 50 % del catalogo y ninguno publica codigo de barras en el
listado. Sin EAN no hay cruce con Open Food Facts, y por tanto no hay
Nutri-Score, ni NOVA, ni ingredientes, para 25.600 productos.

DIA y Mercadona tampoco lo dan en el listado: lo dan en la **ficha**, y por eso
los dos tienen un maestro incremental que solo pide fichas que no conoce.

**Que hay que hacer.** Ejecutar `uv run python -m projects.cesta.sondear_fichas`
(escrito, sin lanzar: desde la sesion no hay salida a esos dominios). Pregunta
**una vez por un producto** a un punado de direcciones candidatas y cuenta que
trae cada respuesta.

    si alguna trae ean/gtin   escribir el maestro incremental calcado al de DIA
                              (collectors/dia.py, funcion `_ficha`). Ritmo lento,
                              fichero permanente: el EAN no cambia, se pide una
                              vez en la vida y el catalogo se cubre en semanas
    si solo trae nutricion    sigue mereciendo la pena: el EAN solo era el camino
    si no trae nada           se deja escrito en CADENAS.md y se deja de buscar

**Lo que NO hay que hacer.** Tirar 25.000 peticiones a ciegas contra el WAF de
Alcampo. Es la forma mas rapida de cerrar la puerta que hoy tenemos abierta,
despues de tres semanas costando que se quede abierta.

**Mientras tanto, y esto se puede hacer hoy:** 3.375 productos de Alcampo estan
enlazados como *identicos* a un producto con EAN de otra cadena y podrian
heredarlo, marcado como **inferido**, nunca como leido. Aldi no puede: todos sus
enlaces son *equivalentes*, porque es marca propia entera.

---

## 8. Escaner de codigo de barras

**Por que.** Es nuestra funcion diferencial. Yuka te dice si un producto es sano.
El lector de precios de Mi Carrefour te dice cuanto cuesta en Carrefour. **Nadie
te dice si esta mas barato en la tienda de al lado.** Y escanear con el movil en
la tienda ya es una costumbre establecida en Espana, asi que no hay que ensenar
el gesto.

**Lo que aguantan los datos** (medido el 17 de septiembre):

    codigos de barras que reconocemos                23.312
    ... de los que podemos comparar precio            9.811   (42 %)
    ... de los que tenemos algo de nutricion         10.826   (46 %)
    ... cuyo grupo llega hasta Alcampo                7.809   (34 %)

    por cadena:  Mercadona 100 % · DIA 100 % · Carrefour 93 %
                 Alcampo 0 % · Aldi 0 %

**El detalle que salva la funcion.** El codigo de barras es **del fabricante**,
no de la cadena. Escaneando una Coca-Cola dentro de un Alcampo, el codigo casa
con la fila de Carrefour, y como el grupo incluye tambien la de Alcampo
(emparejada por nombre), se puede comparar igual. Lo que no funcionara nunca es
escanear la marca propia de Alcampo o de Aldi: esos productos no tienen codigo en
nuestro catalogo.

### Lo tecnico

    Chrome Android     `BarcodeDetector` nativo. Funciona.
    Safari iOS         **NO lo soporta**, desactivado por defecto
    Firefox            tampoco

Asi que:

1. `if ('BarcodeDetector' in window)` → usar el nativo, cero dependencias.
2. Si no → **cargar perezosamente** `zxing-wasm` (variante solo lectura,
   ~1,04 MiB, MIT/Apache 2.0, lee EAN-13 y EAN-8). Solo se descarga cuando hace
   falta, no en cada visita.
3. La camara pide `getUserMedia` con `facingMode: 'environment'` y **solo
   funciona en HTTPS o en localhost**. Detras de Tailscale con http:// no va:
   hay que resolverlo con el certificado de Tailscale (`tailscale cert`) o
   avisar de que el escaner solo va en el PC.

**Esto ultimo hay que comprobarlo antes de prometer nada.** Si no hay HTTPS, el
escaner no existe, por bien que este programado.

### Las cuatro respuestas que tiene que saber dar

El escaner falla mas veces de las que acierta, y eso **no es un fallo: es el
dato**. Las cuatro pantallas tienen que estar disenadas, no solo la buena:

    1. LO CONOZCO Y PUEDO COMPARAR      (42 % de los codigos)
       "Atun Calvo 3x80 g — 3,45 EUR aqui. En Alcampo 2,89 (-16 %)"
       + la ficha entera + boton de anadir a la lista

    2. LO CONOZCO PERO SOLO EN UNA CADENA
       "Lo tengo en DIA a 3,45 EUR. No lo encuentro en las demas."
       No inventar una comparacion que no existe.

    3. NO LO CONOZCO                     (lo mas frecuente en Alcampo y Aldi)
       "No tengo este codigo. Puede ser marca propia de Alcampo o Aldi, que no
        publican codigo de barras."
       + buscador por nombre como salida, no un callejon sin salida.

    4. NO TENGO NUTRICION                (54 % de los que conozco)
       El precio se ensena igual. Donde iria la nota, pone **"no lo se"**, no
       un cero ni una nota gris. La OCU critica exactamente esto en Yuka y
       El CoCo: base de datos incompleta que da notas inexactas.

### Como se sabe que esta bien

    - escanear un EAN conocido de Mercadona ensena la comparacion en menos de
      dos segundos desde que se enfoca
    - escanear un codigo inventado ensena la pantalla 3, con el buscador
    - en un navegador sin camara o sin permiso, el boton del escaner NO SE
      DIBUJA (no se dibuja y falla: no se dibuja)
    - el wasm NO se descarga en Chrome Android
    - una prueba de `GET /api/ean/{codigo}` con: codigo conocido multicadena,
      conocido de una sola, desconocido, y codigo mal formado

---

## 9. La nota del producto, rehecha

**Por que.** Nuestra letra A/B/C de hoy es una posicion **dentro del grupo**, y
cuando ningun producto del grupo publica ingredientes cae a ordenar por precio:
**el 76,9 % de las letras son el precio disfrazado**. Ya nos hizo publicar una
conclusion falsa una vez ("la marca blanca es peor") y la app tiene que llamarla
`gama` para no mentir.

**La solucion no es parchear: es cambiar de nota.** Yuka tiene su formula
publicada y es mejor porque es **absoluta**:

    60 %   calidad nutricional    la metodologia del Nutri-Score
    30 %   aditivos               con tope en 49/100 si hay uno de riesgo alto
    10 %   ecologico              bonus si lleva sello organico oficial

**Lo que tenemos para calcularla:**

    Nutri-Score          8.359 productos
    ingredientes          6.863
    al menos uno de los dos           11.724   (22,6 % del catalogo)
    sellos de OFF (tarea 6)            8.055   → el 10 % de ecologico

**Lo que hay que conservar del sistema actual**, y es lo que nos distingue de
Yuka: **la procedencia**. Un producto sin datos no saca un cero, saca **"no lo
se"**. Eso es justo lo que la OCU echa en falta en Yuka y El CoCo.

**Lo que ya esta bien y no hay que tocar.** Nuestro contador de aditivos exige
`E` seguido de tres o cuatro digitos, asi que **no cuenta los aromas como
aditivos**, que es el error que la OCU documenta en Yuka y MyRealFood.
Comprobado el 17 de septiembre: 2 falsos positivos en 400 productos revisados.
Si tocas `core/calidad.py`, vuelve a comprobarlo.

### Como se sabe que esta bien

    - un producto sin Nutri-Score ni ingredientes devuelve `nota: null` y la
      app pone "no lo se", nunca un numero
    - un producto con un aditivo de riesgo alto no pasa de 49
    - la nota NO cambia al cambiar de grupo (es absoluta: esa es toda la gracia)
    - se conserva `gama` para ordenar dentro de un grupo, y se sigue llamando
      gama

---

## 10. Guardar el cierre de compra

**Por que.** Es barato ahora e imposible de recuperar despues. Sin esto, en
diciembre no habra historial que mirar, y todo lo de la seccion D de
`FUNCIONALIDADES.md` (despensa deducida, sugerencias, "sueles comprar leche cada
nueve dias") no tendra con que funcionar.

**Que hay que hacer.** Una tabla `compra`:

    compra        id, lista_id, cerrada_por, cerrada_en, cadena_elegida,
                  total_estimado_cent
    compra_linea  compra_id, grupo_id, producto_id, cantidad, precio_cent

Y un boton "he terminado la compra" en la lista que: guarda las lineas que
estaban en el carro, las quita de la lista, y deja las que no se cogieron.

**Como se sabe que esta bien.**

    - cerrar una compra vacia la parte "en el carro" y deja "por coger"
    - el historial queda consultable en /api/compras
    - cerrar dos veces no duplica (idempotente por lista y minuto)

---

## 11. Lo que se llena solo

No hay nada que programar. Se apunta para que nadie lo de por roto:

    tendencia_30d       necesita 30 dias   →  5 de octubre
    oferta_sospechosa   necesita 45 dias   →  20 de octubre
    posicion_90d        necesita 90 dias   →  diciembre
    estacionalidad      necesita un ano    →  septiembre de 2027

`oferta_sospechosa` da hoy cero casos porque compara con el precio de hace 45
dias y llevamos doce. **No esta roto: esta esperando.** El panel ya lo dice en
pantalla, con los dias que faltan.

---

## 12. Mas adelante, y por que no ahora

**Recetas a lista.** Util de verdad, pero es un modulo entero: guardar recetas,
sacar ingredientes, casarlos con productos del catalogo (que es el mismo
problema del emparejador, otra vez). Despues de 1 a 4.

**Clasificador de texto para las secciones.** Solo si tras la tarea 1 quedan
restos sin colocar. Hay 10.209 ejemplos etiquetados gratis en Open Food Facts.
TF-IDF y regresion logistica; ni se te ocurra una red neuronal con ese volumen.

**Modelo para el emparejador.** Hay 1.748 pares verdaderos gratis (mismo EAN
entre cadenas). Riesgo conocido: que aprenda de los productos que tienen EAN
(marcas conocidas) y falle justo en marca blanca, que es lo que importa. Hay que
medirlo separando los dos casos antes de creerselo. **Y despues de la tarea 2**,
porque los grupos anchos no los arregla un modelo.

**App nativa y widget.** Hoy somos una web servida por Caddy. Un widget pide app
nativa y eso es otro proyecto.

**Mas cadenas.** QueFalta tiene 19 y nosotros 5, pero las nuestras **se comparan
entre si**. Anadir cadenas sin poder emparejarlas es cambiar lo que nos hace
utiles por una lista mas larga.

---

## 13. Lo que no se hace nunca

- **Resolver el CAPTCHA de Alcampo**, ni a mano ni automatizado.
- **Abrir un puerto en el router.** Hay un PostgreSQL detras. Tailscale, y ya.
- **Ensenar un numero sin decir de cuando es** ni sobre cuantas filas se ha
  calculado.
- **Llamar calidad a una letra que sale del precio.**
- **Restar del total un descuento que no se descuenta en caja.**
- **Escribir en `data/gold/` desde la plataforma.** Lo escribe el pipeline, se
  monta en solo lectura, y esa frontera es lo que permite arreglar una mitad sin
  tocar la otra.

---

# Lo que sigue, despues de la pasada del 17 de septiembre (tarde)

Ordenado por **valor / coste**. Los cinco primeros no necesitan red: el dato ya
esta en `data/raw`.

## A. Sin pedirle nada a ninguna web

### A1. Texto de oferta de DIA y Mercadona — 0 % hoy
Las dos saben que hay oferta (`is_promo_price`, `price_decreased`) pero no
publican **cual** en el listado. Sin el texto no se puede aplicar
`core/promos.py`, que es lo que convierte "2ª unidad -50 %" en un precio real.

**Pasos**: (1) leer 200 fichas de DIA y 200 de Mercadona con el localizador de
`rehacer_maestro.py`; (2) contar cuantas traen texto de promocion y con que
clave; (3) si aparece, anadirlo a `_maestro_de_ficha` y a `a_registro`; (4)
medir cuantas de esas frases entiende `promos.lee()`.
**Valor**: hoy el 13 % del catalogo tiene texto de oferta y son solo Alcampo y
Carrefour. Con DIA y Mercadona pasaria de 6.800 a ~12.000.

### A2. Conservacion de DIA — 0 % hoy
`item_treatment_type` esta en las 5.410 fichas guardadas y no se lee. El filtro
"congelado" hoy no cubre DIA.
**Pasos**: contar los valores distintos, traducirlos en `core/sellos.py`
(`_CONSERVACION`), cablear, medir.

### A3. Categoria estructurada de DIA
`family_code`, `subfamily_code`, `section_code` en el 100 % de las fichas. Hoy la
seccion de DIA se deduce de su URL (`core/secciones.py`). Un arbol de verdad es
mejor que dos trozos de URL, y ademas permite comprobar `secciones.yml` contra
algo que no sea nuestra propia adivinanza.

### A4. `isRecall` de Aldi
Booleano en los 2.065 productos, hoy `false` en todos. **Ninguna app de la
competencia avisa de retiradas de producto**, y nosotros sabemos que hay en cada
lista. Pasarlo a bronze cuesta una linea; cuando deje de ser cero, ya habra donde
engancharlo.
Fuente externa complementaria: las alertas de AESAN, que son publicas.

### A5. `main_feature` y `badges` de Mercadona
`main_feature` (58 %) dice "ultracongelado", "lonchas", "antitranspirante": es
`tipo_producto` gratis para 2.500 productos. `badges.requires_age_check` marca
los que llevan alcohol.

## B. Con red, en orden de valor

### B1. Fichas de Alcampo y Carrefour — el agujero grande
77 % del catalogo sin **nada** de composicion. Es la razon de que la letra de
calidad se calcule ordenando por precio en el 77 % de los casos.
`projects/cesta/sondear_fichas.py` existe y **no se ha ejecutado nunca**.
Ver `docs/PARIDAD-CAMPOS.md`, punto 3.1, y `docs/PATCHRIGHT.md` para el WAF de
Alcampo.

### B2. Origen en Carrefour y Alcampo
Aldi enseno que el origen puede estar donde no se busca: en un logotipo y dentro
de una descripcion. Merece una pasada especifica sobre el crudo de las otras dos
antes de volver a decir que el filtro "producto espanol" es imposible.

## C. Lo que ya estaba pendiente y sigue

1. **Los grupos son demasiado anchos** (F2). Sigue siendo el bloqueo numero uno:
   el grupo del agua junta Perrier (2,40 EUR/l) con marca propia (0,28) **con los
   formatos leidos bien**. Bloquea el panel y el "mejor y mas barato".
   Ahora hay dos senales nuevas que no habia: `tipo_producto` (DIA, 5.410) y
   `envase` (8.829). Dos productos con envase distinto casi nunca son el mismo.
2. **No esta en git.** Decision de David, pero cada pasada como la de hoy toca 20
   ficheros y no hay forma de ver el diff ni de volver atras.
3. **La plataforma nunca se ha levantado con Docker.** Solo piezas sueltas.
4. **HTTPS para el escaner** (`tailscale cert`) sin verificar. Bloquea F5.

## D. Reglas que han salido de esta pasada y conviene no perder

1. **Antes de pedirle un campo nuevo a una web, buscarlo en `data/raw`.** Ha
   aparecido ahi las siete veces que se ha mirado.
2. **Un dato que no cruza la frontera de gold no existe.** Al anadir una columna
   al contrato, anadirla en el mismo commit a `emparejar.COLUMNAS` y a
   `docs/PARIDAD-CAMPOS.md`.
3. **Un centinela no es una fecha ni un numero.** 2030-12-31 en Aldi, 999 dias en
   DIA. Al leer un campo nuevo, mirar primero los valores mas repetidos.
4. **Un campo que se llama X no siempre es X.** `drained_weight` de DIA es el peso
   neto. Comprobarlo contra otra columna antes de creerselo.
5. **El texto se filtra por grupo; un atributo, por producto.**
6. **Cada valor viaja con su procedencia.** `calidad_origen`,
   `proc_precio_unidad` y ahora `sellos_origen`.

---

# Lo siguiente, tras la tercera pasada del 17 de septiembre

La seccion anterior sigue valiendo. Esto es lo que ha cambiado de sitio y lo
nuevo, con las especificaciones desglosadas para que se pueda hacer de una
sentada cada cosa.

## Ya hecho de la lista anterior

- ~~A1. Texto de oferta de DIA~~ → 221 productos, y 200 marcados `promo_club`.
- ~~A4. `isRecall` de Aldi~~ → columna `es_recall`, aviso en rojo en la ficha.
- Y ademas, sin estar en la lista: la fecha de fin de las ofertas de Alcampo
  (1.904), el peso al peso de Alcampo (742), el peso escurrido de Mercadona
  (179), los pictogramas de peligro (450), el distintivo de DIA (550) y el
  filtro "sin alcohol" (3.316).

## N1. El numero real de unidades de un pack — Mercadona, 1.320 productos

**Alto nivel**: hoy, cuando una cadena dice "1 ud" y su precio por unidad
sugiere que el envase trae mas piezas, lo deducimos dividiendo
(`unidades_inferidas`). Mercadona publica el numero exacto en
`price_instructions.total_units`, y el tamano de cada pieza en `pack_size`.

**Desglose**:

1. Medir sobre el crudo cuantos de los 1.320 tienen ademas `pack_size`, y
   comparar `total_units` con el `unidades_inferidas` que calculamos hoy: cuantos
   coinciden, cuantos no, y en los que no, quien acierta. **Sin esta medicion no
   se toca nada**: es la unica forma de saber si el heuristico es bueno.
2. Anadir `unidades_envase` (Int32) al contrato solo si el paso 1 dice que el
   heuristico falla en mas del 5 %.
3. Cablearlo en `mercadona.a_registro`.
4. En `pipeline.a_silver`, dar prioridad a lo declarado sobre lo deducido, y
   dejar `unidades_inferidas` como respaldo. Ojo al orden: `unidades_inferidas`
   ya interactua con la regla de "precios en disputa" (ver
   `docs/PRECIO-POR-UNIDAD.md`, punto 3.1).
5. Prueba: un pack de 6 yogures de 125 g debe dar 6 unidades y 0,75 kg, y el
   precio por kilo tiene que cuadrar con el de la etiqueta de Mercadona.

**Criterio de aceptacion**: el numero de filas "en disputa" no sube, y al menos
1.000 productos pasan de unidades deducidas a unidades declaradas.

## N2. La conservacion de DIA — hoy 0 %

**Alto nivel**: `item_treatment_type` esta en las 5.410 fichas guardadas y no se
lee. El filtro "congelado" hoy no cubre DIA, que es el 10 % del catalogo.

**Desglose**:

1. `uv run python -m projects.cesta.auditar_crudo --fuente dia --minimo 0.5` y
   buscar el campo en la salida; si no aparece, es que esta en la ficha maestra y
   no en el listado: mirarlo con el localizador de `rehacer_maestro.py`.
2. Contar los valores distintos y cuantos productos tiene cada uno.
3. Traducirlos en `core/sellos._CONSERVACION`, que es donde vive el vocabulario.
4. Cablear en `_maestro_de_ficha` (guardando **la palabra de DIA**, no la
   nuestra: ver la regla de `data/master` en `docs/OPERACION.md`) y normalizar en
   `a_registro`.
5. `rehacer_maestro --fuente dia` + `reprocesar --fuente dia` y medir.

**Criterio de aceptacion**: `conservacion` de DIA pasa de 0 a mas de 1.500, y el
filtro "congelado" devuelve congelados de DIA.

## N3. El arbol de categorias de DIA — 5.410 productos

**Alto nivel**: hoy la seccion de DIA se deduce de dos trozos de su URL
(`core/secciones.py`). Su ficha trae `section_code`, `family_code` y
`subfamily_code` en el 100 %: un arbol de verdad.

**Desglose**:

1. Sacar el arbol completo (codigo → cuantos productos) de las fichas guardadas.
2. Cruzarlo con lo que hoy adivina `secciones.clave_de("dia", url)`: cuantos
   coinciden y cuantos no. **Esto es lo valioso**: es la primera vez que se puede
   comprobar `secciones.yml` contra algo que no sea nuestra propia adivinanza.
3. Si el arbol es mejor, anadir `seccion_cadena` al contrato y usarlo como clave
   preferente en `secciones.seccion_de`.
4. Volver a medir la cobertura de secciones (hoy 99,9 %) y los productos mal
   clasificados.

**Criterio de aceptacion**: se publica el numero de discrepancias entre el arbol
de DIA y `secciones.yml`, y se corrige el fichero donde el arbol tenga razon.

## N4. El "2ª unidad" estructurado de Alcampo — 509 productos

`promotions[].requiredProductQuantity` da el N sin leer el texto. Hoy
`core/promos.py` lo saca con una expresion regular y acierta el 69 % de los
textos de Alcampo. Usar el campo cuando exista es gratis y elimina una
adivinanza.

**Desglose**: (1) comparar el N del campo con el `a` que deduce `promos.lee()` en
esos 509; (2) si no coinciden, ver quien acierta mirando el precio; (3) si el
campo gana, pasarlo a `a_registro` y que `promos.lee()` lo acepte como pista.

## N5. Las fichas de Alcampo y Carrefour — sigue siendo el agujero grande

77 % del catalogo sin **nada** de composicion, y es la razon de que la letra de
calidad se calcule ordenando por precio en el 77 % de los casos.
`projects/cesta/sondear_fichas.py` existe y **no se ha ejecutado nunca**, porque
ninguna de las sesiones que han escrito este codigo tiene red hacia esos
dominios. Es la primera tarea de quien si la tenga.

## N6. Una sexta cadena

Estudiado y aparcado, con el motivo:

| cadena | tamano | por que no, hoy |
|---|---|---|
| **Lidl** | ~650 tiendas | investigado y descartado: no publica precios por internet en Espana. Ver `docs/LIDL.md` |
| **Eroski** | ~1.600 | **la mejor candidata**. Tiene tienda online con precios. No se ha podido sondear: ninguna sesion ha tenido red hacia `eroski.es` |
| **Consum** | ~800 | tienda online propia, fuerte en Levante. Mismo problema de red |
| **BonÀrea** | ~500 | catalogo propio, muy integrado. Sin sondear |

**Antes de escribir una linea de colector nuevo**: `sondear_fichas.py` contra la
cadena, medir que campos publica y rellenar su fila en
`docs/PARIDAD-CAMPOS.md`. Una cadena que no publique precio por unidad ni
formato no suma; suma ruido en los grupos.

## N7. Los grupos demasiado anchos (F2) — sigue siendo el bloqueo numero uno

Y ahora se sabe algo mas: **el envase no sirve para separarlos**. De los 980
enlaces donde las dos cadenas publican envase, 372 (38 %) no coinciden, y son el
mismo producto con distinta palabra. `tipo_producto` tampoco, todavia: solo lo
publica DIA, asi que hay cero enlaces con el dato en las dos puntas.

Lo que si hay nuevo para intentarlo: `peso_neto_g` (5.436 productos) permite
comparar un producto vendido por volumen con otro vendido por peso, que hoy
caen en grupos distintos.

## Reglas nuevas de esta pasada

7. **Ejecuta `auditar_crudo.py` antes de pedirle un campo nuevo a una web.** Ha
   acertado las ocho veces.
8. **`\b` no delimita numeros pegados a puntuacion.** Usa `(?<!\d)` y `(?!\d)`.
   Ha fallado dos veces el mismo dia: con `€` y con `_`.
9. **Un patron de texto se escribe con limites de palabra o no se escribe.**
   "eco" dentro de "seco", "champ" dentro de "champu". Dos veces el mismo dia.
10. **Un filtro de exclusion y uno de inclusion se afinan al contrario.** En "sin
    gluten" (incluir) pasarse es peligroso; en "sin alcohol" (excluir) quedarse
    corto es lo peligroso. Ver `core/alcohol.py`.
11. **Medir y descartar tambien es un resultado, y se escribe con su numero.**
    Las valoraciones de Alcampo (1.260 votos en total) y el texto largo de
    Carrefour (no rescata ninguna oferta) estan documentados para que nadie
    repita el trabajo.

---

# Lo siguiente, tras la revision de la ingesta del 18 de septiembre

## Hecho hoy

- ~~N1. Unidades reales de los packs de Mercadona~~ → 1.087 productos. Medido
  antes de tocar nada, como pedia la especificacion: de los 1.256 con
  `total_units`, nuestra deduccion **acertaba 169 y fallaba 1.087**. La ficha
  dice ya "6 × 125 g · 0,42 € cada una".
- `core/cobertura.py`, el control que faltaba: ¿falta media tienda?
- Reintentos y rescate en Carrefour; `precio_comparable` llega a gold; cupo de
  fichas de DIA adaptativo; `core/comparacion.py` con la frontera compartida.

## N8. El boton "esto no es lo mismo" — la idea que mas vale de la competencia

**Alto nivel.** Los grupos demasiado anchos son el bloqueo numero uno y llevamos
tres intentos de arreglarlo desde el algoritmo. Soysuper lo resuelve por otro
lado: deja que la persona rechace un equivalente. Cada rechazo es informacion que
no se puede sacar de ningun dato de la cadena.

**Desglose.**

1. Tabla en PostgreSQL: `par_rechazado(producto_a, producto_b, quien, cuando)`,
   con los dos ids en el orden canonico (el menor primero) para que no haya
   duplicados cruzados.
2. `DELETE`/`POST /api/grupo/{id}/no-es-lo-mismo` con los dos `producto_id`.
   Requiere sesion: un rechazo anonimo no se puede deshacer ni auditar.
3. En la ficha del grupo, junto a cada producto que **no** sea el que se esta
   mirando: un enlace pequeno "no es lo mismo". Nada de iconos: hay que leerlo.
4. El emparejador exporta los rechazos a `data/gold/rechazos.parquet` antes de
   correr y `core/matching.enlaces()` los descarta al emitir. **Ojo**: los
   rechazos son pares de `(fuente, id_fuente)`, no de posiciones, porque las
   posiciones cambian cada dia.
5. Prueba: rechazar un par y comprobar que al dia siguiente el grupo se parte.

**Criterio de aceptacion.** Un rechazo sobrevive a un ciclo completo de pipeline
y emparejador, y el producto rechazado deja de aparecer en el grupo.

**Cuidado.** Un rechazo parte el grupo, pero el union-find los puede volver a
unir por un tercer producto (A–B rechazado, pero A–C y C–B siguen). Hay que
decidir y escribir que se hace: lo honesto es que el rechazo pese sobre el grupo
entero, no solo sobre ese par.

## N9. "Lo de siempre"

Soysuper aprende los productos habituales. Nosotros tenemos las listas y quien
anadio que: una consulta de quince lineas sobre `lista_linea` da los productos que
aparecen en mas de la mitad de las compras del ultimo mes. Pantalla: un boton
"anadir lo de siempre" en una lista vacia.

## N10. Avisos de retirada de producto, con AESAN

**Alto nivel.** El 17 de septiembre se construyo la columna `es_recall` y el aviso
rojo de la ficha, y hoy solo puede alimentarlos Aldi, que lo tiene a cero. AESAN
publica las retiradas oficiales de toda Espana. Con esa fuente, el aviso cubre las
cinco cadenas y pasa a ser **lo unico de la lista que ninguna app tiene**.

**Desglose.**

1. Colector nuevo, `projects/cesta/collectors/aesan.py`. Una pagina al dia. El
   listado esta en `aesan.gob.es/.../alertas_alimentarias/`, con una referencia
   estable por alerta (`ES2026/067`) y una URL por alerta. **No hay RSS ni API**:
   es HTML, que es lo que este proyecto ya sabe tratar.
2. Guardar en `data/raw/fuente=aesan/` como todo lo demas, y en
   `data/gold/alertas.parquet`: referencia, fecha, producto, marca, lote, motivo.
3. Emparejar con el catalogo por marca + nombre, con el umbral **alto**: un falso
   positivo aqui asusta a alguien sin motivo, y un falso negativo lo deja sin
   avisar. Escribir cual de los dos errores se prefiere **antes** de elegir el
   umbral (aqui, al contrario que en el alcohol, los dos son malos: hay que ser
   conservador y ensenar la alerta con el texto de AESAN al lado, para que la
   persona juzgue).
4. En la lista de la compra, banda roja arriba si algo de la lista casa con una
   alerta viva. En la ficha, el aviso que ya existe.
5. Caducar las alertas: AESAN no las retira, asi que hay que decidir cuanto dura
   viva una (tres meses es razonable) y escribirlo.

**Criterio de aceptacion.** Una alerta real de las ultimas semanas aparece
enganchada al producto correcto del catalogo, y ninguna alerta engancha con un
producto que no es.

## N11. Eroski y Consum — CERRADO el 19: Eroski se lee entera (ver docs/EROSKI.md)

Comprobadas las dos, y salen distinto: **Eroski se puede leer** y Consum no, por
una razon que no tiene nada que ver con reto alguno.

- **Eroski**: **RESUELTA.** Se lee entera con un cliente HTTP normal: ni
  navegador, ni reto, ni zona AJAX. La categoria hoja trae los productos
  servidos por el servidor con el precio dentro de un `data-metrics` de GA4
  (precio, id, nombre, marca y la categoria en tres niveles), el precio por kilo
  en texto ("1 KILO A 1,95 €") y las **valoraciones de clientes**, que no publica
  ninguna de nuestras cinco cadenas. El menu da **1.593 categorias de una sola
  peticion**: el recorrido esta resuelto antes de empezar.

  No publica **codigo de barras** en el listado ni JSON-LD. Queda por sondear la
  ficha (`/es/productdetail/<id>-<slug>/`), que es lo unico que falta.

  **Lo que decide si entra no es nada de eso**: es cuantos grupos comparables
  nuevos salen al pasar sus productos por el emparejador. Sin EAN hay que
  emparejar por nombre y formato. Bajar 20 categorias hoja, emparejarlas contra
  el catalogo actual y **contar**. Si anade catalogo y no anade comparaciones, no
  compensa.

  Detalle, y las cuatro veces que el sondeo dio un falso veredicto, en
  `docs/EROSKI.md`.

- **Consum**: la ficha de producto es una SPA -- `tienda.consum.es/es/p/<slug>/<id>`
  devuelve un *spinner* y nada mas --, asi que el unico camino al dato es su API.
  Y su `robots.txt` dice literalmente **`Disallow: /api/`**. El unico camino es el
  que el sitio prohibe. Cerrado.

Que otros lo hagan no lo reabre: `github.com/seravifer/supermarket-tracker` baja
Consum, y eso confirma que el dato esta ahi, no que nos toque cogerlo.

**La sexta cadena, si la hay, es Ahorramas** — ver N15.

## N15. Ahorramas — la unica candidata que ha pasado el filtro

Comprobado el 18 de septiembre, desde fuera:

    robots.txt     permisivo para categorias y fichas; prohibe carrito, login,
                   busqueda y `*ver-todo*`. Declara sitemap_index.xml
    sitemaps       sitemap_0-product.xml y sitemap_2-category.xml,
                   actualizados el 16 de septiembre
    fichas         URL limpia: /miel-de-flores-mel-da-anta-800g-47.html
    plataforma     Salesforce Commerce Cloud (el robots.txt menciona demandware)

Tres preguntas, en este orden, y **ninguna necesita escribir un colector**:

1. `GET` de una categoria con un cliente HTTP normal. ¿Viene el precio en el HTML?
   Buscar `€`, `data-product`, `application/ld+json`.
2. Si no: ver que peticion trae la rejilla. En SFCC suele ser
   `.../Search-UpdateGrid?cgid=<categoria>&start=0&sz=24`. Comprobarla contra el
   `robots.txt`, que hoy **no la prohibe**.
3. Si el precio esta: contar productos y comprobar que hay **precio por unidad**.
   Sin eso entra en el catalogo pero no en la comparacion.

Y la pregunta que decide de verdad, antes de la primera linea de colector:
**¿cuantos de sus productos emparejarian con los que ya tenemos?** Cruzar sus EAN
-- si los publica -- contra nuestros 25.094 productos con codigo de barras. Una
cadena que anade 8.000 productos y 30 grupos comparables no anade nada. La
competencia lo demuestra: RadarSuper cubre siete cadenas y ensena **177**
referencias comparables.

## N12. Open Prices: leer si, mezclar no

`https://prices.openfoodfacts.org`, API REST con busqueda por codigo de barras.
**Licencia ODbL, share-alike**: mezclarla con `data/gold` obliga a publicar la
base combinada como datos abiertos el dia que esto salga de casa. Para contrastar
un precio suelto vale; para meterla en el pipeline hay que decidirlo a proposito.
Y para Espana esta casi vacia.

## Reglas nuevas del 18 de septiembre

12. **Una ejecucion sin errores no es una ejecucion correcta.** "Cero errores"
    significa que nadie fallo, no que este todo.
13. **Un control de calidad de una captura tiene que mirar la FORMA del
    catalogo, no solo su tamano.** Un total puede bajar un 13 % por mil razones;
    una rama que se queda en el 3 % de lo que tenia, no.
14. **Un 403 no es un "no" definitivo.** Es "ahora no". Reintentar y volver mas
    tarde recupero el 91 % de lo que Carrefour perdio.
15. **Un dato derivado mas nuevo que su origen es un dato huerfano, y manda.**
    El silver del 18 sobrevivio a su bronze y volvio a colar el catalogo roto.
16. **La misma regla escrita en dos sitios acaba siendo dos reglas distintas.**
    "Diferencia imposible" eran 3 veces en el resumen y 30 en la interfaz.

---

# Datos de las cadenas que todavia no pedimos (18 de septiembre, tarde)

Hasta ahora se auditaba **que campos** no leiamos de las respuestas que ya
bajabamos (`auditar_crudo.py`). Falta la otra mitad: **que respuestas no pedimos
nunca**. Dos hallazgos, uno ya arreglado y otro por investigar.

## Arreglado hoy: 32 categorias de Alcampo que no llegaban por ningun camino

`auditar_recorrido.py` y el arreglo del nodo de navegacion vacio. Ver
`docs/AUDITAR-RECORRIDO.md`. Son, entre otras, "Lacteos sin lactosa", "Sin Gluten
/ Sin Lactosa", "Arroz Ecologico", "Pollo Ecologico", "Sobrasada", "Ron Premium".

## N13. Endpoints que aparecen en el crudo y no pedimos nunca

Buscando rutas de API **dentro de las respuestas que ya tenemos guardadas**,
salen estos. Ninguno esta probado: ninguna de las sesiones que han escrito este
codigo tiene red hacia esos dominios, asi que lo que sigue es una lista de sitios
donde mirar, no una promesa.

### Carrefour — tiene un buscador con API propia

    /search-api/query/v1/search
    /search-api/suggestions/v1/empathize
    /search-api/suggestions/v1/nextqueries
    /search-api/suggestions/v1/relatedtags

Hoy Carrefour se recorre por categorias desde su sitemap: 653 peticiones que
Cloudflare puede cortar, y esta manana corto 373. **Un buscador es un segundo
camino al mismo catalogo**, y sobre todo un camino de rescate: las categorias que
dan 403 se podrian intentar por termino de busqueda.

Alcampo ya usa esa idea para otra cosa (completar las categorias que tocan el
tope de 300 con 600 terminos de busqueda al dia), asi que el patron esta escrito
y probado en `alcampo.py`.

**Desglose**: (1) pedir a mano una busqueda y ver que devuelve y con que forma;
(2) medir cuantos productos distintos da una lista de 200 terminos frente a los
16.416 del recorrido por categorias; (3) si cubre bien, usarlo **solo como
rescate**, no como camino principal: un buscador nunca garantiza el catalogo
entero.

### DIA — buscador, tiendas y folletos

    /search-back-api-service-v1        el buscador
    /plp-back-api-service-v1           el listado, que ya usamos por otra puerta
    /tiendas  /tiendas/buscador-tiendas-folletos

Lo de **folletos** es lo interesante: son las ofertas de la semana, y hoy solo
tenemos 221 textos de oferta de DIA (el 4 % de su catalogo). Un folleto trae
ofertas que no siempre estan marcadas en el listado.

Y `/tiendas` abre una puerta que no tenemos: **que tiendas hay y donde**. Hoy la
app no sabe si tienes un DIA cerca; la preferencia "cadenas cerca" se rellena a
mano. Con las coordenadas de las tiendas se podria proponer.

### Mercadona — 2 categorias sueltas

"Jamon serrano" y "Perfume y colonia mujer" el 18, 1 el 17. Es ruido de un arbol
que cambia, no un agujero. No hay nada que arreglar.

### Lo que NO se va a usar, dicho a proposito

    /cloud-api/carts-api-form/v1/carts/...     el carrito de Carrefour

Aparece en su crudo y no se toca. Esta aplicacion lee precios; no mete nada en el
carrito de nadie ni simula ser un cliente comprando. Anotado aqui para que quede
claro que se vio y se descarto.

## N14. Lo que sigue sin poder mirarse

Eroski y Consum, y las fichas de producto de Alcampo y Carrefour (el 77 % del
catalogo sin composicion). Las tres cosas necesitan red hacia esos dominios, que
ninguna sesion ha tenido. Es la primera tarea de quien la tenga.

---

# Lo nuevo de la tarde del 18 de septiembre

## N16. Las 199 ofertas de Aldi que todavia no han empezado — LA GRANDE

`promotionPrices` trae, en **317 de los 2.175 productos de Aldi (14,6 %)**, la
oferta completa: `validFromLocalDate`, `validUntilLocalDate`, `priceValue`,
`strikePrice.strikePriceValue` y `priceTagLabels.promoText1`. Y de esas 317,
**199 empiezan mas adelante**:

    Vino tinto crianza DOCa Rioja   6,99 -> 3,99   -42 %   del 19 al 22
    Pack de 2 vinos blancos        14,99 -> 11,99  -20 %   del 19 al 22
    Leche omega 3                   1,89 ->  1,69  -10 %   del 21 al 27

El colector **las ve y las tira**: hay un comentario en `aldi.py` que lo dice
("62 de las 174 promociones de hoy aun no han empezado") y solo las usa para
fijar el `validUntil` del precio de hoy.

Ninguna de las aplicaciones estudiadas hace esto. Todas contestan "cuanto cuesta
hoy" o "cuanto costaba antes". Esto contesta **"no lo compres hoy: el sabado baja
un 42 %"**, que es la pregunta que de verdad ahorra dinero. Y no es una
prediccion: es la cadena publicando su calendario.

**Desglose**: (1) cinco columnas nuevas `promo_futura_desde|hasta|cent|antes_cent|
origen`, de bronze a gold; (2) seleccion: de las entradas con `validFromLocalDate
> hoy`, la mas proxima, y a igualdad de dia la mas barata; (3) **jamas** meter ese
precio en `precio_cent` ni en la serie historica, que es el error facil; (4) aviso
en la linea de la lista y pantalla "espera unos dias" ordenada por lo que se
ahorra en esa lista; (5) decir siempre de donde sale, y dejar de ensenarlo cuando
la ventana pasa aunque no haya captura nueva; (6) prueba: una promocion con
`validFrom` en el pasado no puede acabar en `promo_futura_*`.

## N17. `solo_online`: descuentos que no existen si vas a la tienda

No anade una funcionalidad: **corrige un total que hoy esta mal**.

    Carrefour  badge.description con "Exclusivo online"      76 (46 + 30)
    DIA        headband_promotion = exclusive_online        106
    DIA        promotions[].exclusive_online                 ~100

Hoy esos descuentos entran en el total de la cesta como si fueran reales. Un
campo `solo_online` y la regla de siempre: se ensena, no se resta, y la
comparacion entre cadenas se puede hacer con y sin el.

Es el hermano del caso de la tarjeta de fidelizacion, y **Alcampo lo dice ya con
`promotions[].type = LOYALTY` en 534 productos** (hoy se deduce del texto).

## N18. `badge.description` de Carrefour — 2.024 productos

La regla de la oferta escrita en espanol, en el **17,4 %** del catalogo:

    2.711  Compra 2 unidades y te descontamos el 50 % en la 2ª ud
      800  Compra 2 unidades, Ahorra la segunda
      307  Compra 12 unidades de leche ... PASCUAL brik 1 l
      105  Compra 3 unidades y paga solo 2
       52  Compra 4 unidades y paga solo 3
       46  Te descontamos 5 € por la compra de 18 €

Los dos ultimos son la trampa: **no son reglas de producto, son reglas de cesta**
(por marca y por importe). Si se aplican producto a producto, el total sale mal.
Mientras no haya modelo de cesta, se guardan y se ensenan como texto y **no se
restan**. Tambien sin leer: `strikethrough_price`, el precio anterior real, en 190
productos.

## N19. `main_feature` de Mercadona — municion para F2

**1.209 productos (26,4 %)** con el descriptor de variante: *"Yogur griego dulce
Hacendado"* -> *"con dulce de leche, galleta y platano"*. Entra por **N7, los
grupos demasiado anchos**, no por la ficha: dos productos de la misma cadena con
`variante` distinta no son el mismo producto. Entre cadenas no vale como negativa
(las demas no publican el campo).

## N20. Cruces de calidad: los que no dan datos, dan desacuerdos

    DIA  prices.discount_percentage != 0     161 productos
    DIA  prices.is_club_price = True         130 productos

No hay que copiarlos. Hay que **compararlos con lo nuestro**: si nuestro descuento
calculado y el suyo no coinciden, uno de los dos lee mal el formato; si un
producto dice `is_club_price` y nuestro `promo_club` esta vacio, se nos ha
escapado. Un desacuerdo entre dos fuentes es lo unico que encuentra errores que
ninguna de las dos declara.

Los `stamp_code` de DIA (1, 2, 3 y 4, en 1.096 productos) **no se tocan** hasta
cruzarlos con el texto de la promocion de esos mismos productos y comprobar que
cada codigo cae siempre en el mismo tipo de oferta. Un codigo mal interpretado es
peor que un codigo sin leer.

## N21. La extension de navegador con la curva de precios

Idea tomada de `supermarket-tracker`: ensenar el historico **dentro de la web del
supermercado**, mientras compras. Es la unica forma de que trece dias de serie
sirvan en el momento de decidir, y para nosotros es **un cliente mas de la API que
ya existe**, no una pieza nueva de datos.

## N22. Pantalla "bajadas de esta semana" y "verificador de ofertas"

Las dos salen de la competencia (Precios del Super y PrecioReal) y las dos las
podemos hacer mejor porque el calculo ya esta hecho:

- **bajadas**: ellos comparan con la captura anterior; nosotros tenemos trece dias
  de serie y el `FACTOR_INCREIBLE` para no confundir una bajada con un formato mal
  leido.
- **verificador**: la regla `dudoso` ya esta calculada y hoy es solo un campo.
  Merece pantalla propia: *"esta oferta no lo es"*.

## Reglas nuevas de la tarde del 18 de septiembre

- Un control que aprueba cuando no tiene con que comparar es peor que no tenerlo:
  se confia en el.
- Una comprobacion se escribe donde todavia tiene arreglo barato.
- Arreglar el dato de ayer puede cegar el control de manana. Antes de restaurar
  algo, mirar contra que se compara.
- **Bronze no se borra nunca. Si no esta en su sitio, es que lo apartaron.**
- **Las cadenas se suman; el emparejamiento se gana.** Un comparador con siete
  cadenas ensena 177 referencias comparables; nosotros con cinco ensenamos 6.448.
- **Antes de medir un campo "nuevo", mirar si ya se lee un hermano suyo.**


---

# Lo del 19 de septiembre por la tarde: la auditoria de FICHAS

Hasta hoy se habia auditado el crudo de los **listados** y nunca el de las
**fichas de producto**, que es donde esta lo bueno. Detalle en `docs/FICHAS.md`.

## HECHO hoy

- **`conservacion` de DIA: 0 % -> 34 %.** `storage_instructions` estaba en el
  44 % de las fichas y `sellos.conservacion_de_prosa` ya sabia leerlo desde que
  se escribio para Mercadona. Cierra **N2**.
- **`origen` de DIA: 0 % -> 69 %**, de `manufacturer_contact_country` (29 %) y
  `manufacturer_name` (41 %). La direccion postal no se usa: un domicilio social
  no es un origen.
- **`solo_online`**, la marca que faltaba (era N17): 397 promociones de Alcampo
  lo dicen en su texto y entraban en el total de la cesta como si fueran a bajar
  el ticket de la tienda. Ahora `Mecanica.util` las excluye igual que a las de
  tarjeta, y la busqueda por ofertas tampoco las cuenta.
- **Carrefour: las categorias difuntas ya no se repaginan.** Una categoria que ya
  no existe no da 404: sirve **el catalogo de su padre**, con su paginacion
  entera. Medido sobre el crudo del 19: **531 de 2.634 paginas, el 20 % de todo
  lo que se pidio ese dia**. El caso gordo, `cat20001`: 462 paginas servidas para
  1.008 productos. Se detecta por `navigation_id` y se corta.
- **Carrefour: un cuerpo cortado ya no envenena el rescate.** Una pagina llego con
  220.978 de sus ~468.000 caracteres, el objeto de JavaScript no cerraba, y el
  cuerpo malo **se habia guardado en el crudo del dia**: las tres vueltas de
  rescate lo releyeron de disco y fallaron igual, sin tocar la red. Ahora, si el
  parseo no traga, se vuelve a pedir saltandose la cache.

## N23. El arbol de categorias de DIA, en palabras (sustituye a N3)

`category_description`, `family_description` y `section_description` vienen en el
**100 %** de las fichas: "SECO", "INFUSIONES", "ALM DULCE Y LECHE". Es el arbol
que faltaba, y no hay que pedir nada nuevo: ya esta en el maestro.

## N24. Los "free" de DIA, con cuidado

`gluten_free`, `lactose_free`, `nuts_free`, `salt_free`, `caffeine_free`, `bio`,
entre el 15 % y el 72 % de las fichas. **Trampa**: el valor es "SI", "NO" o
**"No Aplica"**, y "No Aplica" es el 72 % de los `gluten_free`. Solo un "SI"
explicito cuenta. Es la asimetria de siempre: en un filtro de inclusion como "sin
gluten", pasarse marcando es peligroso.

## N25. `stamp_description` desbloquea los `stamp_code`

En la auditoria de listados del 18 quedaron 1.096 productos de DIA con
`stamp_code` 1, 2, 3 o 4 y la nota "no se tocan hasta saber que significan". La
ficha trae `stamp_description` ("Air Fryer"). Cruzando los dos se sabe.

## N26. Codigos de barras secundarios: guardados, sin usar

`secondary_eans` en el 22 % de las fichas de DIA (187 en 460). Se capturan y
**no se usan para emparejar**, a proposito: entre ellos esta el codigo del
**pack**, y emparejar por ahi haria que un pack de seis y una unidad suelta
fueran el mismo producto. Para usarlos hay que saber cual es cual, y la ficha no
lo dice.

## N27. Lo que queda en la ficha de DIA

`drained_weight` (100 %), `item_vat_code` (100 %), `net_contents` (48 %),
`manufacturer_warnings` (22 %), `serving_size` (17 %), `alcohol_content` (7 %),
`nutritional_claim` (5 %), `health_claim` (3 %), `nutri_score` propio (2 %),
`hazard_info` con codigos CLP estructurados (2 %), y micronutrientes (1-2 %).

## N28. Mercadona: `extra_info`

100 % de las 11 fichas del crudo de hoy: `['Nota olfativa floral']`. Muestra
corta -- el maestro es incremental y el crudo viejo se limpia --, pero es un
descriptor mas, hermano de `main_feature` (N19).
