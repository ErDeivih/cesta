# Eroski: se lee entera, y sin navegador

Reconocimiento cerrado el 19 de septiembre de 2026, con tres sondeos desde la
linea de casa. Hacen falta tres porque los dos primeros fallaron, y por que
fallaron es la mitad de lo que hay que contar aqui.

## Veredicto

**Se puede leer, y con un cliente HTTP normal.** Ni navegador, ni reto anti-bot,
ni zona AJAX: la categoria hoja trae los productos **servidos por el servidor**,
con su precio dentro.

    robots.txt           200, 1.948 bytes, y permite las rutas que hacen falta
    portada              200, 999.811 bytes
    categoria hoja       200, 1.245.781 bytes, con 14 productos y sus precios
    ficha de producto    /es/productdetail/<id>-<slug>/

## Lo que publica, por producto

Cada tarjeta de producto lleva un `data-metrics` con el evento de GA4 escapado en
HTML. Descodificado:

```json
{"price": 5.85, "item_id": "23760622",
 "item_name": "Naranja EROSKI, malla 3 kg", "item_brand": "EROSKI.",
 "item_category": "2059698", "item_category2": "2059699",
 "item_category3": "2059700", "item_variant": "",
 "item_affiliation": "Eroski", "quantity": 1, "index": 1}
```

Precio, nombre, identificador, marca y **la categoria en tres niveles, por su
codigo**. Es el mismo truco que ya usamos en Carrefour para sacar el EAN del
datalayer de analitica.

Y ademas, en el HTML visible:

    precio por unidad   "1 KILO A  1,95 €"   en 13 de los 14 productos
    imagenes            /images/<id>.jpg y /images/<id>_x.jpg (grande)
    valoraciones        "3,7 de 5 estrellas (9)"  <- **esto no lo da nadie mas**
    enlace a la ficha   /es/productdetail/<id>-<slug>/

Las valoraciones de clientes son algo que **ninguna de nuestras cinco cadenas
publica**. Si Eroski entra, entra con un dato que no teniamos.

## El arbol de categorias, de una sola peticion

Cualquier pagina del supermercado trae el menu entero: **1.593 enlaces de
categoria distintos**, jerarquicos y con su codigo:

    /es/supermercado/2059698-frescos/
    /es/supermercado/2059698-frescos/2059699-frutas/
    /es/supermercado/2059698-frescos/2059699-frutas/2059700-naranjas-y-otros-citricos/

El recorrido esta resuelto antes de empezar. Y los `item_category` del GA4 son
esos mismos codigos, asi que cada producto se ata solo a su rama.

## Lo que NO publica (medido, no supuesto)

- **Codigo de barras: no aparece, y la ficha tampoco lo trae.** Sondeada la
  ficha el 21 de septiembre de 2026 (`/es/productdetail/23760622-naranja-eroski-malla-3-kg/`,
  HTTP 200, 878.580 bytes): **cero candidatos a EAN de 13 digitos**, ni en el
  listado, ni en el `data-metrics`, ni en la ficha. Queda medido, no supuesto.

  La consecuencia es la que se temia: **Eroski es como Alcampo, sin cruce con
  Open Food Facts.** Ni Nutri-Score, ni NOVA, ni ingredientes por esa via. Todo
  lo que aporte tiene que salir de emparejar por nombre y formato.
- **JSON-LD: no hay.** Nada de `schema.org/Product`. Confirmado tambien en la
  ficha.

## Las tres veces que me equivoque, y por que

Esta parte importa mas que el veredicto, porque los tres fallos eran del sondeo,
no de Eroski, y los tres daban un resultado que **parecia** una conclusion.

### 1. "Eroski esta detras de un reCAPTCHA" (18 sep) — falso

Lo dije con un 403 desde el contenedor y un titulo indexado en Google. Desde una
linea de casa, Eroski contesta **200 y sin pedir nada**. Un 403 desde un centro
de datos no es un reto anti-bot: es que no hablan con centros de datos.

### 2. "La categoria no trae productos" (19 sep, manana) — falso

Se sondeo `/2059806-alimentacion/`, que es **un nodo de navegacion**: devolvio un
megabyte de menu y ni un producto. Es el mismo patron del nodo vacio de Alcampo
que nos costo la rama Frescos entera. **Sondear una rama no dice nada de las
hojas.**

