# Cesta — ¿podemos hacer todo lo que hace la competencia?

**No.** Y la respuesta larga es mas util que la corta.

De las 38 funcionalidades encontradas en las nueve apps estudiadas
(`docs/COMPETENCIA.md`), el reparto es este:

    se pueden hacer ya                          14
    se pueden hacer, pero primero hay que
      arreglar algo nuestro                      5
    se pueden hacer cuando haya historico        3
    se pueden hacer, pero son un proyecto
      aparte                                     4
    NO se pueden hacer con los datos que hay     4
    NO se van a hacer, por decision              8

Lo importante no es el reparto: es **saber en cual esta cada una** antes de
prometersela a alguien.

---

## 1. Las cuatro que NO se pueden hacer, y no por falta de ganas

### 1.1 Filtrar por producto nacional

    lo tiene         nadie de las estudiadas, pero David lo pidio
    nuestro techo    ~1.900 productos de 51.781   (3,7 %)

    origen declarado por las cadenas     1.444   (solo Mercadona lo da)
    + lo que anadiria Open Food Facts      635   (de 12.835 que cruzan)

No hay fuente que lo arregle. BEDCA, la base espanola de composicion de
alimentos, describe **alimentos genericos** ("leche entera de vaca"), no
productos con codigo de barras, asi que no enriquece productos concretos.

El prefijo 84x del codigo de barras **no significa que el producto sea espanol**:
significa que la empresa que registro el codigo se dio de alta en GS1 Espana. Una
marca espanola puede envasar tomate chino y su codigo seguira empezando por 84.

**Veredicto: el filtro se queda escondido y se dice por que.** Dibujarlo a medias
seria peor: la gente lo usaria creyendo que filtra.

### 1.2 Nutricion en Alcampo y Aldi

    lo tiene         QueFalta (porque usa otra fuente), Yuka, El CoCo
    nuestro techo    cero, y es estructural

Ninguna de las dos publica codigo de barras. Sin EAN no hay cruce con Open Food
Facts, y no hay otra llave fiable. Son **25.638 productos, el 49,5 % del
catalogo**, que nunca tendran Nutri-Score, NOVA ni ingredientes por esta via.

Lo unico que puede cambiarlo es que publiquen el EAN en la **ficha** del producto
y no solo en el listado, como hacen DIA y Mercadona. Para saberlo esta escrito
`projects/cesta/sondear_fichas.py`, **sin lanzar todavia**.

Mientras tanto hay un parche parcial y honesto: **3.375 productos de Alcampo**
estan enlazados como *identicos* a un producto con EAN de otra cadena y podrian
heredarlo, marcado como **inferido**. Aldi no puede: todos sus enlaces son
*equivalentes*, porque es marca propia entera.

### 1.3 Notificaciones push

    lo tienen        QueFalta, Bring!, Listonic

Necesitan un servidor accesible a todas horas. **El PC de David se apaga.** No es
un problema de programacion: es la arquitectura que se eligio a proposito para no
pagar un servidor.

Lo que si se hace y cubre casi todo el caso: **las novedades al abrir la lista**.
"Mama cogio la leche, Mama puso papel de cocina".

### 1.4 Precios en tiempo real

    lo tienen        las apps de las propias cadenas

Nuestros precios son de la ultima captura, una vez al dia. Y **a veces de hace
tres dias**: el 11 y el 12 de septiembre Carrefour dio 403 y sus precios eran de
dos dias antes.

Por eso la regla de que cada precio lleva su fecha, y uno de mas de tres dias se
ensena pero **no decide en que tienda comprar**. No es un defecto tapado: es una
regla de la casa.

---

## 2. Las cinco bloqueadas por algo nuestro

Estas si se pueden hacer. Lo que pasa es que hoy **darian respuestas malas**, y
sacarlas antes de arreglar la causa seria peor que no sacarlas.

### 2.1 "Hay uno mejor y ademas mas barato"

    bloqueada por    los grupos demasiado anchos
    hoy daria        "Patatas fritas clasicas Hacendado (E, 6,00/kg)
                      -> prueba Patatas Golden Long McCain (A, 4,05/kg)"
                     que son patatas de bolsa contra patatas congeladas

Es **exactamente** el error que la OCU le achaca a Yuka: proponer alternativas de
otra categoria. Lo cometeriamos por la misma causa.

### 2.2, 2.3, 2.4 Pantalla de secciones, analisis por linea de producto, Explorar

