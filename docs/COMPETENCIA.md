# Cesta — que hacen las otras apps, y que nos llevamos

Estudio del 17 de septiembre de 2026. Nueve apps de cinco categorias distintas.
Al final, lo que nos llevamos, lo que descartamos, y por que.

Todo numero de este documento esta medido contra nuestros datos. Si al ejecutar
algo el numero no sale, es que ha cambiado: hay que volver a medir.

---

## 1. Listas de la compra compartidas

### QueFalta (quefalta.es) — la espanola

La mas parecida a lo que queremos y la mejor hecha de su categoria.

    grupos            "para tu pareja, familia o companeros de piso", con varios
                      carritos y uno activo que se elige
    amigos            se encuentran por @usuario; tambien invitacion por enlace
    miembros          con avatar y papel
    catalogo          19 supermercados con productos reales, fotos y precios
                      "Categorias claras y ordenadas"
    ficha             ingredientes, alergenos, **proveedor y origen**,
                      **conservacion**, informacion nutricional
    la cesta          "Por recoger" frente a "En el carrito"
                      "Total estimado en vivo"
                      **"Ordenada por las categorias del supermercado"**
    avisos            push cuando alguien anade, cuando te meten en un grupo,
                      cuando te mandan solicitud de amistad
    ajustes           supermercados favoritos, claro/oscuro, 7 colores de acento,
                      castellano y catalan
    negocio           gratis y sin anuncios; "QueFalta Plus" opcional, y Lidl
                      solo con Plus

Y el aviso que se pone ella misma, que hay que copiar tal cual: *"Los precios son
orientativos y pueden variar"*, y *"no esta afiliada, asociada ni patrocinada por
ninguno de estos supermercados"*.

**Lo que NO hace: comparar el mismo producto entre cadenas.**

### Bring! (getbring.com) — la europea

La referencia mundial en interfaz de lista.

    anadir            **mosaico de iconos**, no solo buscador. "with tiles or as
                      a list" es una opcion de la propia app
    orden             "Sort your list however you like, for example based on the
                      aisles in your supermarket"
    urgencia          "Mark items with labels based on urgency"
    folletos          "Browse through local brochures" y **"Add offers straight
                      to your shopping list"**
    tarjetas          guarda las tarjetas de fidelizacion
    recetas           ideas semanales, guardar recetas de internet, y
                      **"Add ingredients straight to your shopping list"**
    detalle           notas y fotos por producto

### Listonic (listonic.com) — la eficiente

Donde mejor esta resuelto el "escribir menos".

    categorias        automaticas, y "Sort by aisles, A-Z, or custom order"
    voz               "Voice input - Add items hands-free"
    gestos            "Quick actions - Handy shortcuts and gestures"
    presupuesto       "Budget control - Total cost calculator"
    sugerencias       **"Personalized product suggestions - Based on shopping
                      history"**
    widget            acceso desde la pantalla de inicio
    extras            notas, fotos, 40 idiomas, modo oscuro

---

## 2. Comparadores de precio

### Soysuper / OCU — el comparador de cesta espanol

Esto es lo que hacemos nosotros, hecho por gente con mas datos.

    como va           metes la lista o buscas producto a producto, y te ensena el
                      precio de cada uno en cada cadena
    lo que suma       **incluye los gastos de envio** en la comparacion
    equivalentes      "sugerencias de productos equivalentes cuando no hay
                      coincidencia exacta"
    remate            "enviar al supermercado": la cesta se traslada a su web
    limites (suyos)   solo cadenas nacionales; el surtido online no es el de la
                      tienda fisica, sobre todo en fresco; no siempre hay
                      equivalente

**Sus limitaciones son exactamente las nuestras.** Eso es tranquilizador: no las
tenemos por hacerlo mal, las tiene el problema.

### Tiendeo / Ofertia — los folletos

    folletos          los catalogos de las tiendas de tu ciudad
    tiendas favoritas para enterarte el primero de las nuevas ofertas
    mapa              las tiendas alrededor
    y la idea buena   *"Puedes hacer la lista de la compra y al mismo tiempo ver
                      las promociones de todos los productos que estas
                      anadiendo"*

---

## 3. Escaner de codigo de barras y analisis nutricional

### Yuka (yuka.io) — la que puso de moda escanear

4 millones de productos de alimentacion y 2 de cosmetica, 1.200 nuevos al dia.

