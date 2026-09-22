# ¿Nos dejamos categorias sin pedir?

`projects/cesta/auditar_recorrido.py`, escrito el 18 de septiembre de 2026. Es el
gemelo de `auditar_crudo.py`, y la diferencia entre los dos es toda la gracia:

    auditar_crudo.py       de las respuestas que SI bajamos, que campos no leemos
    auditar_recorrido.py   que respuestas NO bajamos aunque la cadena nos diga
                           que existen

---

## 1. El fallo que obliga a escribirlo

Alcampo entrego un catalogo sin la rama Frescos entera, con cero errores. La
causa cabia en una linea:

```python
if len(productos) >= TOPE_API and hijas:
    pendientes.extend(hijas)      # bajar
else:
    filas.extend(productos)       # quedarse
```

Su API devuelve los productos de **todo el subarbol** de una categoria, con un
tope de 300. De ahi salen tres casos y el tercero estaba mal:

| lo que devuelve | que significa | que hacia |
|---|---|---|
| 300 productos y con hijas | viene cortado | bajar ✔ |
| entre 1 y 299 | cabe entero | quedarse ✔ |
| **0 productos y con hijas** | **nodo de navegacion: todo esta abajo** | **quedarse ✘** |

Ese tercer caso no anadia nada (no habia productos) y no encolaba nada. El
subarbol entero desaparecia. Sin error, sin excepcion, sin hueco en el log.

Arreglado: se baja tambien cuando no hay productos y si hay hijas.

## 2. Lo que midio

Sobre el crudo del 17 de septiembre, un dia que se dio por bueno:

    2.696 categorias declaradas
    1.807 solo las declara el menu completo (ramas excluidas a proposito)
      701 no se pidieron pero llegan por otro camino
       32 **no llegan de ninguna forma**

Y las 32 no son cualquier cosa:

    Lacteos sin lactosa · Chocolates sin azucares anadidos o sin lactosa
    Sin Gluten / Sin Lactosa, Nutricion deportiva y Funcional
    Arroz Ecologico · Pollo Ecologico · Bebidas de avena veganas
    Cochinillo · Sobrasada · Chorizo iberico · Salchichas gourmet
    Ron Premium · Paté en conserva · Pisto y sofritos

La mitad son **categorias de dieta**, justo donde nuestros sellos serian mas
utiles. La otra mitad, producto fresco de gama alta.

Sobre el crudo del 18, el dia malo, la cifra sube a **597**. La herramienta
distingue sola un dia bueno de un dia roto.

## 3. Las tres condiciones para contar una categoria como perdida

Una categoria cuenta como perdida solo si cumple **las tres**:

1. no se pidio (su clave no esta en el crudo del dia),
2. no trae sus productos dentro de la respuesta de su padre, y
3. su nombre no aparece en ninguna categoria del bronze de ese dia.

La segunda quita a Mercadona 469 falsas alarmas: su API devuelve la categoria de
nivel 2 con las hojas y sus productos dentro, asi que no hace falta pedirlas.

La tercera quita 701 mas en Alcampo: muchas hijas llegan igual porque su padre
devolvio el subarbol entero.

Y hay un cuarto filtro, el del menu: **el menu completo de Alcampo declara el
arbol entero de la tienda**, ramas excluidas incluidas. Sin descartarlo, la
herramienta cantaba 899 perdidas que eran juguetes, bricolaje y accesorios de
coche. Solo cuentan las categorias que declara una respuesta **de categoria**, o
sea aquellas por las que ibamos andando cuando nos dejamos el desvio.

## 4. Lo que no puede auditar, y por que

DIA, Carrefour y Aldi guardan **HTML**, no JSON, asi que no declaran su arbol de
forma que se pueda recorrer con esto. Lo dice y sigue:

    dia: su crudo no declara el arbol en JSON, no se puede auditar asi

Para esas tres, el control equivalente es otro: DIA y Carrefour salen de un
sitemap (si el sitemap miente, no hay forma de saberlo desde dentro) y Aldi de un
unico indice de productos. Su red de seguridad es `core/cobertura.py`, que
compara rama a rama contra el dia anterior.

## 5. Como se anade una cadena

Una entrada en `CLAVES` con la plantilla de su clave de cache:

```python
CLAVES = {
    "alcampo": ("api-category-{id}",),
    "mercadona": ("category-{id}",),
}
```

Si un colector cambia como construye su clave y aqui no se cambia, la auditoria
diria que no se pidio nada de nada. Hay una prueba que lo fija.

## 6. Lo que encontro en las otras cadenas

**Mercadona**: 2 categorias el 18 ("Jamon serrano", "Perfume y colonia mujer") y
1 el 17. Es ruido de un arbol que cambia, no un agujero.
