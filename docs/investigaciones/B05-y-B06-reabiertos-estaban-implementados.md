# B05 y B06 reabiertos · **los dos estaban implementados, y la fila decia «cerrado como lectura»**

*El objetivo: *** «*Reabre criterios cerrados por lectura *** y trabaja en implementacion y evidencia».** *
*Y **los tres paquetes mas grandes del plan** *(-- B05, B06, B07 --)* llevaban esa frase en el control.* *

---

## 1. *** B05 · idempotencia y consistencia entre almacenes ***

```
*** «*misma clave con contenido distinto produce *** CONFLICTO ***, *no exito ficticio» *** *
   *-- `core/diario.py:119`: *** «**La entrada que ya hay -- *** o el conflicto, dicho ***» *** ✓
   *-- *y `l195`: *«el indice es parcial, *y *** el destino del conflicto tiene que decirse ***» ✓✓
*** «*operaciones con *** recibo *** y *** huella del contenido ***» *** *
   *-- `core/manifiesto.py:51`: *** `def huella(ruta, trozos=12)` *** *
      *«Huella corta del contenido. *** Sirve para decir «esto es lo que se publico» ***» ✓
   *-- `core/equivalencias.py:53`: *** `def huella_catalogo(filas)` *** ✓
   *-- *y `core/inventario.py:187`: *`resultado, *** hash_util ***, *** parser_version ***` *
      *-- *la huella **y la version del parser**, *que es lo que evita **mezclar precio actual con
      detalle obsoleto** ✓
*** «*concurrencia *** y caida tras insertar media lista ***» *** *
   *-- `core/inventario.py:137-138`: *** `momento = ahora or datetime.now()` *** *
      *** `vence = momento + timedelta(minutes=LEASE_MINUTOS)` *** *
      *** -> un LEASE con vencimiento ***: *si el proceso muere, *el lease **vence** *y **otro lo
      recoge** ✓✓✓
*** «*dos pestañas ***, versiones concurrentes ***» *** *
   *-- `tests/test_fase2_f07_dos_sesiones.py`, *** CINCO ENSAYOS ***: *
      `test_la_cantidad_vieja_no_gana_por_llegar_despues` · *`…la_cantidad_nueva_gana_si_llega_despues` ·
      *`test_el_tachado_gana_el_primero_aunque_llegue_segundo` · *`test_tachar_dos_veces_no_es_un_error` ·
      *`test_destachar_gana_siempre_sin_mirar_la_hora` ✓✓✓
   *-- *y `tests/test_fase2_f02_concurrencia.py`, *un fichero entero ✓
*** -> *** IMPLEMENTADO ***, *salvo **«destino distinto»**, *que queda por medir ⚠️
```

## 2. *** B06 · nutricion por campo, cadena y universo ***

```
*** «ml->g *** solo con dato especifico acreditado, NUNCA asumir densidad 1 ***» *** *
   *-- *dicho en **cinco sitios** (`envases_enteros` x3, `identidad`, `recetas`) ✓
   *-- *y con *** SIETE ENSAYOS ***, *y **el mas fuerte** es `test_b08_la_prevision_no_inventa.py`:
      *«Las palabras se buscan *** sueltas ***»* -> *comprueba que **el codigo dice «densidad»**, *
      *y **no que la invente** ✓✓✓
*** «sin kcal *** no perder macros ***» + «cobertura con numerador/denominador» *** *
   *-- `core/diario.py:292-295`: *** `_cobertura` POR NUTRIENTE ***, *`{con_dato, total, completa}` ✓
   *-- *y `l287`: *** `_trae_dato`: «Sin dato no es cero: es que no se sabe» *** ✓✓✓
*** «*campo *** nativo / enriquecido / manual ***; ausente / no aplicable / no publicado / error /
   pendiente *** diferenciados ***; *cola por nuevos/cambiados/caducados, hash y *** presupuesto por
   fuente ***; *** no 88 horas de fichas sin prioridad ***» *** *
   *-- `core/inventario.py`: *** `PENDIENTE` *** y *** `NO_PUBLICADO` ***, *columna *** `estado` ***, *
      *y cola con prioridad: *«lo pendiente y lo vencido, *y entre eso lo que lleva mas tiempo» ✓
   *-- `core/presupuesto.py`, *** con su motivo escrito ***: *
      *** «*La cola tiene *** 72 319 fichas pendientes *** *y no tenia fecha» *** ✓✓✓
   *-- *y `core/config.py:35` lo cuenta: *«459 nuevos, *** 100 *** pedidas, *** 374 *** pendientes» ✓
*** «*nutricion por *** 100 g / 100 ml / racion *** *y *** preparado / vendido ***» *** *
   *-- `core/schemas.py:77`: *** `"nutricion_por": pl.Utf8,  # "100g" | "100ml" | "porcion"` *** ✓
   *-- `core/diario.py:252-256`: *`round(por_100 * gramos / 100, 1)`, *y **rechaza** `None`, *
      *** `NaN` (`por_100 != por_100`) *** *y negativos ✓✓✓
   *-- `core/normalize.py:115`: *** `unidad_por_100` ***, *que sirve **para el precio y para la
      nutricion** *(-- *las dos se publican por 100 --)* ✓
   *-- *y **en la pantalla**: *un *** selector *** «Base de la etiqueta» (`Cocina.tsx:73`), *
      *y **la validacion de la base** (`cocina.ts:16`: *`!['100g','100ml'].includes(i.base)`)* ✓✓
*** -> *** IMPLEMENTADO ***, *salvo: *la **causa** de cada hueco, *«ausente/no aplicable» diferenciados
   de «no publicado», *los **historicos de ficha**, *y *** preparado / vendido *** ⚠️
```

## 3. *** Y lo que esto significa, que es lo que hay que decir ***

```
*** DE LOS TRES «CERRADOS POR LECTURA» ***: *
   *** B05 ***  *** implementado *** *(-- y la fila no lo contaba --)* ✓
   *** B06 ***  *** implementado en las CUATRO cosas miradas *** *(-- y la fila no lo contaba --)* ✓
   *** B07 ***  *** tenia un SSRF *** *(-- y la fila tampoco lo contaba --)* ⚠️
*** -> *** «cerrado como lectura» no describe el sistema ***: *describe *** que alguien miro.** *
   *-- *y **por eso se lee como si describiera el sistema** *(-- *y **yo mismo lo lei asi**, *
      *y dije «hay trabajo grande en los tres» --)* ⚠️
*** -> y **describia de menos en todo lo comprobado**, *salvo en **B07**, *donde **ocultaba un
   agujero** *(-- *y ese **solo se ve con un ensayo que no existia** --)* ✓✓✓
```

## 4. Y lo que queda, por paquete y medible

```
*** B05 ***  *-- *** destino distinto *** ⚠️
*** B06 ***  *-- *la *** causa *** de cada hueco · *«ausente/no aplicable» vs «no publicado» ·
   *los *** historicos de ficha *** · *y *** preparado / vendido *** ⚠️
*** B07 ***  *-- *la *** foto propia *** · *el *** duplicar semana *** · *los *** temporizadores *** ⚠️
*** y **las cuatro decisiones** *** *(-- tres del propietario, *y **el grano del hallazgo 2** --)* ⚠️
```