**Su formula esta publicada**, y es la parte mas util del estudio:

    60 %   calidad nutricional      metodologia Nutri-Score: azucar, sodio,
                                    grasas saturadas, calorias, proteina, fibra
                                    y contenido de fruta y verdura
    30 %   aditivos                 cada uno con un color de riesgo. Si hay uno
                                    de riesgo alto, la nota se tope en 49/100
    10 %   ecologico                bonus si lleva sello organico oficial

    extras (de pago)  modo sin conexion, buscar sin escanear, avisos de
                      aceite de palma / gluten / lactosa
    gratis            historial de lo escaneado con codigo de color
    recomendacion     "cuando un producto saca mala nota, Yuka propone
                      alternativas mejores para la salud"

### El CoCo / GoCoCo — la espanola equivalente

Mismo concepto, con Nutri-Score y NOVA, y enfocada al mercado espanol.

### Lo que dice la OCU de todas ellas — **leer esto antes de copiar nada**

La OCU analizo El CoCo, Yuka y MyRealFood y encontro tres problemas. Los tres nos
afectan directamente:

1. **Base de datos incompleta.** *"No tengamos resultados cuando escaneamos segun
   que productos"*, y los datos que faltan producen notas inexactas.
2. **Errores tecnicos.** Yuka y MyRealFood *"incluyen los aromas en este grupo y
   no es correcto"*: cuentan los aromas como aditivos.
3. **Recomendaciones cuestionables.** Al sugerir alternativas mas sanas,
   proponen productos de otra categoria en vez de comparables.

La OCU concluye que lo mejor seria que el Nutri-Score fuera obligatorio en toda
la UE, y se hizo su propio comparador basado en productos comprados de verdad.

**Como estamos nosotros en los tres puntos** (medido el 17 de septiembre):

    1. cobertura     22,6 % de nuestros productos tienen ingredientes o
                     Nutri-Score. **Escanear dara "no lo se" cuatro de cada
                     cinco veces.** Hay que disenarlo para eso, no taparlo.
    2. aromas        COMPROBADO Y LIMPIO. Nuestro regex de aditivos exige
                     "E" + tres o cuatro digitos, asi que no captura "aroma":
                     2 falsos positivos en 400 productos revisados.
    3. alternativas  **Aqui fallariamos hoy igual que Yuka**, y por la misma
                     razon: los grupos son demasiado anchos. Ver el punto 6.

---

## 4. Despensa y desperdicio

### NoWaste, KitchenPal

    inventario        listas separadas para congelador, frigorifico y despensa
    caducidad         ordenar por fecha y avisar antes de que caduque
    anadir            escaneo de codigo de barras, y reconocimiento por foto
                      de tickets y de alimentos
    mover             pasar articulos de una lista a otra
    lista             marcar como repuesto al comprar
    estadisticas      cuanta comida se tira
    familia           sincroniza entre dispositivos

**El problema conocido de esta categoria**: meter todo a mano es trabajo, y las
apps de despensa se abandonan. La version que si sale gratis esta en el punto 6.

---

## 5. Las apps de las propias cadenas

### Mi Carrefour

    ticket digital    guarda tus compras, "pasate al Papel Cero"
    lista de tienda   crear listas desde los folletos
    ChequeAhorro      en que has ahorrado
    cupones           descuentos personalizados
    **lector de precios**  "escanea con la app los productos en tienda"
    pago con QR       ensenas el QR en caja
    folletos          digitales

### Mercadona

Ticket digital (se activa por WhatsApp), lista de la compra y compra online.

**Lo que esto nos dice**: escanear un producto en la tienda con el movil **ya es
una costumbre establecida en Espana**. No hay que ensenar el gesto, solo hacerlo
bien.

---

## 6. Donde estamos nosotros, y las tres cosas que solo podemos hacer nosotros

Lo que tenemos hoy que ninguna de las nueve tiene junto:

- **El mismo producto en cinco cadenas, con precio por kilo comparable.**
  6.448 grupos. **En el 49,1 % de ellos la diferencia supera el 20 %.**
- **Donde comprar la lista entera**, en una tienda o repartida entre dos, con lo
  que le falta a cada una dicho por su nombre.
- **Las ofertas entendidas como reglas**, no como etiquetas rojas.
- **Los datos en casa.** No hay una nube con vuestra lista de la compra.

