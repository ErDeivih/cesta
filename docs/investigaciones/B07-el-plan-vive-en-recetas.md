# B07 · **El plan vive en `core/recetas.py`** -- y `escala` es la de «raciones por ocurrencia»

*(13 de octubre de 2026. **Septima ronda de B07. Y la ultima clausula queda localizada.**)*

## 1. Lo que hay, por sus nombres

```
core/recetas.py

  l57:  def _migra(con) -> None                              <- hay tabla, y se migra
  l102: def _de_quien(con, propietario, receta_id)           <- LA PUERTA DEL DUEÑO
  l110: def crear(con, propietario, nombre, raciones, ...)
  l134: *** def escala(ingredientes, de_raciones, a_raciones) ***   <- «RACIONES POR OCURRENCIA»
  l157: def leer(con, propietario, receta_id, ...)
  l189: *** def versiones(con, propietario, receta_id) ***          <- LA VERSION
  l197: def actualizar(con, propietario, receta_id, *, ...)         <- editar
  l227: def listar(con, propietario, ...)
  l244: def archivar(con, propietario, receta_id, ...)
  l253: *** def planificar(con, propietario, fecha, receta...) ***  <- EL PLAN
  l267: *** def plan(con, propietario, desde, hasta) ***            <- y por rango de fechas
  l278: def quitar_del_plan(con, propietario, fecha, r...)          <- lo que B04 toco
```

## 2. Y contesta las clausulas que faltaban de B07

```
B07 PIDE                                        Y AQUI ESTA
  «PLAN con VARIAS COMIDAS POR DIA»               *** `plan(con, propietario, desde, hasta)` ***
                                                  *-- «desde» y «hasta»: **un rango**, no un dia suelto*
  «repetir/duplicar SEMANA»                       *** POR MIRAR *** -- *no aparece en los nombres; puede
                                                  ser cosa de la API o de la pantalla*
  «RACIONES POR OCURRENCIA»                       *** `escala(ingredientes, de_raciones, a_raciones)` ***
                                                  *-- y **`de_raciones` no es «las de la receta»: es **de donde
                                                  se parte**, que es **la ocurrencia***
  «VERSION»                                       `versiones()` + `actualizar()` -- y su ensayo
  «Y EL DUEÑO»                                    *** `_de_quien(con, propietario, receta_id)` ***
                                                  *-- la misma puerta que `core/traspaso.py` citaba: «la puerta
                                                  es `recetas._de_quien`, que ya existe y ya lanza»*
```

> *** Y `escala(ingredientes, de_raciones, a_raciones)` es la pieza que conecta con **B04**: ***
>
> *Es **la misma funcion** que el traspaso usa para **escalar por comensales** -- *y su firma dice algo: **`de_raciones`
> y `a_raciones`**, no «las raciones de la receta y las que quieres».*
>
> *** O sea: **la escala es relativa**, y por eso **la misma receta puede ir al plan con raciones distintas cada
> vez** -- *que es «raciones **por ocurrencia**», exactamente.* ***
>
> *** Y la `l134` esta **antes** de `leer` y de `versiones`: **es una funcion pura de ingredientes**, no toca la
> base -- *y por eso B04 pudo usarla en los dos puentes.* ***

## 3. Y `_de_quien` cierra un circulo que llevaba abierto desde B05

**En `core/traspaso.py` estaba escrito:** *«Y el dueño se comprueba aqui, no en la pantalla. **La puerta es
`recetas._de_quien`, que ya existe y ya lanza**: "una receta necesita dueno: el recetario es personal".»*

> *** Y ahora se ha visto **al otro lado de la puerta**: *** *`core/recetas.py:102` -- *y **existe**, y **esta antes
> de `crear`, `leer` y `actualizar`**.*
>
> *** O sea: **el traspaso de B05 citaba una puerta de B07**, y **las dos partes estan** *** -- *que es **el mismo
> patron que `traspaso.id_de_linea` -> `almacen.anade_linea`*: **la cadena se cierra por un nombre**, y **el nombre
> estaba escrito en el otro fichero**.*
>
> *** Y es **la segunda vez en la sesion** que eso pasa -- *y las dos veces, **leyendo**, no buscando.*

## 4. Y B07 queda con **seis de seis localizadas**

```
  1) EL EDITOR DE RECETA    LOCALIZADO -- `crear`/`actualizar`/`versiones` + `test_editar_receta.py`
  2) LA IMPORTACION         HECHO -- `comprueba_fuente` (4 motivos), `FUENTES` vacia, `razon_declarada`,
                            `Borrador` (la previa); y las de red en `core/fetch.py`
  3) EL PLAN                LOCALIZADO -- `planificar`/`plan`/`quitar_del_plan`/`escala`; «duplicar semana» POR MIRAR
  4) LA COCINA              HECHO -- `cocina.py` puro; el temporizador como hora de fin; «sin declarar consumo»
                            **por no importar el diario**
  5) Y LA VERSION           CON ENSAYO -- `versiones()`, y `test_editar_dice_en_voz_alta_que_crea_version_nueva`
  6) Y LA ACEPTACION        «CINCO RECETAS CON DATOS ... y NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS»
```

> *** Y lo unico que queda «por mirar» en toda B07 son **dos cosas concretas**: ***
>
>   - **«duplicar semana»** *-- *que **no esta en los nombres de `recetas.py`**, y **puede ser de la API o de la
>     pantalla**; y*
>   - **las guardas de red** *-- *que **no son de `importar_receta.py`**: *son de `core/fetch.py`.*
>
> *** Y ninguna de las dos se dice que falte. ***
