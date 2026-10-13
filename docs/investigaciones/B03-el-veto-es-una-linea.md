# B03 · **El veto es UNA linea, y el motivo es codigo muerto**

*(13 de octubre de 2026. **Se buscaba donde Lidl pierde las comparaciones, y no pierde ninguna: pierde un
boton.**)*

## 1. El veto, medido: **una linea**

*`CADENAS` se usa en **un solo sitio** de todo el codigo de produccion. En `plataforma/api/main.py:771`:*

```python
@app.post("/api/listas/{lista_id}/tienda")
def en_tienda(lista_id: str, datos: EnTienda, usuario: dict = Depends(usuario_actual)):
    """Elegir tienda: para una linea, para toda la lista o para borrar la sublista.

    Es la operacion que pidio el dueno: *"en la lista poder elegir en que supermercado
    lo quiero comprar..."*."""
    ...
    if datos.cadena is not None and datos.cadena not in cesta.CADENAS:
        raise HTTPException(422, f"'{datos.cadena}' no es una de las cadenas: {', '.join(cesta.CADENAS)}")
```

> **Asi que `CADENAS` no es «la lista de las que se pueden comparar»: es la lista de las que se pueden
> ELEGIR AL COMPRAR.** *Y el veto real de Lidl no esta en ninguna comparacion de precios -- **esta en que no
> se puede decir «esta linea la compro en Lidl».***

**Y eso es mas grave de lo que parecia, no menos**: *no es que Lidl pierda una comparacion; es que **una
persona que vaya a comprar a Lidl no puede asignarle ni una linea**, aunque el precio de esa linea **si se
haya capturado y sea valido**.* **Que es exactamente lo que B03 pide quitar**: *«Lidl **si puede ofrecer una
linea exacta con precio valido**».*

## 2. Y el motivo existe, esta probado, y **no llega a nadie**

```python
def por_que_no_se_compara(cadena: str) -> str | None:
    """...**Existe para que la pantalla pueda decir por que falta una cadena**, en vez de dejarla
    simplemente ausente."""
```

*Y quien la llama:*

```
plataforma/api/cesta.py:53     <- la definicion
tests/test_revision_a05_lidl.py:61, 70, 78   <- y NADA MAS
```

> **Ni una llamada desde produccion. Ni una mencion en el frontend.** *Asi que la funcion que existe **para
> que la pantalla explique** por que falta Lidl **no la llama ninguna pantalla.***

**Es codigo muerto con una prueba que pasa.** *Y eso es peor que no tenerlo*: *una prueba verde sobre
`por_que_no_se_compara` hace parecer que la explicacion esta puesta*, **y lo que esta puesto es la funcion,
no el uso.**

> *Es la misma clase de hueco que el `grupo_id` que se nombraba y no se leia, y que el `de_dondo` que se
> suponia.* **Tercera vez en este paquete: algo que existe, se prueba, y no llega.**

## 3. Asi que B03, en su parte de API y UI, son **dos cosas pequeñas y concretas**

  (1) **`en_tienda` tiene que admitir `lidl` cuando la linea tenga un precio observado, vigente y de identidad
      acreditada.** *No «admitir lidl» y ya: **admitirlo por linea**, que es la regla fina que el plan pide.*
  (2) **Y `por_que_no_se_compara` tiene que llamarse de verdad**, *para que la pantalla diga por que falta una
      cadena y **por que una linea concreta es desconocida en vez de ausente**.*

**Y las dos tienen la misma forma**: *no anadir una cadena a una lista, sino **decidir por linea y decirlo**.*

## 4. Y lo que NO hay que tocar

**La comprobacion de importacion** (`cesta.py:68`):

```python
if __name__ != "__main__":
    # **Una comprobacion al importar, y es barata**: *la lista comparable tiene que estar DENTRO de la...*
```

*Esa guarda **sigue teniendo sentido***: *la lista de las que se pueden comparar **tiene que estar dentro** de
las capturadas.* **Lo que cambia no es la relacion entre las dos listas, sino QUIEN las usa y para que** --
*`CADENAS` deja de ser un portero de `en_tienda`, y pasa a ser, con la cobertura delante, la lista de las que
pueden cerrar una cesta.*

> **Y asi las dos frases conviven**: *Lidl **puede ganar una linea** (por candidato, con precio observado) y
> **no puede cerrar una cesta** (porque su catalogo es parcial).* **Que es lo que el plan pide, y lo que
> `cesta.py` protegia con su motivo.**