### Las tres que nadie mas puede hacer

**1. Escanear y saber si esta mas barato al lado.** Yuka te dice si es sano.
Carrefour te dice cuanto cuesta en Carrefour. Nadie te dice las dos cosas y
ademas donde esta mas barato. Medido:

    codigos de barras que reconocemos                23.312
    ... de los que podemos comparar precio            9.811   (42 %)
    ... de los que tenemos algo de nutricion         10.826   (46 %)
    ... cuyo grupo llega hasta Alcampo                7.809   (34 %)

    cobertura por cadena:  Mercadona 100 %, DIA 100 %, Carrefour 93 %,
                           Alcampo 0 %, Aldi 0 %

    Detalle que salva la funcion: el codigo de barras es **del fabricante**, no
    de la cadena. Escaneando una Coca-Cola dentro de un Alcampo, el codigo casa
    con la fila de Carrefour, y como el grupo incluye tambien la de Alcampo
    (emparejada por nombre), se puede comparar igual. Lo que no funcionara nunca
    es escanear la marca propia de Alcampo o de Aldi.

**2. "Hay uno mejor y ademas mas barato."** Es lo que Yuka intenta y la OCU le
critica, porque propone productos de otra categoria. Nosotros proponemos **dentro
del mismo grupo**, que por construccion es el mismo producto.

Medido hoy: **189 grupos** tienen un par donde uno es mejor de Nutri-Score *y*
mas barato, con un 50,6 % de diferencia mediana. Pero al mirar los ejemplos sale
el problema:

    "Patatas fritas clasicas Hacendado"  (E, 6,00 EUR/kg)
      -> propone "Patatas Golden Long McCain"  (A, 4,05 EUR/kg)

Eso son patatas fritas de bolsa contra patatas congeladas para freir. **No es el
mismo producto.** Es exactamente el error que la OCU le achaca a Yuka, y lo
cometeriamos por la misma causa: **los grupos son demasiado anchos**.

Conclusion operativa: **esta funcion esta bloqueada detras de arreglar los grupos
anchos**, y sacarla antes seria peor que no sacarla.

**3. La despensa gratis.** No pidiendo que nadie teclee un inventario, sino
deduciendola: cuando marcas algo "en el carro" y cierras la compra, ya sabemos
que lo compraste. Eso da, sin trabajo de nadie, el historial que alimenta
"sueles comprar leche cada nueve dias". Es el 20 % de una app de despensa que
aporta el 80 % del valor, sin el 80 % de escribir.

---

## 7. Lo que nos llevamos, y en que orden

### Cambia la app, y se puede hacer ya

1. **Orden por pasillos** — punto 8, es mucho mas barato de lo que pensabamos.
2. **Anadir sin escribir**: mosaico de lo habitual, voz, y mas adelante las
   sugerencias del historial.
3. **Escaner de codigo de barras** — con el aviso de cobertura bien puesto.
4. **Ver la oferta mientras anades** (la idea de Tiendeo), mejor que ellos porque
   sabemos la mecanica: no "hay promo" sino "llevando dos, 1,50 EUR menos por
   unidad".
5. **Notas por linea** (el campo ya existe) y **el aviso legal** de QueFalta.
6. **La nota de Yuka, con nuestra formula a la vista**: 60 % Nutri-Score, 30 %
   aditivos, 10 % ecologico. Es transparente, es la de referencia en el sector,
   y arregla de raiz el problema de nuestra letra actual: es **absoluta**, no una
   posicion dentro del grupo, asi que no se puede confundir con el precio.

### Despues, y en este orden

7. **"Hay uno mejor y mas barato"** — bloqueado por los grupos anchos.
8. **Historial de compra y sugerencias** — necesita meses de listas hechas.
9. **Recetas a lista** — modulo entero: guardar recetas, sacar ingredientes,
   casarlos con productos (que es el problema del emparejador otra vez).
10. **Caducidades** — solo si el historial de compra demuestra que se usa.

### No nos lo llevamos, y por que

**Amigos por @usuario.** Sois dos. Un sistema de amistades para dos personas es
burocracia.

**Varios carritos activos.** Con una lista de casa y alguna suelta basta.

**Siete colores de acento.** Es bonito y no cambia nada.

**Tarjetas de fidelizacion.** Guardar codigos de tarjeta es asumir una
responsabilidad (son datos personales, algunas dan acceso a saldo) a cambio de
ahorrarse abrir la cartera.

