# La leccion de metodo de esta tanda · **buscar con las palabras del PLAN, no con las mias**

*Y **no es una observacion de estilo**: *me ha hecho decir **«no existe»** *y **«queda por hacer»**
**cuatro veces**, *y **las cuatro estaban mal.** *

---

## 1. *** Los cuatro falsos negativos ***

```
*** 1) «NO HAY NI UN ENSAYO DEL IMPORTADOR» ***  *-- busque `*import*`* ⚠️
   *** y el proyecto lo llama *** `test_fase2_f09_fuente_permitida.py` *** *
   *-- *o sea: **por su FASE**, *no por «importar» ✓
*** 2) «LA EXCLUSION GLOBAL DE LIDL SIGUE EN PIE» ***  *-- busque el veto en `cesta.py`* ⚠️
   *** y la puerta esta en `main.py:844` *** *(-- *a **quince lineas** de donde mire --)* ✓
*** 3) «B06: QUEDAN la causa de cada hueco, ausente/no aplicable, historicos y preparado/vendido» *** ⚠️
   *** y buscando *** «nativo» *** y *** «no_encontrado» *** *(-- **las palabras del plan** --)*: *
   *-- `core/schemas.py`: *** `precio_ref_nativo_cent` · `precio_referencia_nativo_cent` ·
      `precio_anterior_nativo_cent` · `ha_bajado_nativo` *** *
      *** -> «nativo» es UNA COLUMNA, *y lleva `_nativo` en el nombre ✓
   *-- `core/inventario.py:19`: *** «Un 404 no retira nada. Pasa a `no_encontrado` con su fecha» *** ✓
   *-- `core/derive.py:117`: *** `pl.col("fecha").count().alias("dias_de_historico")` *** ✓
   *-- *y *** 23 ficheros de ensayo ***: `test_campos_del_grupo` · `test_matriz_fichas` ·
      `test_informe_inventario` · `test_mide_nutricion` · `test_de_la_ficha_al_diario` ·
      `test_fase2_f05_ficha_carrefour|dia|mercadona` · `test_fichas_lidl` · `test_inventario`… ✓✓✓
*** 4) «EL IMPORTADOR NO TIENE GUARDAS DE REDIRECCION» ***  *-- y **era verdad*** ✓
   *-- *pero **las otras tres** (`fuente`, *`tiempo`, *`tamaño`)* **si estaban**, *
      *y **el plan las nombra juntas** *-- *asi que **hasta que no medi las cuatro, no supe cual faltaba** ✓
```

## 2. *** Y por que pasa ***

```
*** EL PROYECTO NOMBRA CON EL VOCABULARIO DEL ENCARGO *** *
   *-- *`test_g01_*** recibo ***_del_puente.py` *-- «operaciones con *** recibo ***»* ✓
   *-- *`test_b04_*** contrato ***_de_del_plan.py` *-- «el *** contrato *** del puente»* ✓
   *-- *`manifiesto.`*** huella ***` *-- «*** huella *** del contenido»* ✓
   *-- *`precio_ref_`*** nativo ***`_cent` *-- «campo *** nativo ***/enriquecido/manual»* ✓
   *-- *`test_fase2_`*** f05 ***`_ficha_...` *-- *** por FASE ***, *no por «ficha»* ✓
*** Y YO BUSCO CON EL MIO *** ⚠️
   *-- *`*import*` *-- *cuando el fichero se llama **por su fase***
   *-- *`campo_nativo` *-- *cuando la columna se llama **`..._nativo_cent`***
   *-- *`veto`/`excluye` *-- *cuando el codigo dice **`CADENAS_QUE_SE_CAPTURAN`***
*** -> *** y el resultado es un falso «no existe» ***, *que **cuesta mas que no buscar**:
   *porque **se escribe**, *y **el siguiente lo lee como un hecho.*** ⚠️
```

## 3. *** Y lo que hay que hacer, entonces ***

```
*** BUSCAR CON LAS PALABRAS DEL PLAN ***, *no con las mias: *
   *-- *el plan dice «recibo» -> busco **`recibo`** *
   *-- *dice «nativo» -> busco **`nativo`** *
   *-- *dice «ausente/no aplicable/no publicado» -> busco **`no_publicado`**, *`no_aplicable`…*
   *-- *y dice «por fase» -> busco **`f0*`** *(-- *las fases del adjunto --)* ✓
*** Y CUANDO NO APAREZCA, DECIRLO ASI ***: *
   *** «no lo he encontrado buscando `X`» *** *-- *y **no** «no existe»* ✓✓✓
*** -> *y **eso es lo que el objetivo pide con «una funcion por investigacion, evidencia,
   demostrado/hipotesis/desconocido»**: *«no lo he encontrado» *es **desconocido**, *
   *y **«no existe»** es **una afirmacion**, *que **exige haber buscado bien.*** ✓
```

## 4. Y el estado de B06, corregido **otra vez**

```
*** LO QUE DIJE ***  *«quedan cuatro cosas»* ⚠️
*** LO QUE HAY ***  *** lo nativo esta en el esquema, *`no_encontrado` existe con su fecha, *
   *`dias_de_historico` existe, *y hay **23 ficheros de ensayo** *** ✓✓✓
*** -> *** B06, en lo que he mirado, esta implementado *** *
   *-- *densidad (7 ensayos) · *cobertura por nutriente · *inventario con estados, cola y presupuesto ·
      *nutricion por 100g/100ml/porcion con selector · *nativo vs enriquecido en el esquema ·
      *`no_encontrado` sin retirar · *y `dias_de_historico` ✓
*** y **lo que queda de verdad, sin afirmar de mas**: *
   *-- *** «preparado / vendido» *** *-- *que es lo que **no he encontrado con ninguna de las dos
      palabras**, *y **lo digo asi** ⚠️
   *-- *y **la causa concreta de cada hueco** *(-- *que puede estar en `no_publicado` y no la he
      separado de `pendiente` --)* ⚠️
```

*** Y **la leccion vale para todo lo demas**: *llevo **seis** mediciones mias que cayeron al mirar mejor
*-- *y **cuatro** de ellas **por buscar con el vocabulario equivocado.*** *Que es **la misma familia** que
todo lo demas: *una anotacion que **no se corresponde** con lo que hay, *y **se lee como si se
correspondiera.*** *
