# B13 · **PASO 2, concluyente**: `crea_usuario` **solo** escribe en `usuario` -- y su docstring dice la regla

*(13 de octubre de 2026. **Cuarta ronda de B13. Y el paso previo da luz verde, con tres comprobaciones.**)*

## 1. El cuerpo, literal (`plataforma/api/almacen.py:159`)

```python
def crea_usuario(usuario: str, nombre: str, clave: str) -> dict:
    """Da de alta a una persona. El nombre repetido sale por su propia puerta.

    `UsuarioRepetido` en vez de dejar subir el error de PostgreSQL: quien llama
    tiene que poder decirle a la persona "ese nombre ya esta cogido" sin leer el
    texto de una restriccion de la base de datos, que es un detalle del esquema
    y cambia sin avisar.
    """
    try:
        with cursor() as cur:
            cur.execute("""
                INSERT INTO usuario (usuario, nombre, clave_hash) VALUES (%s, %s, %s)
                RETURNING id, usuario, nombre
            """, (usuario.strip().lower(), nombre.strip(), _hasher.hash(clave)))
            return cur.fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise UsuarioRepetido(usuario.strip().lower()) from exc
```

## 2. Y contesta **las tres cosas** del paso 2

```
PASO 2 PEDIA:  «confirmar que SOLO INSERTA EN `usuario` y NO ESCRIBE EN `lista`, `lista_linea`,
               `entrada` NI `compra`»

  *** UN SOLO `INSERT`, Y EN `usuario`. ***  *Ni un `UPDATE`, ni un `DELETE`, ni otra tabla.*
  *** `usuario.strip().lower()` *** -- *normalizado: `Prueba` y `prueba` son el MISMO usuario.*
  *** `_hasher.hash(clave)` *** -- *la clave se guarda **derivada**, nunca en claro.*
  *** Y `RETURNING id, usuario, nombre` *** -- *devuelve **lo justo**: ni el hash.*
```

> *** O sea: **el paso 2 da luz verde, y ademas dice tres cosas que no se habian pedido**: ***
>   - **el nombre se normaliza** *- asi que **no se pueden crear dos usuarios que se diferencien en mayusculas**;*
>   - **la clave no se guarda** *- se guarda **su hash**;*
>   - **y lo que devuelve no incluye el hash** *- **ni siquiera a quien lo crea.** *

## 3. Y su docstring es **la doctrina, vigesimotercera vez** -- y cierra una serie de **tres**

> *** «`UsuarioRepetido` en vez de dejar subir el error de PostgreSQL: quien llama tiene que poder decirle a la
> persona "ese nombre ya esta cogido" *** SIN LEER EL TEXTO DE UNA RESTRICCION DE LA BASE DE DATOS, QUE ES UN DETALLE
> DEL ESQUEMA Y CAMBIA SIN AVISAR. ***» ***
>
> *** Y ese motivo -- «**un detalle que cambia sin avisar**» -- **es la tercera vez que aparece, y las tres son la
> misma leccion**: ***
>
> ```
> B03 / B09:  «no modificar grupos historicos POR ORDINAL»
>             -> *** no depender de la POSICION: *las columnas se anaden, y el ordinal cambia. ***
> B10:        «`momento` es la hora del MOVIL, no la de llegada»
>             -> *** no depender del RELOJ: *el mensaje llega cuando llega, y el orden se inventaria. ***
> B13:        «no leer el texto de una restriccion de la base de datos, QUE ES UN DETALLE DEL ESQUEMA»
>             -> *** no depender del TEXTO de un error: *PostgreSQL lo puede cambiar en una version. ***
> ```
>
> *** LAS TRES DICEN LO MISMO, CON TRES COSAS DISTINTAS: *** *** no te apoyes en algo que **no controlas** y que
> **puede cambiar sin avisarte.** ***
>
> *** Y las tres tienen **la misma solucion**: *** *traducir el fallo a **una puerta propia** -- *`UsuarioRepetido`,
> `estabiliza`, `GREATEST` -- *o sea: **el codigo del proyecto decide, y no la posicion, ni el reloj, ni el texto de
> un error ajeno.** *

## 4. Y lo que esto significa para el paso 3

```
PASO 3 (corregido en la ronda 186):  *** usar los 38 usuarios que YA HAY ***
   -> y `prueba` y `prueba-navegador` son los mas genericos
   -> *** y ahora se sabe que crearlos seria INOFENSIVO (un solo INSERT, y `UsuarioRepetido` si ya estan) ***
      *-- o sea: **el paso 2 confirma que el 3 no podia hacer daño**, y **el 1 dijo que no hace falta.** *
```

> *** Y las dos cosas juntas son **el valor del orden de los pasos**: *** *el **1** evito **crear de mas**, y el **2**
> confirma **que no habria hecho daño** -- *o sea: **si el 1 hubiera faltado, el 2 lo habria cubierto**; *y **si el 2
> hubiera faltado, el 1 lo habria evitado.** *
>
> *** Tener los dos es lo que convierte «creo que es seguro» en «**esta comprobado**». ***