**Inventario de despensa a mano.** Ver el punto 6.3: la version deducida es mejor
y no cuesta trabajo a nadie.

**Pago con QR, folletos digitales, cupones.** Requieren ser la cadena.

**Escaneo de tickets por foto.** Daria el historial de compra de golpe y es
tentador. Pero es reconocimiento optico sobre papel arrugado, con un formato
distinto por cadena, y se rompe cada vez que alguien cambia el disenio del
ticket. **Si algun dia hace falta, la puerta buena es el ticket digital** que ya
dan Mercadona y Carrefour, no la foto.

**Anadir catorce cadenas mas.** QueFalta tiene 19 y nosotros 5, pero **las
nuestras se comparan entre si**. Anadir cadenas sin poder emparejarlas es cambiar
lo que nos hace utiles por una lista mas larga.

**"Enviar al supermercado"** como Soysuper. Implicaria automatizar una compra en
la web de la cadena en nombre del usuario. Ni sencillo ni limpio.

---

## 8. El hallazgo que cambia las prioridades

La pantalla de "ordenada por las categorias del supermercado" parecia bloqueada
detras de una categoria canonica, y la categoria canonica parecia un problema de
aprendizaje automatico. **No lo es.**

    cadena       claves distintas que hay que mapear
    carrefour                  269
    dia                        253
    alcampo                    202   (dos primeros niveles de su arbol)
    aldi                        99
    mercadona                   26
    ------------------------------
    TOTAL                      849

**849 filas.** Eso no es un modelo: es un fichero de equivalencias que se escribe
en una tarde, se lee de un vistazo y se corrige cuando falle. Y a diferencia de
un clasificador, no se equivoca en silencio.

**Ya esta generado**: `core/datos/secciones.yml`, 907 lineas, con el **97 %
propuesto** automaticamente por palabras clave. Quedan **25 claves** marcadas
`# <-- REPASAR`, y la propuesta ya cubre el **95,9 % de los productos**.

Ademas, el arbol de Alcampo es el mas rico (3,6 niveles de media) y **el 64,8 %
de los productos de un grupo podrian heredar la seccion del miembro de Alcampo**
sin mapear nada.

Esto desbloquea de golpe: la lista ordenada por pasillos, el "Explorar" de la
app, la pantalla de secciones del panel y el analisis por linea de producto.

---

## 9. Resumen para quien tenga prisa

**Lo mejor que hemos aprendido**, en cuatro frases:

1. La categoria canonica **no es aprendizaje automatico**: son 849 filas y el
   97 % ya esta propuesto.
2. Los **grupos demasiado anchos** bloquean mas cosas de las que parecia: la
   pantalla de secciones, el analisis por seccion, y la funcion de "hay uno mejor
   y mas barato". Es la segunda prioridad y no la quinta.
3. El **escaner** es nuestra funcion diferencial, y funciona en 23.312 codigos —
   pero fallara en la marca propia de Alcampo y Aldi, y dara "no lo se" cuatro de
   cada cinco veces en nutricion. **Hay que decirlo en pantalla.**
4. La **formula de Yuka esta publicada** y es mejor que nuestra letra actual,
   porque es absoluta en vez de relativa al grupo.

---

# Pasada del 18 de septiembre: lo nuevo

Las nueve apps de arriba siguen valiendo. Esto es lo que aparecio al volver a
mirar, y que no estaba.

## 10. Soysuper, mirado de cerca (es el que mas se parece a nosotros)

Comparador de cesta espanol, respaldado por la OCU, con **nueve cadenas**:
Mercadona, Carrefour, DIA, Alcampo, Eroski, Hipercor, El Corte Ingles, Condis y
Ahorramas. O sea, cuatro mas que nosotros, y tres de ellas (Eroski, Hipercor,
Ahorramas) son las que nos faltan.

Dos ideas suyas que **si podemos copiar y deberiamos**:

### 10.1 Dejar que la persona corrija un emparejamiento — la mejor idea del dia

Cuando Soysuper no encuentra el producto exacto en otra cadena, propone un
equivalente **y deja que el usuario lo rechace**.

