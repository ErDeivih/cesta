# Cesta — usabilidad para alguien que no la construyo

Hasta ahora la app la usan dos personas que saben de donde salen los datos. El
dia que entre un amigo, todo lo que hoy se sobreentiende deja de entenderse.

Este documento es la lista de lo que hay que arreglar para eso, **medida contra
la interfaz que existe hoy**, no contra una ideal.

---

## 1. La regla que lo resume todo

**Si hay que explicarlo, esta mal hecho. Si no se puede no explicarlo, se explica
donde pasa, no en una pantalla de ayuda.**

Sigue sin haber tutorial ni pantalla de bienvenida (`PANTALLAS.md` punto 10).
Eso no cambia. Lo que cambia es que **cada sitio donde hoy falta una frase, la
tiene que llevar**.

---

## 2. Los seis sitios donde un amigo se quedaria colgado

### 2.1 La primera vez que abre, no hay nada

    hoy      entra, ve un buscador vacio y una lista vacia. Nada le dice que
             hacer.
    arreglo  el mosaico de habituales (F3.1) no tiene datos el primer dia, asi
             que en su lugar va **una frase y tres ejemplos que se pueden
             pulsar**:

                 Busca lo que compras. Por ejemplo:
                 [ leche entera ] [ papel de cocina ] [ atun ]

    por que  un buscador vacio no ensena que se puede buscar. Tres ejemplos
             pulsables si, y de paso demuestran que el catalogo es de verdad.

### 2.2 "1 cadenas" y otras cuentas mal escritas

    hoy      la interfaz escribe "3 cadenas · 5 productos" con un `${n}` pelado.
             Con n=1 sale "1 cadenas · 1 productos".
    ojo      el caso de "1 cadenas" **ya se arreglo** quitando el sello de
             comparable, pero el texto en plural sigue ahi para otros contadores
    arreglo  una funcion `plural(n, "cadena", "cadenas")` y usarla en todos.
             Son ocho sitios.
    por que  a quien construyo la app se le pasa; a quien la usa por primera vez
             le dice "esto esta a medias"

### 2.3 Nadie sabe que significa "gama B"

    hoy      la ficha pone `gama B` con un `title` que lo explica. **En un movil
             no hay `title`: no hay raton con el que pasar por encima.**
    arreglo  que el sello sea pulsable y abra una linea de explicacion:
             "Gama: sale de ordenar por precio dentro de su grupo, no de leer la
              etiqueta. No es una nota de calidad."
    lo mismo para `calidad A`, `NOVA 3` y `no comparable`.
    por que  un dato que no se entiende es peor que no ensenarlo: la gente se
             inventa lo que significa

### 2.4 "Sin conexion con casa" no dice de quien es la casa

    hoy      "Sin conexion con casa. Esto es lo ultimo que vi."
    problema para tu madre, "casa" es su casa. Para un amigo, ¿que casa?
    arreglo  "No llego al ordenador de David. Esto es lo ultimo que vi; lo que
              cambies se guardara y se subira cuando vuelva."
    por que  el amigo tiene que entender que **depende de una maquina de otra
             persona**, y eso es informacion, no un fallo que ocultar

### 2.5 Los precios no dicen de donde salen

    hoy      el pie de ajustes lo explica. Nadie entra en ajustes.
    arreglo  bajo el total de la lista, una linea pequena y permanente:
             "Precios orientativos del 17/09. Pueden variar en tienda."
    por que  es lo que hace QueFalta, es verdad, y es lo primero que pregunta
             alguien que no sabe como funciona esto

### 2.6 No hay forma de salir

    hoy      `DELETE /api/yo` ya existe (se anadio hoy). No hay boton.
    arreglo  en ajustes, abajo del todo, "Darme de baja", con confirmacion
             escribiendo el usuario, y diciendo que se lleva y que no:
             "Se borran tus listas, tus favoritos y tu cuenta. Lo que anadiste a
              listas de otros se queda, sin tu nombre."
    por que  quien presta su ordenador para que otros guarden ahi su lista de la
             compra les tiene que dar la puerta de salida

---

## 3. Lo que ya esta bien y conviene no romper

Para que nadie lo "mejore":

    la barra abajo          el pulgar llega. Arriba no.
    dos secciones           "por coger" y "en el carro", no una lista tachada.
                            En el pasillo miras la lista veinte veces y lo que
                            necesitas saber es QUE ME QUEDA.
    nada espera al servidor anadir, tachar y cambiar cantidad se pintan al
                            instante. Un boton que tarda dos segundos se pulsa
                            tres veces.
    el total, pegajoso      es lo que se mira mientras se anaden cosas
    lo que falta, por su
      nombre                "le faltan 2" no sirve para decidir; "en Mercadona
                            no encuentro cafe en grano" si
    el reparto que no
      compensa, se dice     "solo ahorra 0,80 EUR. No compensa el viaje."
    calidad != gama         nunca las dos a la vez