Las dos primeras, bloqueadas por los grupos anchos: el agua con gas sale con un
167 % de diferencia porque el grupo mete Perrier con la marca blanca. Eso mide lo
ancho que es el grupo, no el ahorro.

La tercera ya **no** esta bloqueada: la seccion comun esta hecha
(`core/secciones.py`, 99,9 % de cobertura). Falta llevarla a gold.

### 2.5 La nota de salud del producto

    bloqueada por    nada tecnico; es que hay que cambiarla
    problema         el 76,9 % de nuestras letras salen de ordenar por precio

Nuestra letra A/B/C es una posicion **dentro del grupo**. La solucion esta
especificada (`BACKLOG.md` tarea 9): adoptar la formula de Yuka, que es absoluta
y esta publicada.

---

## 3. Las tres que necesitan tiempo, no trabajo

    sugerencias del historial     necesita 30 dias de listas hechas
    despensa deducida            necesita unos meses
    aviso de caducidad           solo si lo anterior demuestra que se usa

**No se puede acelerar programando.** Lo unico que hay que hacer **ya** es
guardar el cierre de compra (`BACKLOG.md` tarea 10): es barato ahora e imposible
de recuperar despues. Sin esa tabla, en diciembre no habra historial que mirar.

---

## 4. Las cuatro que son un proyecto aparte

    recetas a lista       guardar recetas, sacar ingredientes y casarlos con
                          productos: es el problema del emparejador otra vez
    app nativa y widget   hoy somos una web servida por Caddy
    folletos              nosotros ya tenemos las ofertas producto a producto,
                          que es lo que importa; el folleto es marketing
    modelo de ML para
      el emparejador      hay 1.748 pares verdaderos gratis, pero primero hay
                          que arreglar los grupos anchos

---

## 5. Las ocho que NO se van a hacer, por decision

No por no poder. Estan en `docs/FUNCIONALIDADES.md` seccion G con el motivo
completo. En corto:

    amigos por @usuario          sois dos; es burocracia
    varios carritos activos      una lista de casa y alguna suelta bastan
    7 colores de acento          es bonito y no cambia nada
    tarjetas de fidelizacion     son datos personales, algunas dan acceso a
                                 saldo, y solo ahorran abrir la cartera
    inventario de despensa
      a mano                     la version deducida es mejor y no cuesta
                                 trabajo a nadie
    escaneo de tickets por foto  OCR sobre papel arrugado, un formato por
                                 cadena, se rompe al cambiar el disenio. Si
                                 hace falta, la puerta es el ticket digital.
    "enviar al supermercado"     automatizar una compra en su web en nombre del
                                 usuario. Ni sencillo ni limpio.
    mas cadenas                  las nuestras se comparan entre si; anadir sin
                                 poder emparejar es cambiar lo util por una
                                 lista mas larga

---

## 6. Y las catorce que si, ya

    orden por pasillos           la seccion ya esta hecha al 99,9 %
    mosaico de lo habitual       el dato ya esta en lista_linea
    voz para buscar              del navegador, sin dependencias
    escaner de codigo de barras  23.312 codigos, con sus avisos
    la oferta mientras anades    core/promos.py ya esta hecho y probado
    notas por linea              el campo ya existe
    aviso legal                  dos parrafos
    sellos de Open Food Facts    sin gluten, ecologico, vegano, sin lactosa
    nutrientes completos         11.723 productos
    total en vivo                hecho
    dos secciones en la lista    hecho
    invitar por enlace           hecho
    novedades al abrir           hecho
    fotos de producto            hecho, al 100 % en las cinco cadenas

---

## 7. Lo unico que de verdad limita este proyecto

No es el tiempo ni la dificultad: es **que Alcampo y Aldi no publican el codigo
de barras**. Son la mitad del catalogo, y de ahi salen tres de los cuatro "no se
puede":

    sin EAN  ->  sin cruce con Open Food Facts
             ->  sin Nutri-Score, sin NOVA, sin ingredientes, sin sellos
             ->  el escaner no los reconoce
             ->  la nota de salud no existe para ellos

Todo lo demas son decisiones o cuestion de tiempo. Por eso la tarea 7 del
backlog — **lanzar `sondear_fichas.py` y saber de una vez si lo publican en la
ficha** — vale mas de lo que parece por lo poco que cuesta: es una ejecucion y
una decision, y puede desbloquear la mitad del catalogo.