Nosotros tenemos el mismo problema, mas gordo: los grupos demasiado anchos son el
bloqueo numero uno del proyecto (el grupo del agua junta Perrier a 2,40 EUR/l con
marca blanca a 0,28, con los formatos leidos bien). Y llevamos tres dias
intentando arreglarlo desde el algoritmo: con el envase (38 % de discrepancia
entre cadenas, no sirve), con el tipo de producto (solo lo publica DIA).

Un boton de **"esto no es lo mismo"** en la ficha del grupo resuelve por otro
lado: convierte cada correccion en un par negativo que el emparejador respeta
para siempre. Es barato, mejora solo con el uso, y **ninguna de las nueve apps lo
usa para arreglar su propia base de datos** -- Soysuper lo usa solo para esa cesta
y esa sesion.

Desglose en `docs/BACKLOG.md`, tarea N8.

### 10.2 "Minisuper": aprender lo que compras siempre

Soysuper aprende los productos habituales de cada persona para que montar la
cesta siguiente cueste menos. Nosotros tenemos las listas y el historial de quien
anadio que: sale gratis. Tarea N9.

### 10.3 Lo que hace y no nos sirve

Traspasa la cesta a la web del supermercado para comprar online. Nosotros somos
una app para **ir a la tienda**, no para comprar por internet: eso cambia el
producto entero.

Y una limitacion suya que es tambien nuestra, y que conviene decir en pantalla:
**el surtido de la web no es el de la tienda**, sobre todo en frescos. Lo
reconoce la propia OCU.

## 11. FindItApp — las cadenas regionales

Fuerte en Levante y Cataluna, con Consum, BonPreu y Caprabo. Reconoce que fuera de
esas zonas su base de precios es irregular.

Nos sirve como confirmacion de por donde crecer: despues de Eroski, **Consum** es
la siguiente cadena con tienda online propia y peso real.

## 12. Fuentes de datos externas: dos, y una con trampa

### 12.1 Open Prices (Open Food Facts) — util para comprobar, no para mezclar

`https://prices.openfoodfacts.org` — base de precios abierta, colaborativa, con
API REST y busqueda por codigo de barras. Suena perfecto y tiene un problema
serio: **la licencia es ODbL**, o sea *share-alike*. Si mezclamos sus datos con
los nuestros y publicamos el resultado, hay que publicar la base combinada como
datos abiertos.

Para un uso personal en casa da igual. Para el dia que esto se le deje a alguien
mas, no. **Decision: se puede leer para contrastar un precio puntual; no se
mezcla en `data/gold`.** Si algun dia se quiere usar de verdad, hay que decidirlo
a proposito y dejarlo escrito.

Ademas, para Espana esta muy vacia: son precios que sube la gente a mano.

### 12.2 AESAN — las alertas alimentarias oficiales

`https://www.aesan.gob.es/.../alertas_alimentarias/` publica las retiradas de
producto: producto, marca, lote, motivo y distribucion, con una referencia estable
por alerta (`ES2026/067`) y una URL por alerta.

No tiene RSS ni API ni volcado: es una pagina HTML con un listado cronologico. O
sea, exactamente el tipo de fuente que este proyecto ya sabe tratar, y **una sola
pagina al dia**, nada comparado con las 653 categorias de Carrefour.

Esto engancha con lo que se construyo el 17 de septiembre: la columna `es_recall`
y el aviso rojo en la ficha, que hoy solo puede alimentar Aldi (y esta a cero).
Con AESAN el aviso pasa a cubrir las cinco cadenas y se convierte en **la unica
funcionalidad de la lista que ninguna app de la competencia tiene**: nosotros
sabemos que hay en cada lista de la compra.

Desglose en `docs/BACKLOG.md`, tarea N10.

## 13. Resumen de esta pasada

| idea | de donde | la tenemos ya? |
|---|---|---|
| corregir un emparejamiento a mano | Soysuper | **no, y es la mejor** |
| aprender la compra habitual | Soysuper | no, pero el dato esta |
| avisar de retiradas de producto | AESAN + Aldi | media: falta la fuente |
| precios abiertos de contraste | Open Prices | no, y con cuidado por la licencia |
| cadenas regionales | FindItApp | no: Eroski y Consum, por ese orden |

---

# Segunda pasada: 18 de septiembre de 2026

La pasada del 17 miro **aplicaciones de lista de la compra**. Esta mira otra
familia que no estaba en el documento y que se parece mucho mas a lo que hacemos:
**comparadores espanoles con historico de precios**. Son cinco y ninguno aparecia
aqui.

