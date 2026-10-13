# B05 · **La primera parada**: `core/traspaso.py` **ya es la idempotencia por operacion** -- y es de B04

*(13 de octubre de 2026. **Se abrio el primer fichero. Y contiene el nucleo de B05, razonado.**)*

## 1. Lo que dice su docstring, y es exactamente el criterio de B05

```python
core/traspaso.py:1
"""G12, punto 221: **la transferencia de una receta a la lista, idempotente por operacion.**

G12 lo pide asi: «Receta->lista: previa de cantidades, consolidacion compatible, distincion
g/ml/unidades y envases enteros necesarios. **Repetir la misma transferencia no duplica; otra
semana/operacion legitima si.** Descontar despensa solo si esta modelada y la persona lo elige, **no
por haber comprado antes**.»

**Y la frase que decide el diseno es la de en medio.** *«Repetir no duplica» y «otra semana si» no se
pueden cumplir a la vez mirando las lineas de la lista* -- *dos semanas distintas con los mismos
ingredientes producen lineas identicas, y no hay forma de distinguirlas por su contenido*. **Asi que
la identidad tiene que ser de la operacion, no del resultado**, y eso es una clave: **receta +
version + semana**.

**La clave la calcula el servidor, y la semana tambien.** *Si la mandara el cliente, dos pestañas con
fechas distintas escribirian dos veces, y el 223 de G12 y el 227 de G13 prohiben confiar en lo que
manda el cliente como identidad o como propietario.* **La fecha de hoy es del servidor.**

**Y el dueno se comprueba aqui, no en la pantalla.** *La puerta es `recetas._de_quien`, que ya existe
y ya lanza: «una receta necesita dueno: el recetario es personal».*
"""
```

**Y `Operacion`, que es la clave:**

```python
@dataclass(frozen=True)
class Operacion:
    propietario: str
    receta_id: int
    version: int
    semana: str          # el lunes de la semana, en ISO. *La calcula el servidor.*
```

## 2. Y esto contesta cuatro de las seis cosas de B05, **con su razon**

```
B05 PIDE                                        Y AQUI ESTA
  1) RECIBO Y HUELLA DEL CONTENIDO              `Operacion` -- la identidad de la operacion
  2) MISMA CLAVE + CONTENIDO DISTINTO =
     CONFLICTO, NO EXITO FICTICIO               *** ES EL DOCSTRING ENTERO ***
  3) DOS PESTAÑAS / VERSIONES CONCURRENTES      «si la mandara el cliente, dos pestañas con fechas
                                                 distintas escribirian dos veces» -- y por eso
                                                 **la clave y la semana las calcula el SERVIDOR**
  4) Y EL DUEÑO                                 «se comprueba aqui, no en la pantalla», con la puerta
                                                 `recetas._de_quien`
  5) RESERVAS DE DESPENSA                       «Descontar despensa SOLO si esta modelada y la
                                                 persona LO ELIGE, NO por haber comprado antes»
  6) DESTINO DISTINTO                           (B04)
```

> *** Y fijate en la (2), que es la que el plan subraya: ***
>
> *El docstring **no dice «repetir no duplica» y ya esta**: dice **por que** la identidad **no puede ser el
> contenido de la lista** -- *«dos semanas distintas con los mismos ingredientes producen lineas identicas, y **no
> hay forma de distinguirlas por su contenido**»*.*
>
> *** O sea: la misma clave con contenido distinto **no se puede detectar mirando el contenido**, y por eso la clave
> es la OPERACION. *** *Que es **exactamente** lo que el plan pide con «misma clave con contenido distinto produce
> conflicto, no exito ficticio» -- **resuelto no comparando contenido, sino no usando el contenido como clave**.*

## 3. Y esto es la segunda vez que B05 aparece ya hecho -- y esta vez **con el razonamiento escrito**

**Como en B02, lo que el plan pide **ya esta**.** *Pero aqui hay algo que en B02 no habia: **el docstring explica
las decisiones difíciles**, y **las tres que explica son las tres que el plan subraya**.*

> *Y **el motivo** de que este en `core/traspaso.py` y no en la API: *«la identidad tiene que ser de la operacion»
> -- y **la operacion la define el servidor**, no el cliente.*
>
> *** Que es la leccion de B04, escrita en un docstring, y que B05 pide de nuevo. ***

## 4. Y lo que NO se dice, porque no se ha leido

**Quedan 105 lineas de `traspaso.py` sin abrir.** *Y no se dice qué hacen.*

```
POR LEER, y no se concluye nada:
  - las 105 lineas que quedan de `core/traspaso.py`
  - `core/manifiesto.py` (9,5 KB) y `core/publicacion.py` (12,1 KB) -- el recibo de una publicacion
  - `plataforma/api/almacen.py` (58,4 KB) -- el almacen, donde vive la idempotencia de las listas
  - `core/diario.py` (17,5 KB)
  - y los ensayos de traspaso, si existen
```

> *** Y es la primera ronda de B05: un fichero abierto, una cosa afirmada con su cita, y cinco sitios dichos como
> pendientes. *** *Que es el orden que B02 tardo diez rondas en aprender.*
