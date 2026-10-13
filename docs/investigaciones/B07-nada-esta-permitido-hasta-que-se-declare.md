# B07 · **`importar_receta.py`**: «nada esta permitido hasta que se declare» -- y la lista **empieza vacia**

*(13 de octubre de 2026. **Cuarta ronda de B07. Y la clausula con mas guardas tiene su razon escrita.**)*

## 1. Lo que hay: 337 lineas, y los nombres

```
core/importar_receta.py -- 337 lineas

  l45:  ESQUEMAS = ("http", "https", "file")
  l49:  class Permiso
  l63:  def fuentes_permitidas() -> dict[str, str]
  l68:  def comprueba_fuente(url: str | None) -> Permiso
  l110: class Borrador
  l132: def borrador(url: str | None, campos: dict | None = None) -> tuple[Permiso, Borrador]
  l233: def campos_de_json_ld(datos) -> dict | None
  l289: def _parte_cantidad(texto) -> tuple[float | None, str | None]
  l305: def _minutos_iso(v) -> int | None
  l317: def lee_json_ld(html: str) -> dict | None
```

## 2. Y su docstring es **la decision**, no la descripcion

```python
"""F09 / `R02`: **la fuente permitida** -- la primera mitad del importar recetas.

El criterio dice, y **empieza por aqui**:

> **URL/archivo de fuente permitida**; previa, **fuente**, unidades y edicion antes de guard[ar]

**Y medido el 11 de octubre de 2026**, importar [no tenia] ni ruta, ni pantalla, ni `fuente` de receta.

## Y lo primero que hay que escribir no es el lector: es **a quien se le puede leer**

**«Fuente permitida» no es un detalle del lector: es la PRIMERA cosa que el criterio nombra**, [y]
decide **si el lector se puede escribir**. *Bajarse una receta de un sitio que no lo permite no es un
problema tecnico: es el problema.*

**Y por eso este modulo no lleva la lista: lleva el MECANISMO**, y la lista `FUENTES` **empieza vacia**.

> **Nada esta permitido hasta que se declare.** *Un importador que por defecto acepta cualquier cosa
> no tiene politica de fuentes: tiene la politica de que **todo vale**, escrita en ningun sitio.*

**Es la misma disciplina que `diario.FUENTES`** (*cuatro valores, y una quinta es un `raise`*) [y que]
`_acceso`: *la regla **no se deja al cuidado de quien escribe** -- *se pone en el camino.*
"""
```

## 3. Y contesta la clausula (2) de B07 -- la de las guardas

```
B07 PIDE                                            Y AQUI ESTA
  «URL SOLO FUENTES REVISADAS»                        *** `comprueba_fuente(url) -> Permiso` ***
                                                      y *** `FUENTES` EMPIEZA VACIA ***
  «guardas SSRF / redirecciones / TAMANO / TIMEOUT»    `ESQUEMAS = ("http", "https", "file")` -- el
                                                      esquema se comprueba; *y el resto, POR MIRAR
                                                      (no se ha leido el cuerpo de `comprueba_fuente`)*
  «Y ATRIBUCION»                                       *POR MIRAR*
  «previa ... antes de guardar»                        *** `class Borrador` + `borrador()` -- LA PREVIA ***
```

> *** Y la frase que hay que subrayar es la del defecto: ***
>
> *«Un importador que **por defecto acepta cualquier cosa** no tiene politica de fuentes: **tiene la politica de
> que todo vale, escrita en ningun sitio.**»*
>
> *** O sea: **no decidir es decidir** -- *y decidir «todo vale» **sin escribirlo** es **peor** que escribirlo,
> porque **parece que no hay decision**.*
>
> *Y la solucion que el proyecto elige es **la fuerte**: **la lista empieza vacia**. *No «hay que revisar las
> fuentes»: **no hay ninguna hasta que se declare una**.*
>
> *** Que es **la misma doctrina** que `FUENTES` en `diario.py` y que `_acceso` -- **y el propio docstring lo dice**:
> *«la regla **no se deja al cuidado de quien escribe**: **se pone en el camino**».*
>
> *** La forma fuerte de una regla: no una promesa, una imposibilidad. *** *Que es **la cuarta vez** en esta
> sesion: `id uuid PRIMARY KEY`, `fuente_dato NOT NULL`, `ON CONFLICT`, y ahora **una lista vacia**.*

## 4. Y hay un dato de proceso, otra vez

**«Medido el 11 de octubre de 2026..., importar [no tenia] ni ruta, ni pantalla, ni `fuente` de receta -- el campo
`fuente` que hay es DEL INGREDIENTE.»**

> *** O sea: **habia un campo `fuente`, y no era el de la receta** *** -- *y **eso es exactamente el error que
> `B04` encontro con `cadena` vs `fuente`**: «la alternativa la llama `fuente` ... **y leer solo `cadena` fue mi
> error**» (esta escrito en `cesta.py:1168`).*
>
> *** Dos sitios distintos, el mismo tipo de confusion: **un nombre que parece el que buscas y no lo es**. ***

## 5. Y B07, con cuatro rondas

```
  1) EL EDITOR DE RECETA    LOCALIZADO -- `test_editar_receta.py` (formulario, cantidad, version)
  2) LA IMPORTACION         *** EL MECANISMO LEIDO: *** `comprueba_fuente` + `FUENTES` vacia +
                            `Borrador` (la previa) + `lee_json_ld`. *Faltan las guardas concretas:
                            SSRF, redirecciones, tamano, timeout, atribucion -- POR MIRAR en el cuerpo*
  3) EL PLAN                *** POR MIRAR ***
  4) LA COCINA              `cocina.py` leido (el temporizador como hora de fin); «sin declarar consumo» POR MIRAR
  5) Y LA VERSION           CON ENSAYO
  6) Y LA ACEPTACION        «CINCO RECETAS CON DATOS ... y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS»
```

> *** Y la (2) esta a medias **a proposito**: *** *se ha leido **el mecanismo** -- *que es **la mitad que el
> propio docstring dice que no se puede equivocar*** -- *y **las guardas concretas no**, porque **estan en el
> cuerpo de `comprueba_fuente`** (l68-110), y **no se ha abierto**.*
>
> *** Y decirlo asi es la diferencia entre «leido» y «supuesto». ***