### 3. "No hay precios en esta pagina" (19 sep, tarde) — falso, y el mas fino

El sondeo dijo `precios con simbolo de euro: 0` en una pagina que a la vista pone
**"1 KILO A 1,95 €"**. En bytes:

    b'1 KILO A  1,95\xc2\xa0\xe2\x82\xac'
                      ^^^^^^^^ espacio duro (U+00A0)

`\s` en un patron de **bytes** solo casa el espacio ASCII. Entre el numero y el
simbolo del euro casi ninguna web espanola pone un espacio normal: pone un
espacio duro, para que no se parta la linea.

Un falso negativo asi no dice "no lo he encontrado": dice **"aqui no hay
precios"**, que es un veredicto. Con ese veredicto se cierra una cadena que si se
podia leer, y nadie vuelve a mirarla.

Arreglado en `sondear_cadena.py`: el separador entre numero y simbolo admite
espacio duro, `&nbsp;` y `&#160;`, y el precio por unidad se busca tambien en
prosa ("1 KILO A", "PRECIO POR LITRO"), que es como lo escribe Eroski.

### Y un cuarto, de propina: la ficha que no era una ficha

El sondeo "siguio una ficha" y lo que siguio fue **el selector de idioma**:

    /es/supermarket.menulayout.menumobile.languageswitcher:changelanguage/es
        ?t:ac=2059698-frescos/...

Una direccion de evento de Apache Tapestry. Devolvio la misma pagina de la
categoria, asi que el informe salio identico y **parecia que habia funcionado**:
un falso positivo silencioso, que es peor que un error. Ahora se descartan las
direcciones con `:` en la ruta (ojo: el puerto `:443` tambien lleva dos puntos, y
mirar la direccion entera en vez de la ruta rechazaba fichas buenas).

Y la rejilla de Eroski empieza **pasados los primeros 600 KB** de menu, asi que
buscar el enlace solo en el principio del cuerpo no encontraba nada. Ahora se
mira el cuerpo entero.

## Lo que decide si entra, y no es nada de lo anterior

**Cuantos de sus productos emparejarian con los que ya tenemos.** Sin codigo de
barras hay que emparejar por nombre y formato, que es lo caro y lo que de verdad
distingue este proyecto. La competencia lo demuestra: RadarSuper cubre siete
cadenas y ensena **177** referencias comparables; nosotros con cinco, 6.429.

Asi que antes de escribir una linea de colector:

1. Bajar **una categoria hoja de cada rama** (son 1.593, pero con 20 llega para
   medir) y sacar sus productos con el `data-metrics`.
2. Pasarlos por el emparejador contra nuestro catalogo actual.
3. Contar **cuantos grupos comparables nuevos** salen. Si son pocos, Eroski anade
   catalogo y no anade comparaciones, y no compensa el dia de trabajo.

## Spec del colector, cuando se escriba

    sitemap        no hace falta: el menu de cualquier pagina da las 1.593
                   categorias con su codigo y su jerarquia
    listado        GET /es/supermercado/<rama>/<sub>/<hoja>/
                   productos en `data-metrics` (GA4, escapado en HTML)
                   precio por unidad en `<p class="quantity-text">`
    ficha          GET /es/productdetail/<id>-<slug>/   sondeada el 21 sep
                   2026: 200, un precio, precio por unidad, y **sin EAN**.
                   No aporta nada que no de ya el listado, asi que el colector
                   **no tiene por que pedirla**: una peticion por producto que
                   no paga lo que cuesta
    ritmo          0,5 pet/s, como el resto
    robots.txt     comprobar cada ruta antes de pedirla; hoy permite lo anterior

## Lo que queda, despues del sondeo de la ficha (21 sep 2026)

El reconocimiento esta **cerrado**: se lee entera, sin navegador, sin reto, y
sin codigo de barras en ninguna parte. No queda nada que sondear.

Lo unico que falta es la medicion que decide si entra, y es la de arriba: bajar
20 categorias hoja, pasarlas por el emparejador y **contar cuantos grupos
comparables nuevos** salen. Sin EAN esa cuenta sale peor que con el, asi que el
numero importa mas todavia.

    uv run python -m projects.cesta.sondear_cadena eroski --guardar

sigue sirviendo para repetir el sondeo si un dia Eroski cambia de casa.