---

## 4. Accesibilidad: lo que falta y no cuesta

Hoy la interfaz tiene areas de pulsar grandes, `aria-pressed` en los chips y
`aria-current` en la navegacion. Falta:

    foco visible      hay `:focus-visible` con el ambar, pero no se ha probado
                      recorriendo la app entera con el tabulador
    lectores          la lista usa `aria-label` en el check, pero el marcador
                      del total no se anuncia al cambiar. Un `aria-live="polite"`
                      en el total y ya.
    contraste         el ambar sobre papel claro esta al limite. Medirlo.
    texto grande      si alguien pone el movil al 200 %, las tres columnas del
                      mosaico tienen que bajar a dos. Falta la media query.
    movimiento        `prefers-reduced-motion` ya esta puesto.

Nada de esto es por cumplir: **tu madre va a usar esta app durante anos**, y la
vista cansa.

---

## 5. Los errores, uno por uno

Hoy la app dice "No he podido cargarlo" en varios sitios. Eso no es un mensaje de
error, es un encogimiento de hombros. Cada uno tiene que decir **que ha pasado y
que se puede hacer**:

    no llego al servidor        "No llego al ordenador de David. Tu lista sigue
                                aqui; lo que cambies se subira luego."
    la lista no existe          "Esa lista ya no esta. Puede que la haya borrado
                                quien la creo."
    el enlace no vale           "Ese enlace ya no vale: caduca a los siete dias
                                o puede que ya lo hayan usado tres personas.
                                Pidele otro a quien te lo mando."
    tres enlaces vivos          "Ya hay tres enlaces sin usar para esta lista.
                                Anula alguno antes de crear otro."
    sin permiso para escribir   "En esta lista solo puedes mirar. Pidele a quien
                                la creo que te deje escribir."
    el codigo no se reconoce    "No tengo este codigo. Puede ser marca propia de
                                Alcampo o Aldi, que no publican codigo de
                                barras." + buscador por nombre

**Ninguno dice "error".** Dicen que ha pasado.

---

## 6. Orden

    con la app como esta hoy
      1  plural(n, ...) en los ocho contadores          XS
      2  el aviso de precios bajo el total              XS
      3  "el ordenador de David", no "casa"             XS
      4  los seis mensajes de error de arriba           S
      5  los sellos pulsables con su explicacion        S

    cuando entre el primer amigo
      6  los tres ejemplos pulsables al abrir           XS
      7  el boton de darse de baja                      S
      8  el repaso de accesibilidad con el tabulador    S

Del 1 al 5 se puede hacer sin esperar a nadie, y hacen la app mas facil tambien
para los dos que ya la usan.

---

# Los filtros de dieta en pantalla (17 de septiembre de 2026)

## Donde estan

Debajo de las pastillas de cadena, dentro de un `<details>` **plegado**. En un
movil, cada fila que se ve antes de los resultados es una fila de resultados que
no se ve, y la mayoria de las busquedas no necesitan filtros.

```
  [buscar: leche entera                    ]
  [Alcampo] [Aldi] [Carrefour] [DIA] [Mercadona]
  ⌄ Filtros  ②
```

## Las tres decisiones que importan

**1. El contador en el resumen.** `Filtros ②` cuando hay dos puestos. Sin el, un
filtro plegado es una trampa: buscas, no sale nada y no entiendes por que. El
contador es lo unico que convierte un filtro escondido en un filtro honesto.

**2. Cuando no hay resultados, se culpa a los filtros y se da el boton.**

```
  Nada con «pizza» y los filtros puestos.
  [Quitar los filtros]
```

Si no hay filtros puestos, el mensaje es el de siempre (probar una palabra mas
corta, activar alguna cadena). La diferencia importa: el 90 % de los ceros con
filtros puestos son por los filtros.

**3. El area de toque del resumen es de 44 px.** Es un `<summary>`, que por
defecto mide lo que mide el texto. En el pasillo del supermercado, con una mano y
el carro en la otra, un objetivo de 20 px no se acierta.

## En la ficha del producto

Los sellos van **arriba del todo**, antes del precio, porque quien filtra por
dieta vuelve a comprobarlo en la ficha y es lo primero que mira. Al lado, en
pequeno, de donde sale el dato:

```
  [Sin lactosa]  certificado del producto
```

Los cuatro textos posibles:

| `sellos_origen` | lo que pone |
|---|---|
| `certificado` | certificado del producto |
| `etiqueta` | lo etiqueta la cadena |
| `nombre` | solo lo dice el nombre del producto |
| `mixto` | la cadena y el nombre del producto |