## 14. Los cinco que hacen lo mismo que nosotros

### RadarSuper (radarsuper.com) — el que mejor se puede medir

Es el unico que publica sus numeros, asi que es el unico contra el que se puede
comparar de verdad. Y la comparacion es la conclusion mas importante de esta
pasada.

| | RadarSuper | nosotros |
|---|---:|---:|
| cadenas | 7 (las 5 nuestras + Lidl + Ahorramas) | 5 |
| Alcampo | 19.476 | **23.793** |
| Carrefour | 13.537 | **16.416** |
| DIA | 5.758 | **5.869** |
| Mercadona | **4.740** | 4.322 |
| Ahorramas | 8.041 | — |
| **referencias comparables entre cadenas** | **177** | **6.448** |

Esa ultima fila es la que importa. Ellos cubren **dos cadenas mas** y aun asi su
comparativa publica ("que supermercado es mas barato") se sostiene sobre **177
referencias identicas**. La nuestra sobre 6.448 grupos, 5.663 de ellos medidos en
kg/l/m.

Conviene ser justos: esas 177 pueden ser una cesta escogida para el estudio y no
todo lo que saben emparejar. Pero si es lo que ensenan, es lo que tienen.

**La leccion, que va contra la intuicion:** lo dificil de este dominio **no es
bajar los datos**. Bajarlos lo hace cualquiera, y ellos bajan mas cadenas que
nosotros. Lo dificil es **decidir que dos cosas son la misma cosa** y en que
unidad se restan sus precios. Ahi es donde estan las cuatro reglas de
`PRECIO-POR-UNIDAD.md`, el `FACTOR_INCREIBLE`, las unidades canonicas y los
grupos. Es nuestra ventaja real y hay que seguir invirtiendo ahi antes que en
anadir la sexta cadena.

Dato suyo de septiembre de 2026, para contrastar con el nuestro: Mercadona gana
en **43 de 177** productos comparables y Carrefour en 42. Nuestro numero del mismo
dia es que entre la cadena mas barata y la mas cara de un mismo producto hay un
**17 % de diferencia (mediana)**.

Ojo con una cosa: dicen cubrir **Lidl**. Nuestro reconocimiento del 7 de
septiembre (`LIDL.md`) comprobo con fichas reales que lidl.es **no publica precios
de alimentacion**, solo de bazar. Lo mas probable es que lo suyo salga del folleto
semanal, o sea **ofertas, no catalogo**. No se cambia la decision por un dato de
tercero, pero queda apuntado como comprobacion: si una ficha de alimentacion de
lidl.es llega a traer precio en el HTML, hay que rehacer el reconocimiento.

### Precios del Super (preciosdelsuper.es) — el mas grande

    cadenas     10: Mercadona, Carrefour, DIA, Alcampo, El Corte Ingles,
                Hipercor, Consum, Gadis, Ahorramas y Froiz
    catalogo    mas de 120.000 productos
    frecuencia  cada 24 horas
    tiene       historico, "bajadas de la semana", carrito, cesta optima
    coste       gratis
    no tiene    API publica

El doble de cadenas que nosotros y mas del doble de productos. Lo que no se sabe
-- porque no lo publican -- es **cuantos de esos 120.000 son comparables entre
cadenas**, que es la unica cifra que convierte un catalogo en un comparador.

Su seccion **"bajadas de esta semana"** si es una idea directamente copiable, y
nosotros la podemos hacer mejor: ellos comparan con la captura anterior; nosotros
tenemos trece dias de serie y el `FACTOR_INCREIBLE` para no confundir una bajada
con un formato mal leido.

### PrecioReal (precioreal.com) y Verificador de Ofertas

Se presentan como **"verificador de ofertas e historico de precios"**: la pregunta
no es cuanto cuesta, sino **si el descuento que anuncian es de verdad**. Es
comercio electronico en general, no supermercado, pero la idea es exactamente la
regla `dudoso` que ya tenemos: un "antes/ahora" no vale nada si el "antes" duro
tres dias.

Su web no da mas detalle sin entrar, asi que no hay numeros que apuntar.

### PreciRadar (preciradar.com)

"Precios de Mercadona y Carrefour, actualizados cada dia". Dos cadenas. Su
`robots.txt` no responde, asi que no se ha entrado a mirar; se apunta y ya.

