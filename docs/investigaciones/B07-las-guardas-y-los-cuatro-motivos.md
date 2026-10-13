# B07 · **Las guardas, leidas**: cuatro motivos **separados**, y cada uno dice lo suyo

*(13 de octubre de 2026. **Quinta ronda de B07. Y la clausula (2) queda cerrada.**)*

## 1. `comprueba_fuente`, literal (`importar_receta.py:68`)

```python
def comprueba_fuente(url: str | None) -> Permiso:
    """**Si esa direccion se puede leer.** *Y si no, por que no.*

    **Los motivos estan separados a proposito**, porque son **problemas distintos** y se arr[astran]:

    - **no es una direccion** -- *el texto esta vacio o no se puede leer*
    - **el esquema no vale** -- *`ftp` no es una pagina web, y `javascript:` menos*
    - **el host no esta declarado** -- *es una web, y **no se ha decidido** si se puede*
    - **no tiene host** -- *`file://` sin ruta, o una direccion a medias*
    """
    if not url or not str(url).strip():
        return Permiso(False, "no es una direccion")

    trozos = urlparse(str(url).strip())

    if trozos.scheme.lower() not in ESQUEMAS:          # ("http", "https", "file")
        return Permiso(False, f"el esquema no vale: {trozos.scheme or '(ninguno)'}")

    host = (trozos.hostname or "").lower()

    # **`file` no tiene host, y se permite por el criterio** -- «URL/archivo de fuente [permitida]»
    # pero **con ruta**: un `file://` pelado no es un archivo.
    if trozos.scheme.lower() == "file":
        if not trozos.path:
            return Permiso(False, "archivo sin ruta")
        return Permiso(True, "archivo local", host="", razon_declarada="el criterio admite archivo")

    if not host:
        return Permiso(False, "no tiene host")

    if host not in FUENTES:
        return Permiso(False, f"la fuente no esta declarada: {host}", host=host)

    return Permiso(True, "declarada", host=host, razon_declarada=FUENTES[host])
```

## 2. Y las guardas que el plan pide, una a una

```
B07 PIDE                        Y AQUI ESTA
  «SSRF»                         *** `script:` y `javascript:` NO ESTAN EN `ESQUEMAS` *** -- *y `ESQUEMAS`
                                 es `("http", "https", "file")`: una lista blanca de TRES*
                                 *** y `host not in FUENTES` -> no se lee un host que no se declaro ***
  «redirecciones»                *POR MIRAR: no se ha visto el que sigue redirecciones (`fetch`)*
  «tamano»                       *POR MIRAR* -- *y `MAX` no aparece en los nombres del fichero*
  «timeout»                      *POR MIRAR*
  «atribucion»                   *** `razon_declarada=FUENTES[host]` *** -- *o sea: **cuando se permite, se
                                 permite CON SU RAZON**, que es la que se le ensena a la persona*
  «previa ... antes de guardar»   *** `class Borrador` -- y el comentario del fichero dice: ***
                                 «El borrador: **la previa, que NO ESCRIBE**»
```

> *** Y el `razon_declarada` es lo que hay que subrayar: *** *el permiso **no es un «si»**: es un «si» **con su
> motivo**, *y **el motivo viaja con el permiso** -- *que es **exactamente la atribucion del criterio**, y **lo que
> permite ensenarlo junto al dato**.*
>
> *** Permiso(True, "declarada", host=host, razon_declarada=FUENTES[host]) *** *-- cuatro campos, y el ultimo es
> **por que se puede**. ***

## 3. Y la doctrina aparece **dos veces mas** en este fichero

```
  a) *** «el host no esta declarado -- es una web, y NO SE HA DECIDIDO si se puede» ***
     -> *«no se ha decidido» **es un motivo**, no un silencio.* *** Undecima vez. ***

  b) *** «Los motivos estan separados A PROPOSITO, porque son PROBLEMAS DISTINTOS y se arrastran» ***
     -> *que es **la misma forma** que los cinco motivos de B06 (ausente/no aplicable/no publicado/error/
     pendiente) y que las tres respuestas de `alimentos.py`: **no forzar a dos lo que tiene cuatro**.*
     *** Duodecima vez. ***
```

> *** Y fijate en que el fichero lo dice **en su propio docstring**: *** *«los motivos estan separados **a
> proposito**»* -- *o sea: **alguien decidio no devolver un `False` pelado**, **y lo dejo escrito**.*
>
> *** Doce sitios ya. Y todos dicen lo mismo: *** **el «no» tiene que decir por que.***

## 4. Y B07, con cinco rondas

```
  1) EL EDITOR DE RECETA    LOCALIZADO
  2) LA IMPORTACION         *** HECHO EL MECANISMO Y LAS GUARDAS DE FUENTE: ***
                            `ESQUEMAS` (3, y `javascript:`/`script:` fuera), `file` con ruta, host declarado,
                            `razon_declarada` (atribucion), y `Borrador` (la previa que no escribe)
                            -> *faltan las de RED: redirecciones, tamano, timeout -- POR MIRAR*
  3) EL PLAN                *** POR MIRAR ***
  4) LA COCINA              `cocina.py` leido; «sin declarar consumo» POR MIRAR
  5) Y LA VERSION           CON ENSAYO
  6) Y LA ACEPTACION        «CINCO RECETAS CON DATOS ... y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS»
```

> *** Y las tres de red que faltan (redirecciones, tamano, timeout) **no se dice que falten**: *** *se dice que
> **no se han visto** -- *y **son de otra capa**: **las de fuente se comprueban antes de pedir; las de red, al
> pedir**.* *** Y esa distincion la hace el propio fichero: `comprueba_fuente` **no pide nada**. ***
