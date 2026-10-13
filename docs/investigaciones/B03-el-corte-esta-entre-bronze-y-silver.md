# B03 · **El corte de Lidl esta entre bronze y silver**, y el motivo es una hora

*(13 de octubre de 2026. **Se buscaba por que Lidl no llega a la pantalla, y la respuesta es que el pipeline
no ha corrido desde que su bronze existe.**)*

## 1. El corte, medido en tres sitios

```
bronze:    data/bronze/fuente=lidl/fecha=2026-10-13/part.parquet      EXISTE (escrito hoy)
silver:    data/silver/fuente=alcampo aldi carrefour dia mercadona     CINCO, y NO hay fuente=lidl
publicado: /api/estado -> version 20261013-125853, fecha_datos 2026-10-13
           cadenas: alcampo 22816 · aldi 2476 · carrefour 16149 · dia 5760 · mercadona 4168
```

> **Lidl tiene bronze y no tiene silver, asi que no llega a la API** -- *porque la API lee `silver`
> (`cesta.py:302`), no bronze.*

## 2. Y el motivo esta en las horas

  - **La version publicada es `20261013-125853`**: *las 12:58:53 de hoy.*
  - **El bronze de Lidl se escribio despues**: *sobre las 13:00.*

**Asi que el pipeline no ha corrido desde que el bronze existe.** *No es que Lidl se caiga por el camino: es
que **el camino no se ha andado todavia**.*

**Y la pieza que lo leeria si existe**: `projects/cesta/pipeline.py:50`:

```python
def _cargar_bronze() -> pl.DataFrame | None:
    """Une todos los parquet de bronze aunque tengan columnas distintas."""
```

> **«Todos los parquet de bronze.»** *No una lista de cinco fuentes: **todos**.* **Asi que Lidl entra por
> donde tienen que entrar todas** -- *y no hay que tocar el pipeline para que lo vea.*

## 3. Y esto es lo que hace falta comprobar al correrlo, no antes

*Correr el pipeline es la accion siguiente, y tiene dos desenlaces posibles, y los dos hay que saber leerlos:*

  1. **Sale `fuente=lidl` en silver y aparece en `/api/estado` con `productos` y `al_dia`.** *Entonces el
     recorrido esta hecho, y lo que queda es la interfaz.*
  2. **No sale.** *Y entonces la causa sera **el esquema**: `a_silver` espera unas columnas, y el bronze de
     Lidl las trae o no las trae.* **Y eso se vera en el error, no se supone.**

> *Y no se puede adelantar el diagnostico*: **lo que hay que hacer es correrlo y leer lo que diga.** *Que es la
> misma regla de siempre, aplicada al pipeline en vez de a un colector.*

## 4. Y una cosa que **no** va a pasar, y conviene decirla

**Lidl no va a aparecer como una sexta cadena «igual que las otras».** *Aunque su silver salga bien:*

  - **`CADENAS` sigue teniendo cinco**, *porque es la lista de las que **cierran una cesta***.
  - **y `/api/estado` da `productos` por cadena** -- *y los de Lidl seran **79 fichas de ofertas semanales**,
    no un catalogo.* **Poner ese numero al lado de los 22 816 de Alcampo sin decir que significa otra cosa
    seria la mentira que `cesta.py` lleva todo este tiempo evitando.**

> **Asi que cuando Lidl aparezca, tendra que aparecer **con su cobertura**: `ofertas_semanales_parcial`,
> `con_precio: 77` de `79`, y su `aviso`.** *No vale que sea «una cadena mas» en una lista de numeros.*