"Solo lo dice el nombre del producto" es una frase incomoda a proposito. 990 de
los 1.021 productos con `sin-azucar` salen de leer el nombre, y el nombre es
marketing. Decirlo es la diferencia entre una app en la que se puede confiar y
una que da por seguro lo que no lo es.

## Lo demas que se ve ahora en la ficha

- **Tabla nutricional** de la etiqueta, con su "por 100 g" o "por 100 ml" en el
  titulo de la fila. No es el Nutri-Score: es el dato del que sale, y lo publica
  la cadena.
- **Certificados** con su nombre largo: "Denominación de Origen", "Pesca
  sostenible (MSC)", "Bienestar animal". No las siglas.
- **Conservación** en castellano de andar por casa: "En la nevera", "En el
  congelador", "En la despensa".
- **Hasta cuando dura la oferta**, dentro de la caja de oferta: "Hasta el 20 de
  septiembre". Cuando se acaba importa tanto como cuanto baja.

---

# Lo que cambio en pantalla la tarde del 17 de septiembre

## 1. "Oferta solo con tarjeta", dicho con esas palabras

Aparecieron 221 ofertas de DIA que no teniamos, y **200 son solo con la tarjeta
Club**. Un descuento de tarjeta no baja lo que pagas en caja: se acumula en un
monedero. Asi que:

- El filtro **"En oferta"** las excluye. Quien busca ofertas busca pagar menos
  hoy.
- La tarjeta del resultado dice `oferta solo con tarjeta`, nunca `con oferta`.
- La ficha las pinta distintas (borde ambar, un poco apagadas) y lo explica:

```
  Oferta de tarjeta
  20% DTO. CHORIZO PAMPLONA DIA
  Solo con la tarjeta de la cadena — no baja lo que pagas en caja
```

Esa frase es fea a proposito. La alternativa es que alguien llegue a la caja
esperando pagar un 20 % menos.

## 2. El aviso de producto retirado

Lo unico de toda la interfaz con fondo rojo, y va **arriba de la ficha**, antes
del precio:

```
  Producto retirado
  La cadena ha retirado este lote de la venta. Si lo tienes en casa, no lo
  consumas y consulta en su web o en la AESAN.
```

Hoy no salta en ningun producto: Aldi publica el campo y lo tiene a `false` en
sus 2.065. Se ha construido igual, porque el dia que salte hay que tenerlo hecho,
y porque **ninguna app de la competencia avisa de retiradas de producto** y
nosotros sabemos exactamente que hay en cada lista de la compra.

En la tarjeta del resultado sale como `⚠ lote retirado`.

## 3. "Sin alcohol", un filtro que se afina al contrario que los demas

Nueva pastilla en los filtros. Y una decision de fondo que conviene entender
antes de tocarla:

| filtro | que hace | pasarse | quedarse corto |
|---|---|---|---|
| Sin gluten | **incluye** | PELIGROSO | molesto |
| Sin alcohol | **excluye** | molesto | PELIGROSO |

En "sin gluten" no se puede ensenar nada de lo que no estemos seguros. En "sin
alcohol" es lo contrario: si nos pasamos, desaparece un vinagre de Jerez que se
podia comprar; si nos quedamos cortos, alguien que no bebe ve una cerveza. Asi
que aqui se prefiere pasarse, y de ahi que el alcohol se **deduzca** del nombre
para las tres cadenas que no lo declaran. Ver `core/alcohol.py`.

## 4. "Al peso": decir de cuanto es la estimacion

742 productos de Alcampo se venden al peso y ahora la ficha dice la horquilla:

```
  Al peso    Ronda los 500 g, y puede variar un 25 %.
             El precio por kilo es exacto; el total, una estimación.
```

Antes el total salia como si fuera exacto. Esta frase es la diferencia entre un
dato y una promesa.

## 5. "La cadena dice"

550 productos de DIA llevan un distintivo suyo: "De los mejor valorados en su
web" (282), "Novedad" (168), "Apto para freidora de aire" (82), "Precio
destacado" (18).

Es la **unica senal de popularidad de todo el proyecto**: ninguna cadena publica
ventas, y las valoraciones de Alcampo son 1.260 votos en total para 23.793
productos, o sea ruido. Por eso la fila se llama "La cadena dice" y no "Valorado
con 4 estrellas": lo dice DIA, no lo decimos nosotros, y eso se nota en la
redaccion.

## 6. "Atencion": los pictogramas de peligro

450 productos de limpieza de Alcampo traen los pictogramas del Reglamento CLP.
En la ficha, en rojo:

```
  Atención    Corrosivo para la piel, ojos y/o metales · Inflamable
```

Detalle pequeno que costo un arreglo: las advertencias se guardan separadas por
` | ` y no por comas, porque una de las etiquetas de Alcampo es literalmente
"Corrosivo para la piel, ojos y/o metales" y con comas se partia en dos
advertencias que no significan nada.