### supermarket-tracker (github.com/seravifer/supermarket-tracker)

Codigo abierto, y por eso el mas informativo de todos: **Mercadona, Carrefour y
Consum**, un script diario, PostgreSQL para el historico y una **extension de
Chrome** que dibuja la curva de precios encima de la web del supermercado.

Dos cosas que aprender de el:

1. **Consum se puede bajar.** El nuestro lo descarto (ver abajo) por su
   `robots.txt`. Que ellos lo hagan no cambia nuestra decision, pero confirma que
   el dato esta ahi.
2. **La extension de navegador es una idea excelente y barata.** Ensenar la curva
   de precios de un producto **dentro de la web de la cadena**, mientras compras,
   es la unica forma de que el historico sirva en el momento de decidir. Para
   nosotros seria un cliente mas de la API que ya existe.

## 15. Cadenas nuevas: lo que se ha comprobado hoy

Reconocimiento hecho desde fuera, sin tocar nada.

| cadena | veredicto | por que |
|---|---|---|
| **Ahorramas** | **candidata seria** | `robots.txt` permisivo para categorias y fichas, `sitemap_index.xml` con `sitemap_0-product.xml` y `sitemap_2-category.xml` (actualizados el 16 sep). Fichas con URL limpia (`/miel-de-flores-mel-da-anta-800g-47.html`). Es Salesforce Commerce Cloud, que suele servir el precio en el HTML. **Falta comprobar** si el precio viene en el HTML o por AJAX. |
| **Consum** | **descartada, por su robots.txt** | La web es una SPA: la ficha de producto solo trae un *spinner*, el dato viene de `/api/`. Y su `robots.txt` dice literalmente `Disallow: /api/`. El unico camino al dato es el que el sitio prohibe. |
| **Eroski** | **descartada, por reCAPTCHA** | `supermercado.eroski.es/es/supermercado/` responde con "Checking your browser - reCAPTCHA". Aqui no se entra: **no resolvemos verificaciones anti-bot**, es una linea que no se cruza. |
| El Corte Ingles / Hipercor | sin mirar | los cubre Precios del Super; pendientes de reconocimiento |
| Gadis, Froiz, Condis, BonPreu, Caprabo | sin mirar | regionales |

### Spec del reconocimiento de Ahorramas (para quien lo haga)

Tres preguntas, por este orden, y **ninguna necesita escribir un colector**:

1. `GET https://www.ahorramas.com/cuidado-personal/desodorantes/otros-desodorantes/`
   con un cliente HTTP normal. ¿Aparece el precio en el HTML? Buscar `€`,
   `data-product`, `application/ld+json`.
2. Si no: mirar en las herramientas del navegador que peticion trae la rejilla de
   productos. En Salesforce Commerce Cloud suele ser
   `.../Search-UpdateGrid?cgid=<categoria>&start=0&sz=24`. Comprobarla contra el
   `robots.txt`, que hoy **no la prohibe**.
3. Si el precio esta: contar productos y comprobar que hay **precio por unidad**
   (EUR/kg, EUR/l). Sin eso no entra en la comparacion, solo en el catalogo.

Y la pregunta que decide de verdad: **¿cuantos de sus productos emparejarian con
los que ya tenemos?** Una cadena que anade 8.000 productos y 30 grupos
comparables no anade nada. La prueba es cruzar sus EAN -- si los publica -- contra
nuestros 25.094 productos con codigo de barras, **antes** de escribir el colector.

## 16. Que nos llevamos de esta pasada

1. **"Bajadas de esta semana"** (de Precios del Super). Tenemos mejor materia
   prima que ellos: trece dias de serie y un control de cifras increibles.
2. **Extension de navegador con la curva de precios** (de supermarket-tracker).
   La API ya existe; seria un cliente mas. Es la unica forma de que el historico
   aparezca en el momento de decidir.
3. **"Verificador de ofertas"** como pantalla propia (de PrecioReal). La regla
   `dudoso` ya esta calculada; hoy solo es un campo. Merece ser una pantalla:
   *"esta oferta no lo es"*.
4. **Ahorramas**, si el reconocimiento sale bien y si empareja.

Y lo que **no** nos llevamos: correr a por la sexta, septima y octava cadena. El
comparador con siete cadenas ensena 177 referencias comparables. Las cadenas se
suman; el emparejamiento se gana.
