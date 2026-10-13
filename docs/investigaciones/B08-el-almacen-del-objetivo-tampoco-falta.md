# B08 · **El almacen del objetivo TAMPOCO falta**: `preferencias_de` y `guarda_preferencia` ya existen

*(13 de octubre de 2026. **Y con eso, el objetivo opcional es una ruta de paso, no una construccion.**)*

## 1. Las dos funciones, literales (`plataforma/api/almacen.py`)

```
l1030  *** def preferencias_de(usuario_id: str) -> dict: *** *
l1032      cur.execute("SELECT clave, valor FROM preferencia WHERE usuario_id = %s", (usuario_id,))
           *** -> y devuelve el diccionario `clave -> valor` del usuario *** *

l1036  *** def guarda_preferencia(usuario_id: str, clave: str, valor: Any) -> None: *** *
l1039      cur.execute("""INSERT INTO preferencia (usuario_id, clave, valor) VALUES (%s, %s, %s) ...
           *** -> y los tres campos son exactamente los de la tabla: `usuario_id`, `clave`, `valor` *** *
```

## 2. *** Y con eso, el objetivo es **una clave y una llamada** ***

```
*** GUARDAR el objetivo de una persona para un dia: ***
   `guarda_preferencia(usuario_id, *** f"objetivo:{fecha}" ***, *** {"kcal": 2000} ***)`
   *** -> y no hay que tocar el esquema, ni anadir una tabla, ni escribir un `INSERT`. *** *

*** LEER los objetivos de una persona: ***
   `preferencias_de(usuario_id)` -> *y **filtrar las claves que empiezan por `"objetivo:"`** *
   *** -> y el resto de claves se quedan donde estan, que es lo que hace que sea UNA tabla de preferencias
      y no una tabla por cada cosa. *** *
```

> *** O sea: *** *** **el objetivo opcional es una preferencia mas**, *y **el proyecto ya tiene el
> mecanismo.** *
>
> *** Y **las cuatro piezas de B08 quedan asi**: ***
> ```
> *** 1. la vista de previstos ***     -> *** HECHA *** *(`GET /api/recetas/plan/prevision`, 200)*
> *** 2. su ensayo ***                 -> *** HECHO *** *(8 ensayos: 2025 -> 2033)*
> *** 3. el objetivo: el sitio ***      -> *** `preferencia`, sin migracion *** ✓
> ***    y el almacen ***               -> *** `preferencias_de` y `guarda_preferencia` *** ✓
> *** 4. *** LAS GRAFICAS DE LOS TRES *** ***  -> *y `chispa.ts` **ya tiene sus tres reglas** *
> ```
>
> *** -> y **lo que queda es una RUTA que use las dos funciones**, *y **la vista de las tres series.** *

## 3. Y **el limite de B08, dicho otra vez y sin adorno**

```
*** LO QUE NO SE PUEDE HACER, y el encargo lo prohibe: ***
  *** inventar el VALOR del objetivo *** *-- «no inventes... objetivos de salud»*
  *** -> y por eso la ruta guarda EL QUE ESCRIBA LA PERSONA, y si no hay, devuelve que no hay. *** *
     *No un 2.000 por defecto. *No un «recomendado». *No un calculo por edad o peso.*

*** Y LA CONSECUENCIA, que es la correcta: ***
  *** sin objetivo, la grafica tiene DOS series (registrado y previsto), y NO TRES *** *
  *** -> y eso no es una carencia: es lo que hay, dicho. *** *
```

> *** Y **es la misma doctrina de siempre, en el ultimo sitio donde aparece**: *** *`null` y no cero, *
> *`ABSTIENE` y no una suposicion, *`sin_catalogo` y no un producto inventado, *
> *** y ahora: `sin_objetivo` y no un 2.000 por defecto.** *

## 4. Y el estado, con **el objetivo a una ruta de distancia**

```
*** B08 · lo que queda, y ya con todo localizado: ***
  *** a) LA RUTA DEL OBJETIVO ***   -> *`GET` y `POST`, usando `preferencias_de` y `guarda_preferencia`*
     *con la clave `"objetivo:<fecha>"`, y el valor `{"kcal": N}` como jsonb*
  *** b) Y LA VISTA DE LAS TRES SERIES *** -> *y `chispa.ts` **ya tiene las reglas**: *
     *«lo que no se observo **no se puede dibujar como si se hubiera observado**»*
  *** c) y el paso 3 del enlace *** -> *`cesta.py:184`: la columna la escribe `emparejar.py`,
     *y «ese fichero no la tiene todavia» -- *y **el dia que la escriba, «llega sola».** *
```

> *** Y **ninguna de las tres exige inventar un dato**, *ni decidir donde vive algo: *
> *** la tabla existe, el almacen existe, la grafica tiene sus reglas, y el valor lo pone la persona. *** *
