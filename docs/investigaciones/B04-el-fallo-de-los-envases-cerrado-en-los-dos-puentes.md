# B04 · **El fallo de los envases: cerrado en los DOS puentes, con medicion en vivo**

*14/10/2026. **Es el fallo que denuncio el propietario**, y el complemento decia de el dos cosas que
resultaron ser **la clave**: *

> *** «La reproduccion actual calcula dos envases y guarda uno: persiste el numero correcto…» *** *
> *** «Afecta a **AMBOS** puentes de transferencia (receta->lista y plan->lista)» *** *

*Y tenia razon en las dos. **Lo que yo lei como dos fallos era uno solo**, *en **la pieza que los dos
comparten.** *

---

## 1. El sintoma, medido en vivo (no en un ensayo)

```
*** PUENTE DEL PLAN ***  *5 recetas con `comensales: 4` sobre recetas de 2 raciones, y tres de ellas usando
   el MISMO articulo (`alcampo:99700`, **1,0 kg**):*
  *** `AUCHAN Pisto… cant=3800.0 g` ***  *** `envases=None` ***  -> *y en la lista: *** `CANTIDAD=1` *** *
  *con la nota diciendo «(3800 g)»* *** <- los gramos SOLO en la nota *** ⚠️

*** PUENTE DE LA RECETA ***  *la receta de **1.400 g** del mismo articulo, para 4 comensales:*
  *** `CANTIDAD=1` ***  *con la nota «de la receta: AUCHAN Pisto (…)»* ⚠️
```

> *** Es **exactamente** lo que el complemento describia: *** *** «se calculan dos envases y se persiste
> cantidad 1, y "dos envases" queda solo en la nota.» *** *

## 2. *** La causa: un CONTRATO, no un calculo ***

```
*** `core/previa_compra.py` ***  *** es PURA, y a proposito *** *
   *-- *su propio ensayo lo exige (`tests/test_g12_previa.py:70`): *
      *** `assert list(firma.parameters) == ["ingredientes"], "solo la lista: ni conexion ni propietario"` *** *
   *-- *o sea: **no toca bases, no consulta nada**, *y **por eso se puede probar sin nada** *
*** -> asi que **el tamaño del envase tiene que VENIR PUESTO en el ingrediente** *** *
   *-- *y lo lee en `previa_compra.py:123`: `tamano_envase = ing.get("tamano_envase")`*
*** -> y **el unico que sabe leer el catalogo es `plataforma/api`** *** *
   *-- *`core` **no puede depender de `plataforma`**: *el catalogo vive alli*
*** -> y **quien ponia el dato era `recetas._con_precios`** (`l281-282`), *
   *que **solo se usaba al LEER una receta** (`l229`) *
   *** -> y los dos puentes construyen sus lineas **por otro camino** *** *
```

> *** Y **el calculo estaba bien todo el tiempo**: *`previa_compra` **delega** en `envases_enteros`
> (`previa_compra.py:282`), *y `envases_enteros` **tiene la regla con su ejemplo** — *«1,4 kg con envases
> de 1 kg son **dos envases** y **0,6 kg sobrantes**», escrito desde el 12 de octubre.* *
>
> *** Lo que faltaba era *** *** el dato ***, *y **el propio codigo ya lo decia** (`recetas.py:274-276`):
> *** «La regla estaba escrita y probada; **lo que faltaba era rellenar el dato**, y esa linea es esta.» *** *

## 3. El arreglo, en los dos sitios donde el dato no llegaba

```
*** PUENTE DEL PLAN ***  `plataforma/api/main.py:1638` -- *el bucle que construye los ingredientes*
   *-- *ya escalaba por comensales y ya ponia la receta para la nota; **y no ponia el envase***
   *-- *se anade: `catalogo.producto(str(suyo["producto_id"]))` -> `tamano_envase` / `unidad_envase`*
   *-- *commit `bfed8f7`*

*** PUENTE DE LA RECETA ***  `core/traspaso.py` + `plataforma/api/recetas.py`
   *-- *`a_la_lista` no tiene `hallada` -- **la construye `traspaso`** --, asi que el corte va alli*
   *-- *y `traspaso` **ya aceptaba un inyectado** (`insertar`), asi que se le anade `enriquece=None`*
   *-- *y la API lo rellena con `_con_precios`, **la pieza que ya existia y ya estaba probada***
   *-- *commit `24ca99e`*
```

> *** Y **se intento antes en `previa_compra`**, *con un parametro inyectado — *y **un contrato lo paro**:
> `assert ['ingredientes', 'ficha'] == ['ingredientes']`.* *** *Y tenia razon: *pasar un lector de catalogo
> **es darle acceso al mundo**, *aunque venga como parametro.* *Se deshizo.* *
>
> *** Es **la primera vez en la sesion que un contrato escrito protege en vez de enganar.** *

## 4. *** La medicion en vivo, despues ***

```
*** PUENTE DEL PLAN ***   *3.800 g de un envase de 1.000 g*
   *** -> `ENVASES=4` *** *(3800/1000 = 3,8 -> 4)*, *** `sobrante=200.0` *** *(4x1000 - 3800)*
   *** -> y PERSISTIDO: `CANTIDAD=4` *** ✓

*** PUENTE DE LA RECETA ***  *2.800 g del mismo envase*
   *** -> `CANTIDAD=3` *** *(2800/1000 = 2,8 -> 3)*, *y su sobrante en la nota* ✓
   *** -> y `producto_id = alcampo:99700` *** *** -> el ARTICULO ELEGIDO se conserva *** ✓

*** Y SIN ARTICULO ELEGIDO ***  *`envases=None`, `cantidad=1`* -- *porque la columna es `NOT NULL` --
   *** y la nota dice «no se sabe el tamano del envase» *** ✓
   *** -> «no se inventa», y «es distinto de contarla como cero» *** *
```

## 5. Y las regresiones, las dos probadas **revirtiendo el arreglo**

```
*** LA DEL PLAN ***     *3.800 g -> 4 envases*  *** FALLA sin el arreglo: `KeyError: 'tamano_envase'` *** ✓
*** LA DE LA RECETA *** *1.400 g en envase de 1.000 -> 2 envases y 600 g de sobrante*
                        *** FALLA sin el enganche: `TypeError` *** ✓
*** y las dos llevan al lado el caso contrario ***  *sin arreglo **no se inventa nada** (`envases is None`)*
```

## 6. *** Y una correccion a MIS PROPIOS ENSAYOS, que es la parte incomoda ***

```
*** LAS CINCO REGRESIONES DE ENVASES QUE HABIA ***  *** PARCHAN `main._del_plan` *** *
   *-- *o sea: **le pasan la linea ya calculada** *-- *** y por eso pasaban CON Y SIN arreglo *** ⚠️
   *-- *saltaban **justo el codigo que hacia falta*** *
*** -> es **el mismo error que ya habia cometido antes en la sesion** *(-- una regresion **en la ruta que
   no era**, *en `desde-favoritos` --), *y aqui estaba **repetido cinco veces** en el mismo fichero* ⚠️
*** -> y por eso **el arreglo que yo creia hecho no arreglaba nada**: *`envases or 1` daba `1`,
   *y **`1` es el numero que el propietario denuncio** * ⚠️
```
