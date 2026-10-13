# B08 · **`apunta` rechaza `compra` a proposito** -- con su motivo, y **con las dos idempotencias**

*(13 de octubre de 2026. **Cuarta ronda de B08. Y la restriccion del propietario esta en la firma.**)*

## 1. La firma y el docstring, literales (`diario.py:131`)

```python
def apunta(con: sqlite3.Connection, propietario: str, fecha: str, comida: str, *,
           clave_operacion: str | None = None,
           tipo: str = ALIMENTO, referencia: str | None = None, version: str | None = None,
           cantidad_g: float | None = None, kcal: float | None = None,
           proteinas_g: float | None = None, grasas_g: float | None = None,
           hidratos_g: float | None = None, fuente_dato: str = DESCONOCIDO, nota: str = "",
           ahora: datetime | None = None) -> int:
    """Anota lo que se comio **para quien lo anota**.

    **Rechaza `compra` a proposito.** Comprar no es comer: si una compra entrara aqui, el di[ario
    diria que se ha] comido algo que quiza ni se ha abierto.
    """
    if not propietario:
        raise ValueError("una entrada necesita dueno: el diario es personal")
    if tipo not in TIPOS:
        ...
```

## 2. Y la restriccion del propietario **esta en el codigo, con su motivo**

```
RESTRICCION DEL PROPIETARIO:  «Compra no es consumo.»
   -> *** «RECHAZA `compra` A PROPOSITO. Comprar no es comer: si una compra entrara aqui, el diario
       diria que se ha comido algo que quiza ni se ha abierto.» ***
```

> *** Y el motivo es **el bueno**, y no es «no se debe»: *** *es que **el diario mentiria** -- *«diria que se ha
> comido algo **que quiza ni se ha abierto**».*
>
> *** O sea: **no es una regla de estilo: es que el dato seria falso** *** -- *y **por eso se rechaza**, y **por eso
> hay un ensayo** (`test_una_compra_no_es_consumo`).*
>
> *** Y es **la septima forma de imposibilidad** de la sesion, y la primera **en voz activa**: *** *las otras seis eran
> ausencias (clave, lista vacia, import); **esta es un `raise`** -- *o sea: **alguien lo intento, y el codigo lo dice
> en la cara**.*

## 3. Y tiene **las dos idempotencias**, no una

```
clave_operacion: str | None = None        <- *** la clave POR OPERACION, como B05 ***
_el_mismo_reintento(previa, contenido)     <- *** y la comparacion POR CONTENIDO ***
```

> *** O sea: `diario.apunta` tiene **las dos** -- *** *y eso **contesta** la clausula (2) de B05 **de la forma
> completa**:*
>
>   - **si viene `clave_operacion`**, *la identidad es **de la operacion** -- *repetirla **no duplica**, y **otra
>     distinta, si**;*
>   - **y si no viene**, *se compara **el contenido** -- *`_el_mismo_reintento(previa, contenido)`.*
>
> *** Que es exactamente lo que hacen falta **las dos** para: ***
>
>   - **`test_la_misma_operacion_dos_veces_no_duplica`** *-- la clave;*
>   - **`test_dos_operaciones_distintas_con_lo_mismo_son_dos`** *-- y por eso **la clave no puede ser el
>     contenido**: dos operaciones distintas con lo mismo **son dos**;*
>   - **`test_sin_clave_sigue_funcionando_como_antes`** *-- y **sin clave, el contenido**;*
>   - **`test_la_clave_no_cruza_entre_personas`** *-- y la clave **lleva el propietario dentro**.*
>
> *** Los cuatro ensayos que se leyeron en la ronda 151 **encajan en la firma**, y **ahora se sabe por que son
> cuatro y no uno**.* ***

## 4. Y la firma dice **que se guarda**, que es el snapshot

```
referencia: str | None      <- el id de la receta o del alimento
version: str | None         <- *** LA VERSION ***
cantidad_g: float | None    <- *** la porcion EFECTIVA ***
kcal · proteinas_g · grasas_g · hidratos_g   <- *** LOS CUATRO MACROS, y todos `None` por defecto ***
fuente_dato: str = DESCONOCIDO                <- *** y por defecto, `DESCONOCIDO` ***
```

> *** Y **todos los nutrientes son `float | None` con defecto `None`** *** -- *o sea: **se puede apuntar una comida
> sin saber sus kcal**, *y **queda dicho** (`fuente_dato = DESCONOCIDO`).*
>
> *** Que es **el caso de la aceptacion**: *** *«ausencia de energia con proteina conocida» -- *hay
> `proteinas_g`, **no hay `kcal`**, y **las dos cosas caben en la misma fila**.*
>
> *** Y el defecto de `fuente_dato` es `DESCONOCIDO`, no `ETIQUETA` ni `FICHA`: *** *si no se dice de donde sale,
> **se guarda que no se sabe** -- *que es **la doctrina, en un valor por defecto.***

## 5. Y B08, con cuatro rondas, tiene **la mitad del paquete**

```
  1) PREVISTO != REGISTRADO    *** POR MIRAR *** -- `plataforma/api/diario.py` (la vista de previstos)
  2) QUE SE CONFIRMA Y CON QUE HECHO -- `de_ficha` (snapshot) y `_cobertura`
  3) EL RECIBO Y SU DESHACER   HECHO -- `apunta` y `borrar(con, propietario, entrada_id)`
  4) EL OBJETIVO Y LAS GRAFICAS *** POR MIRAR *** -- no esta en `diario.py`
  5) Y LA ACEPTACION           LOCALIZADA -- los quince ensayos, leidos por su nombre
```

> *** Y las dos «por mirar» son **la misma capa**: *** *la **vista** -- *previstos, objetivo, graficas.*
> *** Que es **`plataforma/api/diario.py` y el frontend**, no el modulo que guarda.** ***
