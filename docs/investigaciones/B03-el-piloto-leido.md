# B03 · El piloto de Lidl, leido: **`sondear_lidl.py`, 81 lineas**

*(13 de octubre de 2026. **Segundo de los siete ficheros, y es el que contesta las preguntas de diseno.**)*

## 1. Y las contesta **con codigo, no con promesas**

### La region: **de `regionsV2`, nunca de un codigo postal**

```python
def precios_region(producto: dict, region: str) -> dict:
    """Resuelve region -> regionPriceId; NUNCA USA EL PRECIO POR DEFECTO COMO SUSTITUTO."""
    contexto = producto.get("regionsV2", {}).get(str(region))
    if not isinstance(contexto, dict) or contexto.get("regionPriceId") is None:
        return {"estado": "region_desconocida", "precios": None}
```

**Y el argumento de linea de ordenes lo dice con estas palabras:**

```
--region   Identificador observado en regionsV2; NO CODIGO POSTAL
```

> **Es exactamente lo que el plan pide** -- *«validar tienda/region y **no convertir CP en id de region sin
> correspondencia**»* --, **y esta resuelto de la unica forma honesta**: *el identificador de region **se
> observa** en el propio payload; si no esta, se dice `region_desconocida` y **no se usa el precio por
> defecto como sustituto.**

**Y eso responde la pregunta que el plan deja abierta** -- *«pedir SOLO ese dato al propietario cuando sea
necesario»* --: **no hace falta pedirlo para capturar.** *Las regiones estan **dentro** del dato, y `--region`
sirve para **elegir** una, no para inventarla.* *Lo que habria que preguntar es **cual quiere**, y solo si
quiere una concreta.*

### El desafio no es un catalogo vacio, y esta escrito

```python
if not productos:
    raise ValueError("HTML sin fichas Lidl: NO EQUIVALE A CATALOGO VACIO VALIDO")
```

> **Es la regla que el encargo pide por su nombre** -- *«no confundas desafio con catalogo vacio»* -- **y esta
> en la primera funcion.** *Un HTML sin `data-grid-data` **revienta**, no devuelve una lista vacia que
> parezca un catalogo de cero productos.*

### IAN y EAN, separados a proposito

```python
def extraer(html: str) -> list[dict]:
    """Conserva el payload completo; NI IAN NI productId SE CONVIERTEN EN EAN."""
```

**Y el duplicado con datos distintos tambien revienta** -- *«Producto {pid} repetido con datos distintos; no
sobrescribir»* --, *en vez de quedarse con el ultimo.*

### Y las condiciones, crudas y sin convertir en precio elegible

```python
"""Devuelve condiciones crudas (normal/club, fechas, formato); NO UN PRECIO ELEGIBLE.
   El campo status de la region NO ES STOCK EN UNA TIENDA."""
```

> **«NO un precio elegible»** -- *y esa distincion es la que B03 pide respetar cuando dice que Lidl «si puede
> ofrecer **una linea exacta con precio valido**»*: *el piloto trae **condiciones**, y convertirlas en un
> precio elegible es el paso que falta, **con sus reglas de club y de fechas**.*

## 2. Lo que el resumen ya declara

```
"cobertura": "ofertas_semanales_parcial",
"fichas_variantes": ..., "productos_padre": ..., "con_precios_regionales": ...,
"aviso": "No integrado en ingesta; no certifica stock, identidad ni precio vigente."
```

**Las tres cuentas que B03 pide** -- *«cobertura por campo»* y *«contador visible»* -- **ya se calculan**, y el
`aviso` dice en una linea lo que **no** certifica. *Es el mismo patron de `sin_cantidad` y `coherencia: None`:
**lo que no se sabe, dicho al lado de lo que si.***

**Y el `robots.txt` se comprueba antes de pedir la pagina** (`can_fetch`), *y si la politica no lo permite,
**revienta en vez de pedirlo igual.***

## 3. Y lo que falta, que es la integracion

*El piloto tiene 81 lineas y ya hace: extraer, validar esquema, resolver region, contar cobertura y decir sus
limites.* **Lo que NO hace, y es B03 entero:**

  - **bronze.** *No escribe nada: imprime un resumen por pantalla.* *«Sin publicar bronze», dice su
    docstring, y es la verdad.*
  - **silver → gold.** *No pasa por el pipeline.*
  - **API ni UI.** *Lidl no aparece como sexta fuente.*
  - **El veto global, quitado.** *`CADENAS` sigue teniendo cinco.* **Y el piloto ya demuestra que hay 76
    fichas que hoy se tiran.**
  - **Condiciones → precio elegible**, con sus reglas de club y fechas.
  - **Y la captura acotada**: *el plan la pide, y el piloto pide **una** pagina.*

## 4. Lo que queda por leer

```
collectors/lidl.py 11,7 KB   descubrir_lidl.py 9,9 KB   fichas_lidl.py 6,7 KB
ficha_lidl.py 7,7 KB         run.py
```

*Cinco ficheros.* **Y `run.py` es el que dice como se engancha al ciclo diario**, *que es la pieza que B03
pide por su nombre.*
