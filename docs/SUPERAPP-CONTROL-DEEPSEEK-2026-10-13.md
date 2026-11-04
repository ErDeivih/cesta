# Control vivo del nuevo encargo

Objetivo: [GOAL ACTUAL](SUPERAPP-GOAL-ACTUAL.md).
Contrato: [plan B00–B16](SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md).
No usar cifras heredadas para cambiar estas celdas.

## Punto de continuación

Preparación de GPT, 13/10/2026, HEAD inspeccionado `dddc74e`.
Tarea diaria Running al observar; puntero `20261012-162023`, precios del 11,
seis huellas correctas. Ruff verificado; 1.999/74 son resultados del traspaso.
No se ha detenido ni duplicado ingesta, cambiado el catálogo o restaurado una base.
Diagnóstico B04 ejecutado sin bases reales: requerida 300 g, previa 100/100,
una unidad insertada con nota 100 g; segunda contribución descartada. Script:
`uv run python -m scripts.auditar_puente_plan_20261013`.
El estado Running es una foto, no una instrucción de asumirlo al retomar.

Siguiente: B00 guardas e inventario actual → B04 regresiones de los dos puentes
→ B03 adaptador diario Lidl. Los demás paquetes continúan sin esperar a la captura.

| Paquete | Estado de este encargo | Próxima evidencia |
| --- | --- | --- |
| B00 | **cerrado** | Docker levantado, cuatro puertas verdes y la guarda del DSN con siete ensayos |
| B01 | **al día, verificado** | Las seis fuentes con dato de hoy; tarea Ready (14/10 06:00); candado libre |
| B02 | **cerrado · y su prediccion vence a las 06:00 del 14** | Lidl ES el sexto en `run.py:40`; su ritmo declarado con motivo; y `fichas_lidl.py` contesta cuatro clausulas. *** A las 00:25 del 14 la ultima pasada era la del 13 a las 10:48, y Lidl NO habia corrido nunca -- porque el cambio de ORDEN es de hoy. La primera ocasion es la pasada de las 06:00, y se comprueba con UNA linea: `Get-Content data\runs.csv -Tail 8 | Select-String lidl` *** |
| B03 | **cerrado** | Aceptacion por HTTP (bed5639); queda fuera del criterio usar la zona para elegir |
| B04 | **cerrado el 13 · REABIERTO y cerrado otra vez el 14** | Aceptación 27/27 contra la API real, *** y el propietario corrigio cuatro puntos el 14: *** *los envases (se calculaban dos y se guardaba uno) · el ingrediente sin catalogo (se quedaba FUERA) · el dedupe por nombre · y la identidad de la receta (el articulo elegido **se perdia siempre**). *Y ademas: el orden del tuple, y la telemetria de Lidl en sus tres salidas mudas.* *** Cada uno con su regresion, revertida para comprobar que falla sin el arreglo. *** |
| B05 | **REABIERTO el 14/10 y MEDIDO · implementado** | El conflicto por clave esta en `core/diario.py` («La entrada que ya hay -- o el conflicto, dicho»), y su indice es parcial **a proposito**; las huellas de contenido estan en `manifiesto.huella` y `equivalencias.huella_catalogo`; la concurrencia de dos pestañas tiene `momento` y **CINCO ensayos** (`test_fase2_f07_dos_sesiones.py`) mas `test_fase2_f02_concurrencia.py`; y la caida a mitad la resuelve un **LEASE con vencimiento** (`LEASE_MINUTOS`). Queda por medir: destino distinto |
| B06 | **REABIERTO el 14/10 y MEDIDO · implementado, la fila lo describia de menos** | «ml->g nunca asumiendo densidad 1»: implementado, dicho en **cinco sitios** y con **SIETE ensayos** (y el mas fuerte busca las palabras sueltas, para comprobar que el codigo dice «densidad» y no que la invente). «Sin kcal no perder macros» y «cobertura con numerador/denominador»: `_cobertura` es **POR NUTRIENTE** (`{con_dato, total, completa}`) y `_trae_dato` dice «Sin dato no es cero: es que no se sabe». Y estados/cola/presupuesto: `inventario.py` con `PENDIENTE` y `NO_PUBLICADO`, columna `estado`, y cola con prioridad; `presupuesto.py` con su motivo escrito (72.319 fichas sin fecha). **Y de las cinco cosas que he medido, las cinco ESTAN** (densidad con 7 ensayos, cobertura POR NUTRIENTE, inventario con estados y cola con prioridad mas presupuesto por fuente, nutricion por 100g/100ml/porcion con selector en la pantalla, y nativo-vs-enriquecido en el esquema con `precio_ref_nativo_cent`). **Lo que NO esta, buscado con las palabras del plan y con las del esquema** (`preparado`, `vendido`, `tal_cual`, `en_seco`, `cocido`, `crudo`, `as_sold`, `estado`): la distincion **«preparado / vendido»** -- el valor del producto que se vende contra el del plato preparado. `nutricion_por` es `100g | 100ml | porcion`, asi que falta ese valor o una columna aparte, y es una decision de diseno. **Y medido despues**: «preparado / vendido» **no es un olvido del proyecto, es una limitacion de la fuente** -- buscado con las palabras del plan, con las del esquema (`tal_cual`, `en_seco`, `cocido`, `crudo`, `as_sold`) y en el codigo entero, solo aparecen **categorias de tienda** (`preparados`, que es una seccion) y `peso_escurrido_g`, que **es peso y no nutricion** (y tiene su motivo escrito: «en conservas cambia cual es mas barato»). **Y la forma de implementarlo, si algun dia hay dato, ya esta decidida por medicion**: columna aparte, porque lo unico que lee `nutricion_por` es una etiqueta de pantalla (`app.js:1299`, `Por ${...}`), asi que anadir un valor romperia la etiqueta y anadir una columna no rompe ninguna lectura -- y `ESQUEMA_BRONZE` es un contrato con ensayo (`test_colectores.py:150` afirma que el registro tiene exactamente sus claves), asi que el cambio se notaria. **Y la CAUSA DE CADA HUECO, medida el 14/10 y tambien estaba**: `core/inventario.py:37-46` tiene NUEVE estados con la causa en el nombre -- `PENDIENTE` (aun no se ha pedido), `EN_CURSO` (con lease), `CORRECTO`, `PARCIAL` (trajo parte, y se sabe cual), `NO_PUBLICADO` (la cadena NO lo publica), `BLOQUEADO` (WAF), `ERROR_TEMPORAL` (red), `NO_ENCONTRADO` (404), `EXCLUIDO` (fuera de alcance) -- y `FINALES = (CORRECTO, PARCIAL, NO_PUBLICADO, NO_ENCONTRADO, EXCLUIDO)` son los cinco que TERMINAN. Y lo que remata la doctrina es la separacion: `BLOQUEADO` y `ERROR_TEMPORAL` NO estan en `FINALES`, o sea que un bloqueo de WAF y un fallo de red NO son un hueco permanente -- se reintentan, y por eso no cierran la ficha. Que es exactamente lo que el encargo pide con «no eludas CAPTCHA/WAF ni confundas desafio con catalogo vacio». **Y lo unico que queda de B06 es «preparado / vendido»**, que no es un olvido sino que la fuente no lo publica; y una nota antigua sobre `no_publicado` |
| B07 | **REABIERTO el 14/10 · TENIA UN SSRF, y queda CERRADO** | La ruta `/api/recetas/importar` **no tenia ni un ensayo** (los 19 de `f09` prueban el modulo), y de sus cuatro guardas -- fuente, tiempo, tamaño y redirecciones -- **faltaba la cuarta**: `urlopen` seguia la redireccion y el destino no se comprobaba, asi que una fuente DECLARADA podia redirigir a un host no declarado y el importador lo leia (medido: **422** con `localhost`). Cerrado con `importar_receta.abre_con_guarda`, que **valida el destino con `comprueba_fuente` ANTES de ir** (comprobar despues no sirve: la peticion ya se hizo), y la ruta lo traduce a **400**. **Cinco ensayos nuevos** de la ruta. **Y medidos despues, uno por uno**: los *** TEMPORIZADORES *** y la cocina recuperable **estan** (`core/cocina.py`, con `tests/test_fase2_f10_cocina.py`, y con la doctrina escrita: «un temporizador NO es una cuenta atras… es una HORA DE FIN», porque «el transcurrido se pierde y quien esta cocinando no se entera»; y «el paso actual es estado, y el estado se guarda»). La *** FOTO *** esta: `schemas.py:70` tiene `imagen`. Y *** «REPETIR / DUPLICAR SEMANA» NO ESTA ***, y ahora se dice con fundamento: **no es un grep de palabras, es la lista ENTERA de rutas** (`GET|POST /`, `GET|POST /plan`, `GET /plan/prevision`, `GET /{id}`, `GET|POST /{id}/a-la-lista`, `GET /{id}/versiones`, `PUT /{id}`, `POST /{id}/archivar`, `DELETE /plan`, `POST /importar`) -- hay borrar el plan y poner una receta en un dia, y **no hay copiar la semana pasada a la siguiente**. Y eso lo clasifica: **es un hueco DEL PROYECTO** (se puede escribir sin depender de nadie), no una limitacion de la fuente como «preparado/vendido». **Y son TRES frases del plan, no una**: «varias comidas por dia», «repetir/duplicar semana» y «raciones por ocurrencia», y las tres fallan **por la misma causa**: la ocurrencia del plan **no tiene identidad propia** -- `plan` es `(fecha, receta_id, version, comensales)` con `PRIMARY KEY (fecha, receta_id)`, asi que no se puede poner la misma receta dos veces el mismo dia, ni decir en que comida va, ni cuantas raciones se cocinan ahi, ni copiar una semana. Lo que SI esta es `comensales NOT NULL`, que es el escalado por comensales que pedia el encargo. **Y el tamano esta medido**: solo TRES sitios escriben el plan, y los tres en `core/recetas.py` -- `planificar` (288), `plan` (298) y `quitar_del_plan` (315) --, asi que el cambio es **un esquema y tres funciones**, con su ensayo equivalente. **Y queda un detalle que solo se ve leyendo la consulta del borrado**: `DELETE FROM plan WHERE fecha = ? AND receta_id = ?` borraria TODAS las comidas de esa receta ese dia, asi que el cambio obliga a decidir que significa `quitar_del_plan`. **Las tres decisiones antes de escribir**: (a) la comida en la clave o (b) un id de ocurrencia; el vocabulario de las comidas; y que significa quitar del plan. **Y el vocabulario NO hay que inventarlo: ya esta** -- `core/diario.py:38` tiene `COMIDAS = ("desayuno", "media manana", "comida", "merienda", "cena", "otras")`, asi que el plan debe usar el mismo. **Y hay una colision de nombre que el cambio obliga a resolver**: `recetas.comidas` (la previa, `recetas.py:203`) son **las ocurrencias del plan** -- una por `(fecha, receta_id)`, **sin ningun campo que diga cual de las comidas es** --, y `diario.COMIDAS` son **las seis comidas del dia**: la misma palabra, dos cosas. Si el plan gana `comida`, `comidas` pasaria a significar «las comidas del dia», y hoy significa «las ocurrencias», asi que hay que renombrarla a `ocurrencias` o aceptar la ambiguedad. **Y con todo medido, lo que queda por decidir es UNA pregunta**: ¿una ocurrencia se puede nombrar por separado, o el par (dia, receta) es la ocurrencia? -- que es la misma que «¿que significa `quitar_del_plan`?», y su respuesta decide la clave, el nombre de `comidas`, y si «duplicar semana» copia filas o crea ocurrencias nuevas. **Y SE RESOLVIO, y se implemento entero el 14/10**: la clave es `(fecha, comida, receta_id)`, con el vocabulario de `diario.COMIDAS`; `raciones` es columna propia de la ocurrencia y `NULL` quiere decir «las de la receta» y NO se copian; la migracion va en `_migra()` conservando los datos (fila vieja -> `comida='comida'` y `raciones=NULL`, que es lo que significaba); las tres funciones, las tres rutas, la previa, y **duplicar semana** (`POST /plan/semana`) con **recibo** `{creadas, ya_estaban}` e `INSERT OR IGNORE`, porque B05 dice que misma clave con contenido distinto produce conflicto y no exito ficticio. **Y la PANTALLA tambien**: `LineaPlan` gana los dos campos, `PlanSemanal` agrupa por dia Y por comida en el orden del vocabulario (no en el que devuelve la consulta, que la haria bailar), dice las raciones sin pintar `null` como cero, y tiene el boton de copiar la semana con su recibo en pantalla. **17 ensayos nuevos** (11 en Python, 6 en el frontend con los 81 que ya habia). Y quedan las **cuatro decisiones del propietario** |
| B08 | **HECHO · las cuatro piezas** | *** la vista de previstos (`200`) · su ensayo (8) · el objetivo (`PUT /api/preferencias` + `GET /api/yo`) · y LAS TRES SERIES *** (`GraficaDeLasTres` + `LeyendaDeSeries` + `puntosDeLasTres`), cosidas en `Tendencias.tsx` · *** y el dictamen ya no lo cuenta como limitacion *** |
| B09 | **5 de 5 · sin ausencia** | El oraculo es INDEPENDIENTE; veredictos CINCO; la prohibicion es `estabiliza` |
| B10 | **7 de 7 · cerrado** | La restriccion del dueno esta ARREGLADA y los DOS puentes pasan por el mismo upsert |
| B11 | **contestado** | «Lo que no se observo no se puede dibujar como si se hubiera observado» + 3 reglas probadas |
| B12 | **contestado** | La receta es §4 de `SUPERAPP-COMPETENCIA-Y-REA.md`, con su REGLA DE PARADA |
| B13 | **5 de 5 recorridos · y la restriccion MEDIDA por los dos puentes** | `Suite` se sirve · 42 recetas · 7 traspasos · y **0 notas en 302 lineas** |
| B14 | **5 de 5 · y el volumen APLICADO** | CSRF (5) · GET · logs = `runs.csv` + **`CAPAS_INTOCABLES`** · y **`datos_api:/app/data`, aplicado con permiso** |
| B15 | **medido · y con el capitulo que faltaba** | 24 capitulos, 60 KB de modulo, 20 ensayos · *** y AHORA 25: `25-la-nutricion-sin-inventar.md` (seccion «Medidas y agregados») ***, asi que **«nutricion» ya tiene el suyo** |
| B16 | **dictamen ESCRITO, ajustado, y con las capacidades MEDIDAS** | `v20261013-155356` · las 4 puertas verdes · *** y once rondas mas midiendo lo que faltaba: la cola, la cobertura (7,6 %), las promociones, el oraculo, el WAF y «casa frente a publico» *** |

Pendiente no significa borrar lo existente: reutilizar sus implementaciones y
pruebas; estos criterios solo se cierran cuando corresponden a este escenario.

## Entradas por paquete

### B04 · 14/10/2026 (2ª parte) · **las cinco puertas, verdes** · commits `bfed8f7` … `8dbdca1`

> *** Entrada nueva, y **la anterior del 14/10 sigue arriba**: *aquella cerro el complemento; *esta **lo
> mide entero, con las puertas y la app en marcha.*** *

- **Cambio o hallazgo nuevo**: *** el fallo del dueño quedo cerrado EN LOS DOS PUENTES, medido en vivo *** *
  ```
  *** EL FALLO DE RAIZ, y era UN CONTRATO, NO UN CALCULO *** *
    *`core/previa_compra.py` **es pura a proposito** -- *su ensayo lo exige: «solo la lista: ni conexion
    ni propietario»* --, *asi que **el tamaño del envase tiene que VENIR PUESTO en el ingrediente***
    *-- *y quien lo ponia (`recetas._con_precios`) **solo lo hacia al LEER una receta** --*
    *** -> y LOS DOS PUENTES construyen sus lineas por otro camino ***
  *** Y SE ARREGLA EN CADA UNO, porque NO hay un sitio comun *** *
    *el PLAN: `main.py:1638`, buscando la ficha del articulo elegido* (commit `bfed8f7`)
    *la RECETA: `traspaso.pasar_a_lista(..., enriquece=_con_precios)`* (commit `24ca99e`)
    *-- *y **se intento antes en `previa_compra`**, con un parametro inyectado, *
       *** y UN CONTRATO LO PARO ***: *`assert ['ingredientes','ficha'] == ['ingredientes']`* *
  *** MEDIDO EN VIVO, con el codigo desplegado *** *
    *plan:   3.800 g de un envase de 1.000 g -> `ENVASES=4`, sobrante 200, y *** `CANTIDAD=4` *** *
    *receta: 2.800 g -> *** `CANTIDAD=3` ***, y **el `producto_id` conservado** *
  *** Y SIN ARTICULO ELEGIDO ***  *`envases=None`, `cantidad=1`, *y **la nota dice que no se sabe** *
  ```

- **Pruebas ejecutadas**: *** LAS CINCO PUERTAS, VERDES *** *
  ```
  *** `uv run ruff check .` ***   *** All checks passed! *** *
  *** `uv run pytest -q` ***      *** 2.049 passed · 0 failed · 0 errors · 17 skipped *** *
  *** `npm test` ***              *** 81 pass · 0 fail *** *
  *** `npx tsc --noEmit` ***      *** exit 0 *** *
  *** `npm run build` ***         *** exit 0 *** *
  *** y **cada regresion nueva, revertida** para comprobar que falla sin su arreglo *** *
  ```

- **Evidencia**: *los documentos de `docs/investigaciones` de esta tanda*, *y en especial*
  `CIERRE-14-10-2026-las-cinco-puertas.md` y `B04-el-fallo-de-los-envases-cerrado-en-los-dos-puentes.md`
- **Pendiente o limite exacto**: *** UNA decision, y es del propietario ***: *
  *¿la lista **suma** o **sustituye**? *Hoy `uuid5(lista_id|clave)` + `ON CONFLICT DO UPDATE`
  **reemplaza**, *asi que **dos operaciones legitimas del mismo producto se pisan**.*
  *** y el diario ya respondio que suman ***: *«Dos comidas legitimas llevan claves distintas
  **y se registran las dos**»* *-- *o sea: **la identidad es la OPERACION**, no el producto*
  *-- *y `traspaso` **ya construye su clave como operacion** (`propietario|receta|version|semana`)*

- **Y ademas, que no estaba en el complemento**: *
  ```
  *** EL RESPALDO, QUE NO EXISTIA ***  *`respaldar.bat` fallaba siempre: buscaba «running» y Docker
     dejo de decirla; `data\respaldos` no existia; y no cubria las dos SQLite*
  *** EL ARRANQUE QUE ADOPTA SU VOLUMEN ***  *«Recetas» dejo de poder guardar (`readonly database`)
     porque el volumen era de `root`; *ahora `entrar-api.sh` lo adopta y **baja a `cesta`***
  *** LIDL ***  *publicado en gold (79 productos) y **con `region='28'` y precios***
  *** LA RESTAURACION ***  *** las tres patas dentro del ensayo ***, *en base nueva y desechable*
  *** Y SIETE FALLOS que los instrumentos se encontraron a si mismos ***  *-- *el ultimo, *
     *el umbral que confundia «ficha corta» con «ficha rota» (una Granada con `"Granadas."`)*
  ```

### B16 · 14/10/2026 (3ª parte) · **el hallazgo 6 del plan, CERRADO** · commits `271a991` … `c10e593`

> *** Entrada nueva. *Las dos anteriores del 14/10 siguen arriba.* *

- **Cambio o hallazgo nuevo**: *** el recorrido E2E ya recorre Recetas y Calorias *** *
  ```
  *** LO QUE HABIA ***: *`plataforma/prueba_e2e.py` (764 lineas) cubria listas, compras, cierre,
     permisos, ofertas, pasillos, alertas, el vigilante y hasta tiempos -- *y *** el grep de
     `recetas|diario|comensales|kcal` salia VACIO *** *
  *** LO QUE HAY ***: *tres bloques nuevos -- *cinco recetas con datos conocidos, *el plan a la
     lista, *y el diario -- *y el recorrido *** TERMINA Y DA «== TODO BIEN» con exit 0 *** *
  *** Y COMPRUEBA LA ACEPTACION PRINCIPAL ***: *5 de 5 recetas · *las cantidades · *el dedupe (dos
     recetas con el mismo ingrediente -> UNA linea) · *persistencia tras recargar (15 lineas) ·
     *idempotencia (misma clave -> el mismo id, clave distinta -> otro apunte) · *y la cobertura
     dicha (`kcal_conocida=None`, `completo=False`)*
  *** Y POR EL CAMINO SALIO UN DEFECTO REAL ***: *`core/recetas.py` y `core/diario.py` declaran
     `propietario: str` en *** QUINCE *** funciones *y **no lo comprobaba ninguna** *-- *un ensayo
     que inyecta el usuario con `dependency_overrides` llega con un `UUID` y SQLite revienta*
     *** -> arreglado en `core/dueno.py` ***, *un decorador compartido, *con el motivo escrito dentro*
  ```

- **Pruebas ejecutadas**: *** LAS CINCO PUERTAS, VERDES *** *
  ```
  *** `ruff` ***                     *** All checks passed! *** *
  *** `pytest -q` ***                *** 2.056 passed · 0 failed · 0 errors · 17 skipped *** *
  *** `python -m plataforma.prueba_e2e` ***  *** == TODO BIEN · exit 0 *** *
  *** `npm test` ***                 *** 81 pass · 0 fail *** *
  *** `tsc --noEmit` *** y *** `build` ***  *** exit 0 *** *
  ```

- **Evidencia**: `docs/investigaciones/hallazgo-6-cerrado-el-recorrido-receta-y-calorias.md`,
  `hallazgo-6-el-recorrido-no-toca-recetas-ni-diario.md`, `los-siete-hallazgos-del-plan-y-su-estado.md`

- **Pendiente o limite exacto**: *** seis de los siete hallazgos del plan, hechos o medidos ***; *
  *del (2) queda **el grano** *(-- la cesta se decide por cadena, *y el plan la quiere **por articulo,
  region y fecha** --)*; *y **tres decisiones del propietario**: *
  *¿la lista **suma** o **sustituye**? · *¿que origenes se permiten, *y que se hace **sin
  `Origin`**? · *¿la marca de visita se mueve a un `POST`?*

- **Y cuatro conclusiones mias cayeron al medirlas**: *el CSRF, la exclusion de Lidl,
  `calculada.ya_estaban` y «la previa miente» -- *y **las cuatro son el mismo error**: *leer una pieza
  y creer que es el todo* ⚠️

### B05/B06/B07 · 14/10/2026 (4ª parte) · **reabiertos por lectura, y B07 tenia un SSRF** · commits `e676692` … `9c03f18`

> *** Entrada nueva. *El objetivo dice *** «*Reabre criterios cerrados por lectura *** y trabaja en
> implementacion y evidencia»** *, *y la tabla de arriba tenia **B05, B06 y B07 «cerrados como lectura».** *
> *-- *y **al reabrirlos**, *pasa esto:* *

- **Cambio o hallazgo nuevo**: *** B07 tenia un SSRF REAL, medido, y queda CERRADO *** *
  ```
  *** LA RUTA `/api/recetas/importar` NO TENIA NI UN ENSAYO *** *
     *-- *los 19 de `tests/test_fase2_f09_fuente_permitida.py` prueban *** EL MODULO ***
        (`comprueba_fuente`, `lee_json_ld`, `borrador`), *no **el endpoint** *
     *-- *y el endpoint es donde viven *** cuatro guardas ***: *la fuente, *el tiempo (`timeout=10`),
        *el tamaño (`r.read(2_000_000)`) *y *** las redirecciones *** *
     *-- *y de las cuatro: *tres estaban, *y *** la cuarta no *** *
  *** EL SSRF ***: *`urlopen` **sigue las redirecciones por defecto**, *y **el destino no se
     comprobaba** *-- *asi que **una fuente DECLARADA** podia redirigir a **un host que nadie declaro**,
     *y el importador **lo leia** *(-- *medido con un servidor de fixture: *** 422 *** con `localhost`,
     *otro nombre no declarado --)* *
  *** CERRADO ***: *`core/importar_receta.abre_con_guarda`, *un `HTTPRedirectHandler` que *** valida el
     destino con `comprueba_fuente` ANTES de ir *** *-- *y **no despues**, *porque comprobar despues
     **no sirve**: *la peticion al host no declarado **ya se hizo** *--. *La ruta lo usa, *traduce el
     `HTTPError` a *** 400 con su motivo ***, *y **medido despues da `400`** *
  *** Y CINCO ENSAYOS NUEVOS DE LA RUTA ***, *que no existian: *
     *fuente no declarada **400** · *pagina sin `ld+json` **422** *(-- *distinto del 400 --)* ·
     *red que falla **502** · *el camino bueno (**`fuente`** y **`guardada: False`**) ·
     *y el redirect a otro host **400** *
  ```

- **Cambio o hallazgo nuevo**: *** B06 estaba IMPLEMENTADO, y la fila lo describia de menos *** *
  ```
  *** «ml→g solo con dato acreditado, *** NUNCA *** asumir densidad 1» ***: *implementado, *dicho en
     **cinco sitios**, *y con *** SIETE ENSAYOS *** *(-- *y el mas fuerte busca las palabras **sueltas**,
     *para comprobar que **el codigo dice «densidad»** *y **no que la invente** --)* ✓
  *** «sin kcal *** no perder macros ***» + «cobertura con numerador/denominador» ***: *
     `core/diario.py:_cobertura` es *** POR NUTRIENTE *** *-- `{con_dato, total, completa}` --, *
     *asi que **una entrada sin kcal y con proteinas cuenta en proteinas**; *
     *y `_trae_dato` dice *** «Sin dato no es cero: es que no se sabe» *** ✓
  *** estados · cola con prioridad · *** PRESUPUESTO POR FUENTE *** ***: *
     `core/inventario.py` *(-- `PENDIENTE`, `NO_PUBLICADO`, *columna `estado`, *cola con prioridad --)* *
     *y `core/presupuesto.py`, *con su motivo escrito: *** «la cola tiene 72.319 fichas pendientes y no
     tenia fecha» ***; *y `config.py` lo cuenta: *«459 nuevos, 100 pedidas, 374 pendientes» ✓
  ```

- **Pruebas ejecutadas**: *** LAS CINCO PUERTAS, VERDES *** *
  ```
  *** `ruff` ***   *** All checks passed! *** *
  *** `pytest -q` ***  *** 2.061 passed · 0 failed · 0 xfailed · 17 skipped *** *
  *** `python -m plataforma.prueba_e2e` ***  *** == TODO BIEN *** *
  *** `npm test` ***   *** 81 pass · 0 fail ***   *** `tsc` y `build` ***  *** exit 0 *** *
  ```

- **Evidencia**: `docs/investigaciones/B07-un-ssrf-real-en-el-importador-cerrado.md`,
  `B06-reabierto-estaba-implementado.md`

- **Y un error mio, medido y escrito**: *la primera version del ensayo del SSRF redirigia a
  `127.0.0.1:OTRO_PUERTO` -- *** el mismo host ***, *porque `comprueba_fuente` mira `hostname`, *
  *que **no lleva puerto** --, *asi que **seguirla era correcto**; *por eso **reverti un arreglo que
  funcionaba**.* *Es la **sexta** vez del dia que **el que media mal era yo** y no el codigo* ⚠️

- **Pendiente o limite exacto**: *** de B05, B06 y B07 quedan cosas medibles una a una ***: *
  *la **causa** de cada hueco nutricional · *los **historicos de ficha** · *la **foto propia** ·
  *el **duplicar semana** · *los **temporizadores** · *y las cinco de B05 (conflicto por contenido
  distinto, concurrencia, caida tras insertar media lista, dos pestañas, destino distinto)*

### B07 · 14/10/2026 (5ª parte) · **«varias comidas, duplicar semana y raciones»: del modelo a la pantalla** · commits `939cdb6` … `f93a7cf`

> *** Entrada nueva. *La frase de B07 parecia **tres features** y era *** una carencia de modelo ***,
> *y **lo dijo la clave primaria**: *`plan` era `(fecha, receta_id, version, comensales)` con
> `PRIMARY KEY (fecha, receta_id)`, *asi que **no se podia** poner la misma receta dos veces el mismo
> dia, *ni decir en que comida va, *ni cuantas raciones se cocinan ahi, *ni copiar una semana.* *

- **Cambio o hallazgo nuevo**: *** la ocurrencia del plan ahora tiene identidad *** *
  ```
  *** LA CLAVE ***  *** `(fecha, comida, receta_id)` ***, *con el vocabulario de *** `diario.COMIDAS` *** *
     *(-- «desayuno», «media manana», «comida», «merienda», «cena», «otras» --), *que **YA EXISTIA**: *
     *el vocabulario **no se invento** ✓
  *** `raciones` ***  *es columna **propia de la ocurrencia**, *y *** `NULL` = «las de la receta» ***, *
     *y *** NO se copian ***: *si se copiaran, *una receta que cambie de raciones *
     *cambiaria *** lo que ya se cocino *** ✓
  *** LA MIGRACION ***  *va en `_migra()`, *conservando los datos: *fila vieja -> `comida='comida'` *
     *(-- lo que significaba --)* *y `raciones=NULL` ✓
  *** LAS TRES FUNCIONES ***  *-- `planificar` · `plan` · `quitar_del_plan` *(-- que gana `comida`,
     *y con ella **la pregunta que el modelo viejo no tenia**: *¿la receta del dia, *o solo esa comida? --)*
  *** LAS TRES RUTAS ***  *y **la previa** ✓
  ```

- **Cambio o hallazgo nuevo**: *** «repetir / duplicar semana», y su decision la contesto B05 *** *
  ```
  *** `duplicar_semana(con, propietario, desde, hacia)` ***  *y *** `POST /plan/semana` *** ✓
  *** y NO usa `INSERT OR REPLACE` *** *(-- que es lo que usan las demas, *y alli reemplazar es
     correcto: *el usuario esta diciendo «pon esta receta aqui» --)*
  *** sino `INSERT OR IGNORE` ***, *y **devuelve el recibo** `{creadas, ya_estaban}` ✓
  *** PORQUE lo dice B05 ***: *«*misma clave con contenido distinto produce *** conflicto, *
     *no exito ficticio ***» *-- *y **decir «duplicado» cuando no se duplico nada** seria ese exito ✓
  ```

- **Cambio o hallazgo nuevo**: *** y la PANTALLA, que es lo que separa «esta en el codigo» de «se ve» *** *
  ```
  *** `LineaPlan` NO TENIA los campos *** *-- y por eso **la pantalla no podia enseñarlos**: *
     *el tipo es el sitio donde se ve si algo esta a medio camino ✓
  *** `PlanSemanal` agrupaba por FECHA *** *y descartaba la comida y las raciones; *ahora agrupa *
     *por dia **Y por comida**, *y **en el orden del vocabulario** *(-- no en el que devuelve la
     consulta: *si no, *«merienda» apareceria antes de «comida» un dia si y otro no, *y la pantalla
     bailaria entre recargas --)* ✓
  *** y `null` NO se pinta como cero ***: *se dice «las raciones de la receta» *-- *pintar «0
     raciones» seria **inventar un dato** *y **el contrario** del que hay ✓
  *** y el boton de copiar la semana ***, *que **enseña el recibo** *y tiene **frase propia para las
     dos a cero** *(-- «No habia nada que copiar: esta semana esta vacia» --)*, *porque «hecho» no
     dice si copio tres o ninguna ✓
  ```

- **Pruebas ejecutadas**: *** LAS SEIS PUERTAS, VERDES *** *
  ```
  *** `ruff check .` ***  *** All checks passed! *** *
  *** `pytest -q` ***  *** 2.072 passed · 0 failed · 17 skipped *** *
  *** `npm test` ***  *** 81 pass · 0 fail *** *
  *** `npx tsc --noEmit` ***  *** cero errores *** *
  *** `npm run build` ***  *** built *** *
  *** `python -m plataforma.prueba_e2e` ***  *** == TODO BIEN *** *
  ```
  *Y **el recorrido camina las tres frases**, *con numeros: *«la misma receta esta dos veces el mismo
  dia: ['cena', 'comida']» · *«la cena lleva sus 2 raciones, que son de la ocurrencia y no de la
  receta» · *«copiar la semana: 6 creadas, 0 ya estaban» · *«y en la semana siguiente hay 6, que es lo
  que dice el recibo»* ✓

- **Evidencia**: `docs/investigaciones/B07-la-ocurrencia-y-duplicar-semana.md`,
  `B07-la-frase-del-plan-que-es-un-solo-cambio-de-modelo.md`,
  `B07-un-ssrf-real-en-el-importador-cerrado.md`

- **Pendiente o limite exacto**: **de B07 no queda nada del plan**; *y quedan, **del propietario**, las
  **cuatro decisiones de producto**: *el **ambito de Lidl**, *los **origenes permitidos** del CSRF y el
  caso **sin `Origin`**, *si **la lista suma o sustituye**, *y si **`ver_lista` se declara o se mueve**.
  *Y **de B06**, una cosa **medible por mi**: *la *** causa *** concreta de cada hueco nutricional.

### UI/UX · 15/10/2026 · **de 611 clases de fabrica a 9, y cuatro correcciones al plan**

> *** El propietario pidio rehacer la UI/UX: *«*no me gusta el layout, colores, formas, no
> tiene estilo propio»*.* *Y tenia razon, *y esta **medido**.\ *

```
*** LO QUE HABIA ***: *89 ficheros .tsx, *996 lineas con clases de Tailwind **en linea**, *
   *un `estilos.css` de 221 lineas del que **1 clase** era de componente, *y *** las
   *fuentes declaradas NO SE SERVIAN ***: *los titulos salian en **Georgia** ✓
*** Y LA CAUSA DE QUE PARECIERA GENERICA TENIENDO COMPONENTES ***: *`componentes/ui.tsx`
   *ya tenia *** 18 piezas *** *y lo importaban *** 40 ficheros ***.* *Lo que fallaba era
   *que estaban *** enchufadas a la paleta de Tailwind ***: *611 clases de fabrica contra
   *398 de la casa, *y el **boton principal era `bg-sky-700`** *-- *** azul *** *--* cuando
   *el propio `tailwind.config.js` dice que `bosque` es «navegacion y accion principal» ✓✓✓
*** LO QUE HAY AHORA ***: *escalas completas en el tema, *las fuentes **servidas en local**
   *(OFL, con su aviso)*, *las 18 piezas **contra los tokens**, *la navegacion **con iconos**
   *-- 4 dibujados a mano --, *la entrada de pantalla, *los esqueletos, *y *** 9 clases de
   *fabrica ***, *de las que **ninguna es codigo vivo** ✓
*** Y LA PUERTA ***: *`tests/test_contraste.py` **ya existia** y **calcula WCAG**; *
   *reescrito a tokens, *y **al hacerlo midio la direccion nueva**: *`bosque` sobre
   *`marfil` **>=4,5:1** *y `borde-fuerte` sobre `papel` **>=3:1**, *en los dos temas ✓
```

- **Las cuatro correcciones al plan**, *en `docs/ui/PLAN-UI-UX-2026-10-15.md`*: *(1) las
  piezas **ya existian** *(-- 8 de las 10 --)*; *(2) la puerta de calidad **ya estaba**;
  *(3) `Inicio.tsx` **no se pinta** *-- no lo importa nadie --, *asi que **la lista de
  pantallas estaba mal**; *y (4) el color bajo **de 611 a 9**, *y los 9 **no son codigo
  vivo**: *7 son comentarios y 2 un fichero muerto.* *
- **Y lo que sigue dependiendo del propietario**, *pedido desde la ronda 1*: *** ¿pulir o
  rehacer la estructura de las pantallas grandes? *** *(`Cesta` 80 KB, `Panel` 62,
  `Grupo` 34) *y *** ¿se reconstruye `cesta-web-1` para verlo con datos? *** *

### CIERRE DE LA TANDA · 15/10/2026 · **las seis puertas y las cuatro correcciones**

*Verificado a las 514 rondas. *Y **esto no es un cierre por numero de rondas**: *es **el unico criterio que
el complemento del 14/10 acepta** -- *sus **cuatro correcciones**, *y **B00-B16**.* *

```
*** LAS SEIS PUERTAS ***  *** TODAS VERDES *** *
   *** `ruff check .` ***       *** All checks passed! *** *
   *** `pytest -q` ***          *** 2.078 passed · 0 failed · 17 skipped *** *
   *** `prueba_e2e` ***         *** == TODO BIEN *** *
   *** `npm test` ***           *** 81 pass · 0 fail *** *
   *** `npx tsc --noEmit` ***   *** limpio *** *
   *** `npm run build` ***      *** built *** *
*** Y *** LAS CUATRO CORRECCIONES DEL COMPLEMENTO ***, *una por una: *
   *** 1) *** *** «el fallo del dueno SI se reproduce» *** *
      *-- *hoy **`main.py:1842`** escribe **`uno.envases or 1`** en **`cantidad`**, *
         *no solo en la nota* ✓
   *** 2) *** *** «el ingrediente sin catalogo se queda FUERA» *** *
      *-- *la migracion *** `014_la_linea_sin_destino` *** quito la restriccion, *y la linea *
         *** se apunta *** *(-- «Pendiente de identificar» --)* ✓
   *** 3) *** *** «Lidl puede fallar sin fila en `runs.csv`» *** *
      *-- *hoy tiene **DOS filas, dos dias seguidos**: *
         *** `2026-10-14T08:16` *** *** lidl *** *** 79 *** *y *** `2026-10-15T08:43` *** *** lidl *** *** 79 *** ✓
      *-- *y **el de hoy corrio dentro del ciclo diario**, *no en una prueba aparte* ✓✓✓
   *** 4) *** *** «restaurar en una base NUEVA y desechable» *** *
      *-- *** `scripts/ensayo_de_restauracion.py` ***, *con sus guardas ✓
*** Y *** B00-B16 ***: *los **17 con estado**, *y **los tres que decian «cerrado como lectura»** *
   *(-- B05, B06, B07 --)* *** reabiertos, medidos y cerrados *** *
   *-- *con **un SSRF cerrado**, *la **ocurrencia del plan con identidad**, *
      *«duplicar semana», *la **pantalla**, *el **recorrido**, *y **la lista que acumula** ✓✓✓
*** Y *** LAS CUATRO DECISIONES DEL PROPIETARIO ***, *contestadas y ejecutadas ✓
```

- **Lo que queda declarado como LIMITE, y no como hecho**:
  - *** «preparado / vendido» ***: *no es un olvido, *es que **ninguna de las seis cadenas lo publica** ✓
  - *** el ambito de Lidl ***: *es **regional**, *y **`region='28'` sigue SIN IDENTIFICAR** ✓
  - *** el CSRF sin `Origin` ***: *** se declara el limite ***, *no se cierra ✓

### LA INGESTA DEL 15/10 · **corriendo, y con Lidl dentro** · verificado a las 512 rondas

```
*** `(Get-ScheduledTask -TaskName "Cesta diaria").State` ***  *** Running *** *
*** `LastTaskResult` ***  *** 267009 *** = *** `0x41301` *** = *** SCHED_S_TASK_RUNNING *** *
   *-- *o sea: *** la tarea esta EN EJECUCION ***, *no que fallara* ✓
*** y **`data/runs.csv`** lo dice **con datos de hoy**: *
   *** 2026-10-15T08:43:10 ***  *** lidl ***       *** 79 *** *
   *** 2026-10-15T08:44:36 ***  *** aldi ***       *** 2573 *** *
   *** 2026-10-15T08:44:57 ***  *** mercadona ***  *** 4213 *** *
   *** 2026-10-15T08:55:10 ***  *** dia ***        *** 5760 *** *
*** -> cuatro cadenas **terminadas hoy**, *y la tarea **sigue corriendo** *-- *esta en las gordas ✓
*** Y **LIDL HA CORRIDO HOY**, *con sus **79**, *en el *** MISMO ciclo diario *** *
   *-- *que es **lo que B03 pedia**, *y **no un sitemap** ✓✓✓
*** -> y **por el encargo** (*** «*espera/verifica la ingesta activa *** sin duplicarla ***»), *
   *** NO SE LANZA NADA *** *y **se deja correr** ✓
```

### LAS CUATRO DECISIONES · 14/10/2026 · **contestadas por el propietario**

> *** Entrada nueva, *y es la primera vez en la sesion que estas cuatro dejan de estar abiertas. *
> *Se preguntaron **con la opcion recomendada delante**, *medida contra la doctrina del proyecto, *
> *y el propietario contesto: *** «las cuatro, de acuerdo con lo recomendado».** *

```
*** 1) CSRF · PETICIONES SIN `Origin` ***  *** SE DECLARA EL LIMITE *** ✓ *
   *-- *medido: *tres mutaciones con origen ajeno **devolvieron 201**, *y **no hay comprobacion
      de `Origin`** *
   *-- *y **se acepta** *(-- no se rechaza --)* **a condicion de declararlo** en el dictamen *
      *-- *porque **rechazar sin `Origin` rompe curl y movil**, *y **el plan ya avisa** contra
      «la conclusion excesiva de SameSite» ✓
*** 2) AMBITO DE LIDL ***  *** REGIONAL DECLARADO *** ✓ *
   *-- *y **`region='28'` SIGUE SIN IDENTIFICAR**: *el propietario **no ha dicho cual es**, *
      *y **no se inventa** *-- *se declara **como lo que es**: *un ambito **regional**, *
      *con **su codigo sin traducir** ⚠️
*** 3) LA LISTA ***  *** ACUMULA *** *-- ¡y **es un cambio de codigo**! ⚠️ *
   *-- *hoy `uuid5(lista_id|clave)` + `ON CONFLICT DO UPDATE` **sustituye** *
   *-- *y **la regla del diario dice lo contrario**: *«*dos comidas legitimas llevan claves
      distintas *** y se registran las dos ***» *
   *-- *asi que **dos operaciones legitimas sobre la lista tienen que acumularse** ✓✓✓
*** 4) `ver_lista` ***  *** SE DECLARA LA EXCEPCION *** ✓ *
   *-- *es un GET que escribe (`marca_visita`: `INSERT ... ON CONFLICT DO UPDATE SET vista_en =
      now()`), *medido con `scripts/auditar_gets_que_escriben.py` ✓
   *-- *y **no se mueve a POST** *-- *se **declara** ✓
```

- **Siguiente comando**: *** ninguno: *las cuatro estan hechas** *** ✓
  ```
  *** 1) CSRF ***      *se declara el limite, *y esta escrito* ✓
  *** 2) LIDL ***      *ambito regional declarado*, *y `region='28'` SIN IDENTIFICAR, *dicho asi* ✓
  *** 3) LA LISTA ***  *** ACUMULA ***: *migracion `020_la_operacion_de_la_linea.sql`, *
     *`anade_linea` y `lineas_de` con la columna, *`ya` filtrando por ella *(-- y por `None` --), *
     *el id con `traspaso.id_de_linea`, *y *** seis ensayos *** en `tests/test_la_lista_acumula.py` ✓✓✓
  *** 4) `ver_lista` *** *se declara la excepcion* ✓
  ```
- **Evidencia de las cuatro**: `docs/investigaciones/la-lista-que-acumula-media-hecha.md`,
  y **`tests/test_la_lista_acumula.py`** *(-- el ensayo que prueba que **dos operaciones
  sobre lo mismo COEXISTEN** --)*

### B05 · 13/10/2026 · **sin codigo todavia** · ocho rondas de lectura, y las seis clausulas ya estaban

- **Cambio o hallazgo nuevo**: **las SEIS clausulas del criterio de B05 ya estan en el proyecto, y cinco con su
  razonamiento escrito.** *Y en tres niveles: **el razonamiento en los docstrings**, **la garantia en el esquema**,
  y **la prueba con el nombre de la frase del plan**.*

  ```
  1) RECIBO Y HUELLA             -> `core/traspaso.py`: `Operacion(propietario, receta_id, version, semana)`
                                    + `clave()` + `id_de_linea(lista_id, clave)`      + 8 ensayos (g12)
  2) CONFLICTO, NO EXITO FICTICIO -> `lista_linea.id uuid PRIMARY KEY` -- LA BASE IMPIDE la fila repetida,
                                    asi que no hay carrera de «¿ya existe?»             + test_quitar_dos_veces_...
  3) CONCURRENCIA Y MEDIA LISTA   -> `borrado_en` + indice parcial + purga a 30 dias, y el DDL lo RAZONA:
                                    «si dos moviles borran y anaden a la vez, una fila borrada reaparece...
                                     con una marca, no» / «borrar media lista sin querer... reversible»
  4) RESERVAS DE DESPENSA         -> `017_la_despensa.sql`: la regla EN EL DDL («no hay ninguna clave ajena a
                                    `compra`, ni ningun disparador que escriba aqui»)    + 9 ensayos (f11)
  5) CALCULO INCREMENTAL DEL PLAN -> la previa y quitar del plan                        + 11 ensayos
  6) DESTINO DISTINTO             -> B04 (`014_la_linea_sin_destino.sql`)
  ```

  **Y dos de los ensayos son las restricciones del propietario, literales**:
  *`test_no_hay_ninguna_funcion_que_sume_una_compra`* («compra no es consumo») y
  *`test_kg_y_ud_no_se_restan_y_se_dice_por_que`* + *`test_una_unidad_que_no_se_conoce_no_se_resta`*
  («no inventes equivalencias» -- **y no solo no las inventa: dice por que**).
  *Y `test_un_ingrediente_escrito_a_mano_no_entra_y_se_dice`, que es la misma doctrina.*

  **Y la idempotencia del traspaso esta razonada**: *«"repetir no duplica" y "otra semana si" **no se pueden cumplir
  a la vez mirando las lineas de la lista** -- dos semanas con los mismos ingredientes producen lineas identicas.
  **Asi que la identidad es de la OPERACION, no del resultado**: receta + version + semana. **Y la clave la calcula
  el servidor**, porque si la mandara el cliente, **dos pestañas con fechas distintas escribirian dos veces**.»*

- *** Y EL ENSAYO, HECHO *** *(ronda 276, commit `4d4165a`)*: *** 8 ensayos *** en
  `tests/test_b08_la_prevision_no_inventa.py` -- *y **el proyecto pasa de 2025 a 2033 pruebas.** *
  ```
  *la ruta existe y pide `desde`/`hasta` · va ANTES del id · *** solo se convierten `g` y `kg` ***
  (y `ml`/`ud` NO, con su motivo escrito) · `sin_dato` lleva el TEXTO · *** la suma es `diario.resumen`
  y no una copia *** · `de_ficha` calcula nutriente a nutriente · y *** la prevision NO escribe ***,
  comprobado SOBRE EL ARBOL SINTACTICO: ni `apunta(`, ni `INSERT`, ni `UPDATE`, ni `DELETE`, ni `commit(` *
  ```
  *** -> o sea: «compra no es consumo» esta fijado por un ENSAYO, y no por un comentario. ***

- *** Y UNA LECCION DE METODO, que costo tres fallos y vale para todo lo escrito: ***
  *** los `***` y las mayusculas de MIS documentos son enfasis mio, y NO texto literal del codigo. *** *
  *Lo buscaba asi: «NUTRIENTE A NUTRIENTE, NO EN BLOQUE» y «la densidad»; *y el codigo dice
  «nutriente a nutriente, no en bloque» y «la **densidad**». *
  *** -> y el arreglo quedo en el ensayo, con su motivo: *** *«las palabras se buscan sueltas y no en frases:
  el docstring lleva marcas de enfasis (`**densidad**`) que parten las frases, y un ensayo que dependa del
  marcado se rompe al reescribir el comentario.» *

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` *** 2033 pasan ***, 0 fallan, 0 se saltan. *Y **nada de
  codigo**: ocho rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B05-*.md` (9 documentos) · `core/traspaso.py` · `plataforma/sql/001_esquema.sql`
  (`lista_linea`) · `plataforma/sql/017_la_despensa.sql` · `tests/test_g12_traspaso.py` ·
  `tests/test_fase2_f11_despensa.py` · `tests/test_la_previa_del_plan.py` · `tests/test_quitar_del_plan.py`
- **Pendiente o límite exacto**: **ninguno: B05 esta LEIDO, con las seis clausulas comprobadas EN LOS SITIOS DONDE SE
  DECIDE.** *Y las tres preguntas que quedaban abiertas tienen respuesta con el codigo delante:*

  ```
  ¿el `linea_id` repetido PISA, IGNORA o LEVANTA?   -> *** PISA *** (`ON CONFLICT (id) DO UPDATE`),
                                                      y pisa CON EL CONTENIDO NUEVO (cantidad, nota).
  ¿y la carrera de dos moviles?                     -> RESUELTA con `COALESCE`: si `cadena_elegida` llega
                                                      NULL, SE QUEDA LA QUE HABIA. *Y el docstring lo dice en
                                                      los dos sentidos: «no puede borrar la tienda que se
                                                      eligio despues en otro movil» / «ponerla es ponerla».*
  ¿y si la linea estaba borrada?                    -> `borrado_en = NULL`: volver a subirla LA RESUCITA.
  ```

  *Y `COALESCE` aparece **14 veces** en `almacen.py`: **no es un caso aislado, es la doctrina del proyecto** --
  **«no llega» y «llega vacio» son dos cosas distintas**.* *La misma que la columna `cantidad` de la despensa que
  admite NULL, `sin_precio`, y `diario.fuente_dato`: **cuatro sitios donde el proyecto distingue «no se sabe» de
  «es cero»** -- *que es la respuesta escrita a «no inventes».*

- **Siguiente comando o acción**: **B05 queda cerrado como lectura; lo que sigue es B06** (*«Nutricion por campo,
  cadena y universo»*, plan:269), *con el mismo metodo: `ls` de la zona · el fichero que el titulo nombra · los
  nombres de los ensayos · y `grep` al final, con las palabras del codigo.*

  **Y de B02 siguen sus tres cosas** (la cobertura de Carrefour y Alcampo -- que es **diseño, no copia** --, la
  captura acotada real, y la decision del navegador del propietario).

  **Y el metodo, que es lo unico que cambia entre B02 y B05**: *B02 tardo **diez rondas** y produjo **nueve
  correcciones** de mis conclusiones -- porque empezo con **un `grep` de mis palabras**. B05 empezo con **`ls` de
  la zona**, siguio por **el fichero que el titulo del paquete nombraba** (`core/traspaso.py`), y leyo **los
  nombres de los ensayos**. *** `ls` · el fichero que el titulo nombra · los nombres de los ensayos · y `grep` al
  final, con las palabras del codigo. ***

### B06 · 13/10/2026 · **sin codigo todavia** · ocho rondas, cero correcciones, y las cinco clausulas estaban

- **Cambio o hallazgo nuevo**: **las cinco clausulas del criterio tienen respuesta, y ninguna hubo que inventarla.**

  ```
  1) EL INVENTARIO DE CAMPOS        -> 21 ensayos en `test_dia_nutricion.py`, campo por campo
                                       (ingredientes · kcal/macros · fibra/sal · pesos · cantidades · origen
                                        · conservacion · descripcion · fechas · ausente · error)
  2) NATIVO / ENRIQUECIDO / MANUAL  -> `core/diario.py:52`: **`fuente_dato TEXT NOT NULL`**
                                       + `l34: FUENTES = (ETIQUETA, FICHA, ESTIMADO, DESCONOCIDO)`
                                       + `ValueError` si no esta en la lista. Y `core/derive.py` (`enriquecer`).
  3) LOS CINCO MOTIVOS              -> «ausente» (`test_sin_tabla_no_hay_campo`) y «error»
                                       (`test_nutrientes_invalidos_no_se_publican`) con ensayo; **«no aplicable»
                                       en `core/alimentos.py`** (tres respuestas, no dos); **`DESCONOCIDO`** en
                                       `FUENTES`; y **«pendiente» en `config.py:35` y `embeddings.py`**.
  4) LA COLA CON PRESUPUESTO        -> `core/manifiesto.py`: `huella()` (sha256 corto de cada fichero de gold),
                                       `_fuentes()`, `_version_politica()` (sha256 del yml de alcance).
                                       *** Y el patron de la cola con checkpoint, entero, en `embeddings.py`
                                       (`previos` se saltan, `pendientes` por lotes). ***
  5) Y EL HISTORICO DE FICHA        -> `manifiesto`: «por cadena, **la fecha de su captura**», y la version del
                                       alcance. Y su frase: *«sin eso, dos catalogos distintos parecen el mismo,
                                       y **una comparacion puede ser exacta y estar comparando cosas distintas**»*.
  ```

  **Y lo que B06 deja claro del proyecto, que es lo que valia la pena**: *** «no se sabe» es un VALOR, no un
  hueco *** -- *y esta escrito **NUEVE VECES**, en nueve modulos, de nueve formas:*
  *`cantidad` que admite NULL · `sin_precio` · `fuente_dato NOT NULL` · `COALESCE` en `anade_linea` · el «mezcla»
  de `alimentos.py` · `test_un_cero_no_se_confunde_con_no_haber_dato` · `unidad_canon` (sin unidad no se calcula)
  · `FUENTES`+`ValueError` · y **`DESCONOCIDO` dentro de la lista**.*
  *** No es una regla que el proyecto cumpla: es la forma que tiene. ***

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: ocho rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B06-*.md` (8 documentos) · `core/alimentos.py` · `core/derive.py` ·
  `core/diario.py` · `core/manifiesto.py` · `core/embeddings.py` · `tests/test_dia_nutricion.py` (21 ensayos)
- **Pendiente o límite exacto**: **ninguno de lectura.** *Lo que queda de B06 es la pregunta de siempre al
  terminar de leer: **si algo de lo que hay necesita cambiarse** -- y no se ha respondido, porque **no se ha
  mirado con esa intencion**.*
- **Siguiente comando o acción**: **B07** (*«Recetas con contenido, versiones y cocina»*, plan:~283), *con el
  metodo: `ls` de la zona · el fichero que el titulo nombra · los nombres de los ensayos · y `grep` al final.*

  **Y el contraste, que ya es el tercero y es lo unico que hay que recordar**:
  ```
  B02:  diez rondas, NUEVE correcciones de mis conclusiones -- empezo con un `grep` de MIS palabras
  B05:  nueve rondas, CERO correcciones -- empezo con `ls` y por el fichero que el titulo nombraba
  B06:  ocho rondas, CERO correcciones -- igual
  ```

### B07 · 13/10/2026 · **sin codigo todavia** · siete rondas, cero correcciones, y las seis clausulas localizadas

- **Cambio o hallazgo nuevo**: **las seis clausulas del criterio tienen respuesta, y ninguna hubo que inventarla.**

  ```
  1) EL EDITOR DE RECETA -> core/recetas.py: crear/actualizar/versiones/leer/listar/archivar
                            + tests/test_editar_receta.py y test_detalle_receta.py
  2) LA IMPORTACION      -> core/importar_receta.py: `comprueba_fuente(url) -> Permiso` con **CUATRO MOTIVOS
                            SEPARADOS** («no es una direccion» · «el esquema no vale» · «el host no esta
                            declarado» · «no tiene host»), `ESQUEMAS = (http, https, file)`, `file` exige ruta,
                            `razon_declarada` (LA ATRIBUCION viaja con el permiso), y `class Borrador` = «LA
                            PREVIA, QUE NO ESCRIBE». *** Y `FUENTES` EMPIEZA VACIA: «nada esta permitido hasta
                            que se declare» -- y «un importador que por defecto acepta cualquier cosa no tiene
                            politica de fuentes: tiene la politica de que todo vale, escrita en ningun sitio». ***
                            *Las guardas de RED (redirecciones, tamano, timeout) son de `core/fetch.py` (`timeout:
                            int = 25`), no de aqui -- y no se dice que falten.*
  3) EL PLAN             -> core/recetas.py: `planificar`, `plan(desde, hasta)`, `quitar_del_plan`, y
                            *** `escala(ingredientes, de_raciones, a_raciones)` *** -- la escala es RELATIVA, y
                            por eso la misma receta va al plan con raciones distintas cada vez: «RACIONES POR
                            OCURRENCIA». *«Semana» esta en la API de recetas y en cinco ficheros del frontend.*
  4) LA COCINA           -> core/cocina.py: `class Cocina` y `class Temporizador`, y *** el temporizador NO es
                            una cuenta atras: es una HORA DE FIN *** («se guarda `empepezo_en` y `minutos`, y
                            reanudar es volver a leer» -- y **funciona sin conexion porque no hay nada que
                            consultar**). *** Y «SIN DECLARAR CONSUMO» es ESTRUCTURAL: `cocina.py` solo importa
                            `re`, `dataclasses` y `datetime` -- NO IMPORTA EL DIARIO, asi que NO HAY CAMINO. ***
  5) Y LA VERSION        -> `versiones()` + `test_editar_dice_en_voz_alta_que_crea_version_nueva`
  6) Y LA ACEPTACION     -> «CINCO RECETAS CON DATOS, edicion, version, importacion permitida, cocina, recarga y
                            cambios de semana; NO CERRAR POR ENTRAR A CINCO RUTAS VACIAS»
  ```

  **Y lo que B07 deja claro, con su cita mas fuerte**: *** «no decidir es decidir» *** -- *y la solucion que el
  proyecto elige es **que la lista empiece VACIA**, porque «la regla **no se deja al cuidado de quien escribe**:
  **se pone en el camino**». *Es **la sexta forma de imposibilidad** de la sesion: `id uuid PRIMARY KEY` ·
  `fuente_dato NOT NULL` · `FUENTES` vacia · `ON CONFLICT` · la despensa sin clave ajena a `compra` · y **`cocina.py`
  sin importar `diario`**.*

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: siete rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B07-*.md` (7 documentos) · `core/cocina.py` · `core/importar_receta.py` ·
  `core/recetas.py` · `core/traspaso.py` (`_de_quien`) · `core/fetch.py` · `tests/test_editar_receta.py` ·
  `tests/test_detalle_receta.py`
- **Pendiente o límite exacto**: **ninguno de lectura.** *Lo que queda es la pregunta de siempre al terminar de
  leer: **si algo de lo que hay necesita cambiarse** -- y no se ha respondido.*
  *Por confirmar, y sin decir que falte*: que el recorrido de **cinco recetas con datos** se pueda hacer de verdad
  (*la aceptacion del paquete*) -- *que es lo unico de B07 que **no se lee: se ejecuta**.*
- **Siguiente comando o acción**: **B08** (*«Calorias integradas pero personales»*, plan:291), *con el mismo metodo.*

  **Y el contraste, ya con tres**:
  ```
  B02:  diez rondas, NUEVE correcciones de mis conclusiones -- empezo con un `grep` de MIS palabras
  B05:  nueve rondas, CERO correcciones
  B06:  ocho rondas, CERO correcciones
  B07:  siete rondas, CERO correcciones
  ```

### B09 · 13/10/2026 · **sin codigo todavia** · seis rondas · **y las cinco clausulas tienen respuesta (no hay ausencia)**

- **Cambio o hallazgo nuevo**: **el «completo» del titulo no es una carencia: es una negativa razonada -- y los
  veredictos del codigo no son los que el plan nombra. Y la quinta clausula esta, con nombre de funcion.**

  ```
  5) LA PROHIBICION DEL ORDINAL -- *** HECHA ***
     El plan dice: «NO MODIFICAR grupos de listas historicas POR ORDINAL» -- y *** «ordinal» NO APARECE en ningun
     ensayo ***. La PROPIEDAD que la prohibicion protege SI:
       `tests/test_b03_herencia_con_dos_zonas.py::test_lo_que_no_cambia_conserva_su_numero`  (un ensayo DE B03)
         «**El caso que importa de verdad**: lo que era un grupo y sigue siendo el mismo, conser[va su numero].
          *Es para lo que existe `estabiliza`, y es lo que hay que proteger.*»
         con su mensaje: *** «un grupo que no cambia tiene que conservar su numero» ***
     *** Y la funcion es `core/grupos_ids.py::estabiliza(hoy, ayer)` *** -- y el ensayo la usa **indexando por
     `clave`** (`lidl:1`, `dia:9`, NO por posicion) **y con `zip(..., strict=True)`**: *si las dos listas no miden
     lo mismo, REVIENTA en vez de emparejar mal.*
     *** Y `test_banco_verdad.py::test_el_id_es_ESTABLE_y_distingue_fichas` es la misma propiedad, otra vez. ***
  ```

  *** Y la regla que estas rondas dejan escrita, y que sirve para lo que falta: ***
  ```
  EL PLAN NOMBRA LAS PROHIBICIONES POR SU SINTOMA   -- «por ordinal», «no neutraliza formato incompatible»
  EL CODIGO LAS PRUEBA POR SU PROPIEDAD             -- «el id es estable», «es alternativa, no identidad»
  ```
  *Las cuatro veces que una clausula no aparecio por su palabra, **la palabra del plan no estaba y la propiedad si**:
  «por ordinal» -> **estable/conserva/no cambia** · «no neutraliza formato incompatible» -> **`ABSTIENE`** ·
  «distinto no acredita mismo articulo» -> **`probable y nunca exacto`** · «separar lo previsto de lo real» ->
  **`_con_precios`, «separar coste de lo usado del desembolso por envases»**.*

  ```
  1) REUTILIZAR (Y SER INDEPENDIENTE)
     `core/oraculo_reparto.py` (164 lineas) -- *** «INDEPENDIENTE QUIERE DECIR INDEPENDIENTE: este modulo NO
     IMPORTA NADA de `plataforma/api/cesta.py`» ***. Y su razon: «si los dos coinciden, es porque LOS DOS CALCULAN
     BIEN, no porque COMPARTAN EL MISMO CODIGO». -> *el oraculo es un SEGUNDO CALCULO, no una copia.*
     *** Y es, escrita como criterio, la herramienta que esta sesion ha usado a mano: comparar los seis
     colectores, los ocho fabricantes, `despensa` con `cocina`. ***

  2) EL «COMPLETO» -- NO CUBRE `umbral`, Y A PROPOSITO
     Su docstring: «**No cubre `umbral`** («5 EUR dto comprando 20 EUR»), y a proposito: el texto del folleto no
     [dice si el] umbral es del producto o del ticket entero, y el motor ha elegido una lectura SIN PUBLICARLA.
     **13 de octubre de 2026: dos lineas distintas de 12 EUR con esa oferta dan 2400 con la lectura del motor y
     1900 con la del ticket. Mientras eso no se decida, un oraculo que lo cubriera estaria ELIGIENDO UNA DE LAS
     DOS LECTURAS Y LLAMANDOLA VERDAD.»** *** -> el oraculo prefiere estar incompleto antes que mentir. ***

  3) LOS VEREDICTOS -- *** SON CINCO, y el criterio nombra otros cuatro ***
     `core/identidad.py:33`: `EXACTO` · `PROBABLE` · `ALTERNATIVA` · `CUARENTENA` · `ABSTIENE`
     *El criterio dice: `exacto` · `familia` · `alternativa` · `desconocido`.*
     *** Y `ABSTIENE` es la doctrina convertida en VEREDICTO: el sistema puede decir «no me pronuncio», y eso es
     un RESULTADO, no un fallo -- que es lo que la regla del EAN necesita: «cuando el formato no cuadra, no elige:
     se abstiene». *** *Y `CUARENTENA` es su compañera: las dos son «no ahora», y las dos son estados.*

  4) Y EL «NO» CON SU MOTIVO, OTRA VEZ
     `l125 def _presentacion(a, b) -> tuple[bool, list[str]]` (si son comparables **y los motivos**) ·
     `l144 def _no_comparable(motivos)` -- *** no se puede llamar sin decir por que *** ·
     `l51 RE_PACK` -- el «2 x 500 g» y el «pack de 3»: el **neto/pack** del criterio.

  POR LEER: `core/banco_de_pares.py` + `tests/test_banco_de_pares.py` (*** y es donde tienen que estar `familia` y
  `desconocido`, si es que estan ***) · `tests/test_g11_oraculo.py` · y la prohibicion del ordinal.
  ```

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: cuatro rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B09-*.md` (4 documentos) · `core/oraculo_reparto.py` · `core/identidad.py` ·
  `tests/test_identidad.py` · `tests/test_banco_de_pares.py`
- **Pendiente o límite exacto**: **el banco de pares entero** (clausula 2) y **la prohibicion del ordinal**
  (clausula 5) -- *y `familia`/`desconocido` sin encontrar en `identidad.py`, **sin decir que falten**.*
- **Siguiente comando o acción**: **`tests/test_banco_de_pares.py`** *-- el paso (3) del metodo: los nombres de los
  ensayos son el contrato.*

### B10 · 13/10/2026 · **sin codigo todavia** · siete rondas · **cerrado, y la restriccion del dueno LOCALIZADA**

- **Cambio o hallazgo nuevo**: *** LA RESTRICCION DEL PROPIETARIO NO ERA UNA SOSPECHA: ERA UN DEFECTO, Y ESTA
  ARREGLADO, ESCRITO Y PROBADO. *** *Y la pregunta que quedaba -- «¿afecta a AMBOS puentes?» -- tiene **dos
  respuestas en el codigo**.*

  ```
  1) LOS ESTADOS           `cambia_linea` + `SIN_CAMBIAR = object()`              *cuerpo POR LEER*
  2) LAS LISTAS            *** HECHO *** -- `crea_lista(usuario_id, nombre, es_de_casa=False)` · `listas_de` ·
                           `papel_en` · `comparte` · `lineas_de`
  3) BUSCAR Y FILTRAR      *** POR MIRAR *** -- «marca/formato/EAN y filtros utiles»
  4) LA PAGINACION         *** MEDIDA EN LAS DOS DIRECCIONES ***
                           *HAY*: `main.py:340`/`477` `limite: int = Query(...)` **con cotas** · `main.py:167 def buscar(q: str = "",
        cadenas: str | None = None, limite: int = 40, ...)` -- *** con FILTRO (`cadenas`) *** · y `main.py:200 def
        busca(que: str)`
        *NO HAY*: `offset` (0 en `cesta.py`) · `pagina` (0) · `por_pagina` (0) · `siguiente` (0)
        *** y `cursor` aparece UNA SOLA VEZ en la API: `almacen.py:122 def cursor()` -- y es el cursor DE
        POSTGRESQL, no el de la paginacion ***
        -> *el criterio pide «version/cursor» **por una razon que el mismo dice**: «feedback sobre cambios del
        catalogo».*
 6) Y LA DUREZA           *** HECHO, y con LOS DOS PUENTES LOCALIZADOS ***
      `tests/test_fase2_f07_dos_sesiones.py` (5): `test_la_cantidad_vieja_no_gana_por_llegar_despues` ·
      `test_el_tachado_gana_el_primero_aunque_llegue_segundo` · `test_tachar_dos_veces_no_es_un_error` ·
      *** `test_destachar_gana_siempre_SIN_MIRAR_LA_HORA` ***
      *** Y la regla esta en `plataforma/api/almacen.py:415-448`, con EL DEFECTO ESCRITO: ***
        «`momento` es la hora del MOVIL, no la de llegada... *** que si no el orden de los hechos se lo inventa el
         servidor ***»
        `tachado_en = LEAST(COALESCE(tachado_en, %s), %s)`      <- «YO LO HICE PRIMERO»: GANA EL PRIMERO
        `cantidad_en = GREATEST(COALESCE(cantidad_en, %s), %s)` <- «ESTE ES EL VALOR DE AHORA»: GANA EL MAS NUEVO
        y el comentario cuenta el fallo: «Esto era `cantidad = %s` con el comentario "el ultimo, a proposito", y ese
        "ultimo" era EL ULTIMO QUE LLEGA -- asi que dos personas cambiando la cantidad sin cobertura SE PISABAN, y
        GANABA LA DE LAS 17:50 QUE LLEGO A LAS 18:31.»
        *** Y las dos reglas opuestas estan razonadas: «GREATEST, al contrario que el tachado, que usa LEAST. NO ES
        UNA INCOHERENCIA: tachar es "yo lo hice primero" y gana el primero; la cantidad es "este es el valor de
        ahora" y gana el mas nuevo. DOS REGLAS OPUESTAS, CADA UNA CON SU MOTIVO.» ***
      *** Y LOS DOS PUENTES: ***
        `main.py:1608` «*** Y AQUI ESTA LA CONSOLIDACION, QUE ES LA MISMA QUE LA DEL OTRO PUENTE ***» y `l1669`
        `almacen.anade_linea(...)`  ·  `recetas.py:247` «*** la idempotencia esta DOS VECES: `traspaso` impide la
        segunda operacion, `almacen.anade_linea` YA ES UN UPSERT ***»
        -> **una capa impide repetir el ENUNCIADO, y la otra duplicar el RESULTADO** (B05, clausula 2).
  ```

  *** Y los ensayos del gasto contestan la clausula entera, y traen la doctrina por LOS DOS LADOS otra vez: ***
  ```
  tests/test_g05_gasto.py (14)
    test_suma_lo_conocido_y_DECLARA_LO_QUE_FALTA            <- el criterio, literal
    test_sin_ningun_importe_el_total_es_None_Y_NO_CERO       <- *** la doctrina ***
    test_cero_explicito_SI_es_un_importe_conocido            <- *** ¡y el otro lado! ***
    test_una_linea_sin_fecha_NO_SE_COLOCA_EN_EL_PERIODO_DE_HOY   <- no inventar fecha
    test_un_periodo_desconocido_es_un_ERROR_Y_NO_UN_SILENCIO
    test_lo_conocido_y_lo_desconocido_se_suman_POR_SEPARADO
    test_la_COBERTURA_cuenta_LINEAS_Y_NO_SOLO_COMPRAS        <- la cobertura con SU unidad
  tests/test_la_estimacion_de_la_lista.py (3)
    test_DIVIDIR_LA_COMPRA_EN_LINEAS_NO_CAMBIA_EL_TOTAL       <- *** y es la «suma de partes igual al total»
                                                               del oraculo de B09, aplicada al coste ***
  ```
  *** Y el par del diario y el del gasto son EL MISMO PAR ***: `test_un_nutriente_..._sin_dato_y_no_cero` +
  `test_un_cero_publicado_es_un_dato` (B08) **y** `test_sin_ningun_importe_el_total_es_None_y_no_cero` +
  `test_cero_explicito_SI_es_un_importe_conocido` (B10) -- *** cuatro ensayos, dos modulos, la misma distincion, y
  aqui con CONSECUENCIA DE DINERO ***. *Y `test_la_cobertura_cuenta_LINEAS_Y_NO_SOLO_COMPRAS` es la exigencia de
  B11 («declara MEDIDA y UNIDAD») **aplicada a un numero**.*

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: cuatro rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B10-*.md` (2 documentos) · `plataforma/api/almacen.py` ·
  `plataforma/api/main.py:340,477` · `tests/test_g05_gasto.py` · `tests/test_la_estimacion_de_la_lista.py` ·
  `tests/test_lista_de_casa_unica.py` · `tests/test_pasillos.py` · `tests/test_pasillo_pegajoso.py`
- **Pendiente o límite exacto**: **(1)** el cuerpo de `cambia_linea` y su ensayo de dureza; **(3)** buscar/filtrar
  («marca/formato/EAN»); **(4)** la paginacion por version/cursor -- ***medida: hay `limite` con cotas, y no hay
  `cursor`/`version`/`offset`***. *Y sigue abierta la pregunta de siempre: **si algo de lo que hay necesita
  cambiarse**.*
- **Siguiente comando o acción**: **`tests/test_pasillos.py` y `test_pasillo_pegajoso.py`** *-- el paso (3) del metodo:
  los nombres de los ensayos son el contrato.* *** Y «pegajoso» es el nombre que hay que entender: el orden por
  pasillos que se recuerda. ***

### B11 y B12 · 13/10/2026 · **sin codigo todavia** · **el principio mas fuerte de la sesion, y su receta con REGLA DE PARADA**

- **Cambio o hallazgo nuevo**: *** «LO QUE NO SE OBSERVO NO SE PUEDE DIBUJAR COMO SI SE HUBIERA OBSERVADO.» ***
  *Es el principio del que **salen las veinte formas anteriores** de la doctrina, y **esta en
  `plataforma/web/app/src/logica/chispa.ts`** -- el modulo que decide **que se dibuja en una chispa y que no.***

  ```
  `logica/chispa.ts` (114 lineas) -- «*** Sin uPlot y sin DOM: SE PUEDE PROBAR ***. *compilar no es acertar*.
  Las tres salen del mismo principio: LO QUE NO SE OBSERVO NO SE PUEDE DIBUJAR COMO SI SE HUBIERA OBSERVADO.»
    - *** Un hueco es un hueco ***: un `null` entre dos precios SE CONSERVA como `null`.
    - *** Una fecha ilegible no es 1970 ***: el punto se descarta y se cuenta.
      *(«antes iba al origen del eje Y ARRASTRABA LA ESCALA»)*
    - *** De una serie vacia no se infiere nada ***: dice que NO HAY SERIE, no que haya un solo dia.
  *** Y las tres estan PROBADAS: `tests/cocina.test.mjs:49,61,68` *** (+ `:81` «un valor no finito es un hueco,
  no un cero» y `:89` «la tabla lista los huecos, y los lee como "sin dato"»).
  *** (y el fichero se llama `cocina` porque los ensayos del frontend estan agrupados POR PAGINA, no por modulo) ***

  `componentes/Chispa.tsx` -- «una serie de precio POR UNIDAD, SIN EJES», y:
    *** «Si la serie mezcla unidades, NO SE DIBUJA UNA LINEA QUE LAS JUNTE.» ***
    `if (!unidades.dibujable && unidades.motivoUnidad) return <p>{unidades.motivoUnidad}</p>`
    -> *** veredicto + motivo, PINTADO en la pantalla: la misma forma que `Permiso(ok, reason)` (B07) y
    `_presentacion -> tuple[bool, list[str]]` (B09). TERCERA VEZ. ***

  `api/formato.ts` (236 lineas) -- *** LA DOCTRINA EN EL FRONTEND: ***
    «La regla que manda aqui: un dato que no tenemos es "no lo se", NUNCA UN CERO. Un 0,00 EUR se lee como
     "gratis" y una letra vacia como "malo"; LAS DOS COSAS SERIAN MENTIRA. ... NINGUNA TIENE UN VALOR POR
     DEFECTO NUMERICO.»
    `export const NO_LO_SE = 'no lo sé'` · `sufijoUnidad(unidad)` · `eurosUnidad(...)` -- *** «la unidad» de B11 ***
    «El dinero llega en CENTIMOS ENTEROS y se pasa a euros SOLO AL PINTAR. No se redondea antes de tiempo.»
  ```

  *** Y B12: el documento que pide YA EXISTE, y es `docs/SUPERAPP-COMPETENCIA-Y-REA.md` (104 lineas, 6 secciones) ***:
  ```
  §1  *** once apps tabuladas, con CUATRO columnas: Referencia · Fuente oficial · Capacidad documentada ·
      «QUE NO ASUMIR» *** (Bring! · AnyList · Listonic · Soysuper · Paprika · Samsung Food · Mealime ·
      Cookidoo · Cronometer · YAZIO · MacroFactor)
  §4  *** «Investigacion minima que produce una mejora» -- OCHO REGLAS, y las cuatro categorias del encargo:
      «Demostrado documental / demostrado por ejecucion / HIPOTESIS / DESCONOCIDO» ***
      + «La misma matriz de casos para referencia y Cesta» (*** el oraculo de B09, aplicado a la investigacion ***)
      + «No extraer catalogos de recetas, marcas, ilustraciones, textos largos ni codigo privado»
      + *** «REGLA DE PARADA: cuando se puede especificar una mejora COMPROBABLE con las fuentes
        SUFICIENTES» *** -- *que es lo que permite no estudiar un binario enorme.*
  ```
  *** Y el plan lo dice DOS VECES ***: *«una funcionalidad anunciada en una web **no acredita su mecanismo
  interno**»* (B12) **y** *«estas referencias prueban funcionalidades **documentadas**, no el algoritmo»* (§8).
  *** Y la seccion 8 anade: «NO se han descargado ni decompilado las apps comerciales», y el laboratorio
  (`F:\EspacioCodigo\ProyectoServidor\rea-sandbox`) es de FUERA de este proyecto, COMPARTIDO con otros encargos. ***

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: tres + cuatro rondas de lectura.*
- **Evidencia**: `docs/investigaciones/B11-*.md` (3) y `B12-*.md` (2) · `logica/chispa.ts` ·
  `componentes/Chispa.tsx` · `api/formato.ts` · `tests/cocina.test.mjs` · `docs/SUPERAPP-COMPETENCIA-Y-REA.md`
- **Pendiente o límite exacto**: **ninguno de los dos tiene ausencia.** *El unico cabo de B11 era «donde estan las
  pruebas de las tres reglas», y **estan** (`cocina.test.mjs`). *Y de B12 queda **escribir un informe por
  capacidad** -- y la capacidad la elige el plan (**menu, porciones/diario, flujos de lista**), *que son **las tres
  que esta sesion ya ha leido a fondo**.*
- **Siguiente comando o acción**: **B13** (*«UX con datos reales y pruebas de recorridos»*, plan:338), *cuyo
  criterio ya esta leido y trae un defecto con nombre*: *** «inventariar rutas y componentes montados, EVITAR
  ARREGLAR `Nav` SI SE SIRVE `SUITE`» *** -- *y su ultima frase es el encargo otra vez: «no "cerrar A09 entero" con
  vacios unicamente».*

### B14 y B15 · 13/10/2026 · **sin codigo todavia** · y las dos tienen su contrato **medido**

- **B14 · Seguridad, copias y operacion** -- *** tres de los cinco bloques, contestados con nombre de ensayo. ***

  ```
  EL FICHERO:  `tests/test_fase2_f04_csrf.py` (116 lineas, 11 de octubre) -- CINCO ensayos:
    test_un_origen_ajeno_no_recibe_permiso
    test_un_origen_configurado_si_recibe_permiso
    *** test_el_preflight_de_un_origen_ajeno_tampoco_lo_autoriza ***
    test_la_cookie_va_con_httponly_y_samesite_lax
    *** test_ninguna_ruta_que_muta_es_un_get ***

  Y CONTRA EL CRITERIO, FRASE POR FRASE:
    «CSRF con sesion real» + «origen permitido/RECHAZADO»  -> los DOS primeros, *** y son un PAR ***
    *** «CORS no sustituye autorizacion de mutacion» ***   -> *** el PREFLIGHT ajeno tampoco autoriza ***
    «misma-site distinto origen»                           -> `Lax`: la cookie NO VIAJA en cruzado
    *** «auditar GET sin cambios» ***                      -> *** `test_ninguna_ruta_que_muta_es_un_get` ***
                                                             *-- no se auditan uno a uno: SE PROHIBE.*
    «no declarar defensa completa por 401 sin cookie»       -> *y el fichero ya evita esa trampa: prueba
                                                             EL ORIGEN, no la ausencia de cookie.*

  LA COPIA (OPERACION.md:459):
    *** «Copia de seguridad, cuando haya algo que perder: EL CRUDO ES LO UNICO IRRECUPERABLE.
        Un `robocopy` semanal de `data\raw` a un disco externo cubre el riesgo entero.» ***
    -> *y B14 pide «copias de PostgreSQL, SQLITE PRIVADOS y metadatos»:*
      *** `data/diario.sqlite` (11 entradas) y `data/recetas.sqlite` (42 recetas, 42 del plan, 43 versiones,
      7 traspasos) SON IRREEMPLAZABLES Y NO SON CRUDO *** -- *o sea: **el criterio, aplicado con rigor, los
      incluiria.** *** Y NO SE DICE QUE NO SE COPIEN: se dice que LA DOCUMENTADA NO LOS CUBRE. ***
      *La comprobacion que lo decide (que se copia al disco externo) NO se puede saber desde el repositorio.*

  LOS LOGS Y LA ROTACION:
    `data/runs.csv` -- 6 columnas (`ts,fuente,filas,errores,segundos,ok`), 228 lineas, y crece en cada pasada.
    *** NO HAY SITIO PARA UN SECRETO *** (numeros y un nombre de cadena) -- *comprobado leyendo la cabecera.*
    *** y la ROTACION: NO SE HA VISTO NINGUN MECANISMO *** -- *`scripts/` no tiene nada que nombre
    rota/log/limpi/purga.*
  ```

- **B15 · Aprendizaje reproducible** -- *** la zona es mucho mayor de lo que parecia. ***

  ```
  `plataforma/aprende.py`  -- *** 60 KB ***
  `docs/aprende/`          -- *** 24 capitulos *** (los «diez» de la primera lectura eran los diez primeros
                              alfabeticamente) · de `00-como-usar-este-material` a `98-glosario`
  `tests/test_aprende.py`  -- *** 20 ensayos ***, y varios ESTRUCTURALES («una pagina por documento», «un indice
                              por capitulo», «una sola cabecera por documento», «las tablas llevan su columna en
                              cada celda»)

  Y LA LISTA DE B15, CONTRA LOS CAPITULOS:  ocho de nueve temas tienen capitulo
    fuente->raw->bronze->silver->gold->API  -> `02` + *** `11-servir-los-datos` ***
    evaluacion del algoritmo                -> `05` + *** `12-medir-sin-enganarse` ***
    *** DBT/Dagster: que esta REALMENTE instalado *** -> *** `14-el-stack-explicado` ***
    entidades/unidades/matching             -> `03` · `04` · *** `16-catalogo-fichas-identidad` ***
    costes y promociones                    -> *** `08-promociones-y-anomalias` ***
    *** casos de errores reales ***         -> *** `17-fallos-reales` ***
    cobertura                               -> *** `18-cobertura-real` ***
    *** linaje ***                          -> *** `92-anexo-como-se-investigo` ***
    *** NUTRICION ***                       -> *** NO HAY CAPITULO CON ESE NOMBRE ***

  Y TRES FORMAS NUEVAS DE LA DOCTRINA, en los ensayos y en las secciones:
    *** `test_la_pagina_DE_LO_QUE_NO_ESTA_existe_y_lleva_a_donde_si` ***  <- «no se sabe» hecho PAGINA
    *** `test_el_sitio_NO_PIDE_NADA_POR_RED` ***                          <- nada sale de casa
    *** `test_NADA_EN_LINEA_porque_EL_CSP_DE_CADDY_LO_PROHIBE` ***        <- *** IMPOSIBILIDAD IMPUESTA POR UN
                                                                            SERVIDOR: no es que nadie lo haga,
                                                                            es que NO SE PUEDE ***
    y la seccion 6 de `05-medir-el-emparejador`: *** «La auditoria dirigida: POR QUE FALTA CADA PAR QUE FALTA» ***
      <- *no cuantos faltan: **por que falta cada uno.*** (y la 5: «el sesgo que hay que declarar ANTES de tocar
      el banco»)

  Y LO QUE FALTA DE LAS CUATRO COSAS QUE B15 PIDE POR CAPITULO:  «comando» en 6 de 24 · «salida» en 6 de 24 ·
  «test» en 14 de 24. *** Y ESO PUEDE SER CORRECTO: un capitulo de CONCEPTO no tiene comando, y uno practico si --
  asi que LA CUENTA NO DISTINGUE LOS DOS TIPOS, y decirlo es mejor que contarlo como falta. ***
  ```

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**.*
- **Evidencia**: `docs/investigaciones/B14-*.md` (3) y `B15-*.md` (2) · `tests/test_fase2_f04_csrf.py` ·
  `docs/OPERACION.md:459` · `data/runs.csv` · `plataforma/aprende.py` · `docs/aprende/` · `tests/test_aprende.py`
- **Pendiente o límite exacto**: **de B14**: *la rotacion del log (por mirar), si hay guion de copia en otro sitio, y
  **la pregunta para el dueno: que se copia al disco externo**.* **De B15**: *** «nutricion» sin capitulo *** -- *y
  **es la tercera vez que aparece en una lista del plan sin estar en el codigo** (B08, B15, y el encargo), *y las tres
  en los paquetes del diario.*
- **Siguiente comando o acción**: **B16** -- *«Dictamen por capacidad y puertas finales»* --, *que es **lo unico que
  queda que no sea ejecutar B13.***

- **Y DOS COSAS MAS DE B14, medidas despues** *(el 13/10, en las rondas 255-256)*:
  ```
  *** 1) LA «ROTACION» NO ES UN ROTADOR: ES UNA POLITICA CON SU NOMBRE ***
     `core/storage.py:24`  *** CAPAS_INTOCABLES = ("bronze", "gold") ***
     y `comprueba_borrable(ruta)` *** «REVIENTA si la ruta cae dentro de una capa que NO SE BORRA» ***
     y `l16`: *** «Capas que no se borran nunca. `raw` se puede tirar CUANDO CADUCA -- OCUPA 338 MB» ***
     *** -> y `silver` NO esta en la lista, y se deduce sin forzar: si `bronze` es intocable y `silver`
        sale de el, `silver` SE RECALCULA -- y por eso se puede tirar. ***
     *** -> LA POLITICA ES: LO QUE SE RECALCULA SE PUEDE TIRAR; LO QUE NO, NO. ***
     *** y el codigo es MAS ESTRICTO QUE EL MANUAL: *** *`OPERACION.md:459` nombra UNA cosa («el crudo»),
        y `storage.py` protege DOS (bronze y gold) -- *y `publicacion.py:23` dice por que gold: *** «publicar
        NO BORRA. Un catalogo no se destruye por publicar otro» ***.
     *** y «apartar, no borrar» se ejecuta con un `rename`, y el nombre queda `<cadena>-<fecha>-<motivo>`. ***
     *** y `data/runs.csv` (6 columnas, 228 filas) NO TIENE SITIO PARA UN SECRETO. ***

  *** 2) LAS COPIAS, CON SU DIFF Y SU ORDEN ***
     *** TRES sitios irreemplazables: *** *`data\raw` (copiado) · los dos `.sqlite` del host (NO copiados) ·
        y *** `/app/data` DEL CONTENEDOR (invisible: sin montaje ni volumen) *** *
     *** A) la copia lleva los tres: *** *`robocopy data\raw` + `robocopy data` de `diario.sqlite` y `recetas.sqlite`*
     *** B) y `/app/data` deja de ser invisible: *** *volumen nombrado `datos_api:/app/data` (o un bind a OTRA
        carpeta, para no tener DOS ESCRITORES sobre el mismo fichero)*
     *** Y EL ORDEN, si se aplica: *** *1) sacar el `/app/data` actual · 2) cambiar el compose · 3) `up -d`*
        *** -- y el paso 1 NO se puede saltar, porque el fichero que hay que salvar esta dentro de lo que se recrea. ***
     *** Y SE MIDIO LO QUE HAY DENTRO: *** *`/app/data` tiene *** UN fichero *** (`recetas.sqlite`, 32 KB, 5 recetas
        DE ENSAYO) y *** NO hay `diario.sqlite` *** -- *o sea: **el contenedor no tiene ningun dato real.** *
     *** -> asi que la (B) HOY no pierde nada; y el dia que alguien use la web, si. ***
     *** y NO SE APLICA: recrear un contenedor es del propietario («preserva cambios ajenos»). ***
  ```

- *** Y EL VOLUMEN, APLICADO *** *(ronda 258, y con permiso del propietario)*:
  ```
  *** EL PROBLEMA: *** `/app/data` NO tenia montaje ni volumen, asi que `recetas.sqlite` y `diario.sqlite`
     vivian *** EN LA CAPA DEL CONTENEDOR *** -- *donde `docker compose down` se los lleva y*
     *** `robocopy data\raw` NO LOS VE. ***
  *** Y SE HIZO EN ESTE ORDEN, y el orden es lo que evito perder el dato: ***
     1) `docker cp cesta-api-1:/app/data data\debug\app_data_antes_20261013`  *** <- y NO se puede saltar ***
     2) `plataforma/docker-compose.yml` -> *** `- datos_api:/app/data` *** y el volumen `datos_api`
     3) `docker compose up -d *** api ***`  *(y NO `cesta-api`: **el servicio se llama `api`**)*
        y *** `docker cp` de vuelta ***, porque *** el volumen nace VACIO ***
  *** Y VERIFICADO, por los dos lados: ***
     el montaje: `{"Type":"volume","Name":"cesta_datos_api","Destination":"/app/data","RW":true}`
        *** -- y el bind de `/datos` sigue `ro`: no se toco nada de lo que ya estaba bien ***
     y la aplicacion: *** 5 recetas · `ENTRAR` 200 · las 5 por la API · y la web 200 ***
  *** -> y ahora la copia puede cubrir LOS TRES: `data\raw` · los dos `.sqlite` del host · y el del
     contenedor, que *** ya se ve *** porque esta en un volumen con nombre (`cesta_datos_api`). ***
  *** commit `f040527` *** -- *y es el TERCER commit de codigo de la sesion, y el unico de infraestructura.*
  ```

### B02 · 13/10/2026 · commits `5039b9c`, `fa16f1f` · **cerrado con una fecha, y con la decima correccion**

- **Cambio o hallazgo nuevo**: **Lidl SI esta en el ciclo diario, y la prueba estaba en `run.py`, no en
  `ejecutar.bat`.**

  ```
  `projects/cesta/run.py:40`   *** ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl"] ***
  y el comentario (l35-39): «**Lidl entra aqui, y por eso**: tiene colector, descubrimiento, cola de fichas y
  parser, y `ORDEN` no lo incluia -- que es *** la PRIMERA MITAD DEL PUNTO 189 DE G09 ***; `_en_paralelo` resuelve
  por nombre de modulo, *** asi que anadirlo es una palabra ***; y va AL FINAL porque `ORDEN` tambien es el orden de
  LECTURA de los resultados.»
  y l44-46, EL DEFECTO ESCRITO: «su `main` exige `--html` o `--web` (`required=True`), y aqui se llamaba `main()` a
  secas -- asi que `argparse` salia con [error]. *** EL DIA SEGUIA SIN LIDL, CON UN AVISO EN EL LOG QUE PARECIA UNA
  PRECAUCION. ***»
  y l48: «*** `--escribir` va con `--web` A PROPOSITO ***: es lo que convierte la captura en bronze.»

  *** Y `ejecutar.bat` dice «las cinco cadenas (carrefour, dia, mercadona, aldi, alcampo)» -- y es UN COMENTARIO
  VIEJO: la lista de verdad esta en `run.py`. ***
  ```

  *** Y el hilo de `runs.csv` se cierra con DOS FECHAS ***:
  ```
  el arreglo `5039b9c` (log_run dentro del `--escribir`):  *** 2026-10-13 16:15:27 +0200 ***
  la ultima pasada en `data/runs.csv`:                       *** 2026-10-13 10:48:12 +00:00 (12:48 +0200) ***
     -> *** el arreglo es ~3,5 h POSTERIOR: NINGUNA CADENA HA CORRIDO DESDE EL ARREGLO ***
     -> y por eso `lidl` no tiene fila: *** no es un fallo del registro -- es que el registro nuevo todavia no se ha
        ejercitado. ***
  *** Y QUEDA UNA PREDICCION CON FECHA: *** *mañana a las 06:00 corre la tarea, y si Lidl escribe, aparecera su
  fila. Si NO aparece, entonces SI hay algo que mirar:*
    `Get-Content data\runs.csv -Tail 8 | Select-String lidl`
  ```

  *** Y las tres «contradicciones» se resuelven con una fecha y una linea de codigo: ***
  ```
  «Lidl esta en el ciclo»  vs  «el .bat dice cinco»      -> el .bat es un COMENTARIO viejo; la lista esta en run.py
  «Lidl escribe»            vs  «no tiene fila»            -> NADIE HA CORRIDO DESDE EL ARREGLO
  «hay crudo de Lidl»       vs  «cero pasadas»             -> el crudo es de ANTES DEL ARREGLO
  ```

  *** Y es la DECIMA correccion a mi mismo ***: *la ronda 205 dije «Lidl no esta en el ciclo diario»; **y lo escribi
  con la comprobacion al lado** («leer `projects/cesta/run.py` y ver si la lista esta escrita o se descubre»),
  *y la ronda 206 **la hizo** y **la afirmacion se cayo.** *

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**.*
- **Evidencia**: `docs/investigaciones/B02-*.md` (**32 documentos**) · `run.py:35-48` · `ejecutar.bat:6` ·
  `data/runs.csv` · y las fechas de `5039b9c`
- **Pendiente o límite exacto**: *** UNA PREDICCION CON FECHA, y nada mas. *** *Mañana a las 06:00, `runs.csv` debe
  tener una fila de `lidl`. **Y si no la tiene, entonces si hay un fallo.** *Y **la «segunda mitad del punto 189 de
  G09» YA SE LEYO** (`SUPERAPP-EJECUCION.md:914`, y su fila de tabla la marca `✓✓`)*: **son TRES piezas, y las tres
  estan:***
  ```
  (1) *** Lidl esta en `ORDEN` *** -- «entraba con UNA PALABRA y no estaba»
  (2) *** Su ritmo esta DECLARADO *** -- era un `RITMO.get("lidl", 1.0)` *** IMPLICITO: ***
      *** «un valor que NADIE HABIA ELEGIDO y que NO SE PODIA REVISAR» *** -- y declarado con el **mismo 1.0**:
      *** «no cambia lo que pasa, CAMBIA QUE SE PUEDA VER Y DISCUTIR» ***
  (3) *** Y CON PRESUPUESTO *** -- `--limite` valia **3**, y la cola real son *** 5.026 pendientes:
      1.676 ejecuciones, CUATRO AÑOS Y MEDIO ***; y `LIMITE_POR_EJECUCION = 1000` -> **6 ejecuciones (~1,7 h) -> 6 dias**
      *** y esta IMPLEMENTADO: `projects/cesta/fichas_lidl.py` (y `fichas_carrefour.py`) *** -- *porque el presupuesto
      es de las FICHAS (la cola), no de los precios.*
  ```
  *** Y `fichas_lidl.py` resulta contestar CUATRO clausulas mas del encargo, con su nombre y su motivo *** --
  *y su cabecera las declara: «**con presupuesto, con hash y dejando la proxima revision puesta**».*
  ```
  EL ENCARGO PIDE: «validacion, CHECKPOINTS, backoff, LIMITES, observabilidad y RECUPERACION»
    *** «limites» ***       *** `LIMITE_POR_EJECUCION = 1000` *** -- y su razon: *** «NO HAY BUCLE HASTA AGOTAR:
                            una ejecucion que no termina NO ES PROGRESO, ES UN RASTRO QUE SE QUEDA A MEDIAS» ***
    *** «checkpoints» ***   *** «El *LEASE* manda»: si el proceso se muere a mitad, LA FICHA VUELVE SOLA A LA COLA
                            -- y NO HAY QUE HACER NADA ESPECIAL, *** Y ESO ES LO QUE SE GANA POR HABERLO HECHO BIEN
                            ALLI ***» ***  *-- el lease vive en `core/inventario.py`*
                            *** -> la recuperacion NO es un `try/except`: es UNA PROPIEDAD DE LA COLA ***
    *** «recuperacion» ***  *** `error_temporal` SE REINTENTA -- y NO CUENTA COMO INTENTO FALLIDO DEL PRODUCTO ***
    *** «validacion» ***    el hash del contenido util · la version del parser · la fecha de la proxima revision
    *** y la doctrina, DOS ESTADOS NUEVOS: *** *** «FALLO DE RED Y DATO QUE FALTA SON ESTADOS DISTINTOS» ***
        red -> `error_temporal` (temporal) · fuente -> `no_publicado` (*** «UN DATO SOBRE LA FUENTE, NO UN FALLO» ***)
        *-- decimoquinta vez, y es la parte que PROTEGE: si un fallo de red contara como intento, EL PRODUCTO SE
        MARCARIA COMO MALO POR UN PROBLEMA DE LA RED -- y eso es UN DATO FALSO SOBRE EL PRODUCTO.*
  ```
  *** Y LA COLA, que es donde el *lease* vive: `core/inventario.py`, con su fichero `data/inventario.sqlite` (14,7 MB,
  el mayor del proyecto). ***
  ```
  *** NUEVE ESTADOS, y CINCO SON FINALES: ***
    PENDIENTE · EN_CURSO                                   <- los dos «en marcha»
    *** CORRECTO · PARCIAL · NO_PUBLICADO · NO_ENCONTRADO · EXCLUIDO ***  <- Y LOS CINCO FINALES
    BLOQUEADO · ERROR_TEMPORAL                             <- y los dos «vuelve»
    `l46  FINALES = (CORRECTO, PARCIAL, NO_PUBLICADO, NO_ENCONTRADO, EXCLUIDO)`
  *** y CINCO FORMAS DE TERMINAR, Y SOLO UNA ES «BIEN»: *** *las otras cuatro son FINALES LEGITIMOS, no fallos
  pendientes de arreglar.* *** Decimosexta vez, y es EL MAXIMO del proyecto. ***

  *** Y EL LEASE, CON SUS TRES NUMEROS: ***
    *** `LEASE_MINUTOS = 30` ***  -> *una ficha tomada y no terminada VUELVE A LA COLA A LOS 30 MINUTOS*
    *** `def tomar(con, limite = 50, *, fuentes = [...])` ***  -> *y `tomar` es LA QUE LA SACA*
    *** `EN_CURSO` ***            -> *lo que tiene mientras esta tomada -- y si el proceso muere, se queda ahi
                                    HASTA QUE EL LEASE VENCE, y entonces VUELVE A PENDIENTE SOLA*
    *** -> LA RECUPERACION ES UNA RESTA DE TIEMPO, y NO HACE FALTA CODIGO DE RECUPERACION ***
       *-- sin `finally`, sin `atexit`, sin vigilante: **el proximo que llame a `tomar(...)` la ve otra vez**,
       porque **el lease caduco mientras nadie miraba.***

  *** Y DOS PLAZOS, QUE SON POLITICA Y NO CODIGO: ***
    `REVISION_DIAS = 30` (ordinaria)  ·  *** `REVISION_CONFLICTO_DIAS = 7` (conflicto o cambio observado) ***
    *-- y el comentario dice que **«el contrato la quiere»**: el numero NO es del programador.*
    *** la revision ordinaria es lenta; y LA QUE RESPONDE A UN CONFLICTO ES RAPIDA -- porque UN CONFLICTO ES UNA
    SEÑAL, Y UNA SEÑAL SE MIRA ANTES. ***
  ```
- **Siguiente comando o acción**: **`Get-Content data\runs.csv -Tail 8 | Select-String lidl`**, *despues del proximo
  arranque.*

### B08 · 13/10/2026 · **y NO es 4 de 5: el plan SI pide la vista de previstos**

- **Cambio o hallazgo nuevo**: *** el criterio de B08, literal (`plan:291`): ***
  > *** «Vista de PREVISTOS SEPARADA DEL DIARIO REAL. *Elegir receta versionada, porciones efectivas y comida;
  > consultar snapshot nutricional y cobertura antes de confirmar. *Acceso rapido desde plan/cocina con recibo de
  > consumo y correccion/borrado propios. *** Objetivo OPCIONAL por persona y fecha; *** *** GRAFICAS DE REGISTRADO
  > VERSUS PREVISTO VERSUS OBJETIVO, *** *sin totalizar un dia no completo ni colorear diagnosticos medicos.
  > *Aceptar *** R1=270, media=135 ***, ausencia de energia con proteina conocida, idempotencia, recarga y
  > aislamiento A/B; *** compra nunca genera consumo por si sola. ***» ***

  *** Y LA AUSENCIA ESTA CONFIRMADA POR CUATRO VIAS: ***
  ```
  1) LOS SIETE NOMBRES      -> *«previsto» y «objetivo» no aparecen*
  2) EL FRONTEND (73)        -> *y ninguna coincidencia es del plan*
  3) EL API Y EL NUCLEO      -> *** `previst`/`prevision` dan CERO ***
  4) Y LOS ENSAYOS           -> *** y `R1=270` / `media=135` no estan en ninguno ***
  ```

- *** Y EL PRIMER PASO, LOCALIZADO, que es lo util ***:
  ```
  *** la nutricion de un ingrediente necesita DOS decisiones: ***
    1) el TEXTO de la linea -> un GRUPO    -> *y `/api/buscar` **ya lo hace***: *`grupo_id: 10645`*
    2) *** y el GRUPO -> un PRODUCTO ***     -> *** y falta ELEGIR LA CADENA ***
       *y `/api/buscar` da `producto_id: None` y `nutriscore` -- **y NO `kcal`** (una letra no se suma)*
  *** -> y sin cadena elegida no hay `producto_id`, y sin `producto_id` no hay nutricion. ***
  *** -> Y EL SITIO PARA ESA ELECCION YA EXISTE: `lista_linea` tiene `cadena_elegida`, `autorizado` y
     `autorizado_producto` -- *y es el mismo que usa la lista para «un articulo elegido solo admite
     alternativas autorizadas». ***
  ```

- *** Y LO QUE YA ESTA, QUE ES MATERIA PRIMA ***:
  ```
  *** el ESCALADO ***        -> *** `core/recetas.py:134 escala(...)` ya existe ***, *con `factor = a/de`,*
                                *y **«las dos cifras»**: `raciones` y `raciones_receta`, y `escalada`*
  *** el coste ***            -> *`logica/costeReceta.ts`: «nutricion por racion y coste estimado» (G05)*
  *** la cobertura ***        -> *** el patron esta en `desde-la-compra` ***: `{con_dato, total}` y `sin_dato`
  *** y la grafica ***        -> *`logica/chispa.ts`, con sus tres reglas probadas*
  *** y `core/recetas.py` NO TIENE NUTRICION: *** *32 coincidencias, y ninguna es `nutricion`/`kcal`/`energia`*
  ```

- *** Y LA LECCION DE ESTE PAQUETE, que es una correccion a mi mismo: ***
  *durante varias rondas lo llame «la ausencia del eje de la PREVISION» y lo trate como **una limitacion
  declarada** o **una decision del propietario**. *** Y el plan dice otra cosa: es UNA CLAUSULA, y esta sin
  hacer. *** *
  *** Y NO se marca el objetivo cumplido por eso: queda un paquete del plan a medias, y los numeros del criterio
  (`270`, `135`) sirven para construirlo. ***

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**.
- **Evidencia**: `docs/investigaciones/B08-*.md` (**5 documentos**) · `plan:291` · `core/recetas.py:134` ·
  `logica/costeReceta.ts` · `main.py:1679` (`desde-la-compra`) · `logica/chispa.ts`
- *** Y EL OBJETIVO **FUNCIONA HOY** *** *(rondas 282-283, y **sin escribir una linea de codigo**)*:
  ```
  `plataforma/api/main.py`
    l1256  class Preferencia(BaseModel):  *** clave: str  ·  valor: object ***   <- CUALQUIER clave y valor
    l1261  @app.put("/api/preferencias")  ->  almacen.guarda_preferencia(usuario["id"], p.clave, p.valor)
    l158   *** @app.get("/api/yo") ***     ->  {"usuario": ..., "preferencias": ... if usuario else {}}

  *** Y PROBADO DE VERDAD: ***
    `PUT /api/preferencias` {"clave": *** "objetivo:2026-10-14" ***, "valor": *** {"kcal": 2000} ***}
      -> *** {"hecho": true} ***
    `GET /api/yo` -> *** {"objetivo:2026-10-14": {"kcal": 2000}} ***
    y en la base: `b13-recorrido-2301 | objetivo:2026-10-14 | {"kcal": 2000}`
  *** -> o sea: la tercera pieza de B08 NO habia que construirla: *** la tabla, el almacen y LA RUTA ya estaban.
  *** -> y NO se inventa el valor: si no hay objetivo, NO SE DEVUELVE UNO -- la grafica tiene DOS series. ***
  ```

- *** Y UNA CORRECCION MAS (la 14a), y es el mismo error de B02: *** *declare «una anomalia en la lectura»
  porque `GET /api/estado` daba `preferencias: null` -- *y **la ruta es `/api/yo`, y `/api/estado` no tiene ese
  campo.** *Y el codigo estaba bien: `if usuario else {}`, *o sea *** `{}` *** y **no `null`.** *
  *** -> y la salvaguarda funciono porque se escribio: *** *«no se declara cual es la causa... concluir "esta
  roto" sin leerla seria el error de B02.» *Y **al leer la linea, el falso positivo se cayo.** *

- *** Y EL OBJETIVO NO NECESITA MIGRACION *** *(ronda 278)*: *** `preferencia` ya lo admite *** *
  ```
  Table "public.preferencia"
    *** usuario_id | uuid | not null ***  ·  *** clave | text | not null ***  ·  *** valor | jsonb | not null ***
    PRIMARY KEY (*** usuario_id, clave ***)  ·  FK a `usuario(id)` *** ON DELETE CASCADE ***
  ```
  *** -> y el encargo pide «OBJETIVO OPCIONAL POR PERSONA Y FECHA», que es justo eso: ***
     *`usuario_id` = la persona · **la fecha cabe en `clave`** (`"objetivo:2026-10-14"`) ·
     `valor` jsonb = **el que ponga la persona** · y **la PK compuesta impide dos objetivos para el mismo dia**
     · y `ON DELETE CASCADE` **limpia al borrar la cuenta.** *
  *** -> y NO se inventa el valor: el encargo prohibe «inventar objetivos de salud», y esta tabla guarda
     EL QUE LA PERSONA ESCRIBA. *** *
  *** -> y se usa desde `core/despensa.py`, `almacen.py` y `main.py`: hay funciones de leer y escribir
     preferencias, y el objetivo es una preferencia mas. ***

- *** Y LA CUARTA PIEZA ES UNA COMPOSICION, NO UNA DECISION *** *(ronda 285)*:
  ```
  *** LOS TRES DATOS YA SE LEEN: ***
    registrado -> `GET /api/diario/rango`            -> `kcal_conocida` (o `null`)
    previsto   -> *** `GET /api/recetas/plan/prevision` *** -> `conocido.kcal` (o `null`) + *** cobertura POR NUTRIENTE ***
    objetivo   -> *** `GET /api/yo` ***                    -> `{"objetivo:<fecha>": {"kcal": N}}`, *y si no hay, LA CLAVE NO ESTA*
  *** Y LAS TRES REGLAS YA ESTAN ESCRITAS Y PROBADAS *** (`logica/chispa.ts`, 114 lineas):
    *** «lo que no se observo no se puede dibujar como si se hubiera observado» ***
    *** «un hueco es un hueco: un `null` se conserva como `null`» ***
    *** «de una serie vacia no se infiere nada: pinta que NO HAY SERIE, no que haya un solo dia» ***
    *(y `l93` ya pide la *** «tabla accesible de los mismos datos» *** que G05 exige)*
  *** Y `serieDeChispa(puntos) -> SerieDeChispa` ES GENERICA *** *-- no sabe de precios ni de calorias:
    recibe puntos y devuelve la serie **con su cobertura `{valor, faltantes}`**.*
  *** -> y las tres cumplen la regla SIN ARREGLARLAS: *** *`kcal_conocida: null`, `conocido.kcal: null`,
     y el objetivo **no existe como clave** -- no un cero en ninguno de los tres.*
  *** -> y si no hay objetivo, LA LEYENDA TIENE DOS SERIES Y LO DICE. *** *
  ```

- *** Y UN INVARIANTE QUE HAY QUE SABER ANTES DE TOCAR ESA COMPOSICION *** *(ronda 288, y se descubrio
  intentandolo y revirtiendolo)*: *** *** `plataforma/web/app/src/logica/` son HOJAS. *** *
  ```
  $ git grep -n "^import .* from '\./" -- "plataforma/web/app/src/logica"
  *** -> NADA: ningun modulo de `logica/` importa a otro de `logica/`. *** *

  *** Y por eso los ensayos los pueden probar asi (`tests/*.test.mjs`, con `node --test`): ***
     `import { aMs, filasDeChispa, *** serieDeChispa *** } from '*** ../src/logica/chispa.ts ***'`
     -- *funciona porque `chispa.ts` **no importa nada**.*

  *** Y EL CONFLICTO, si se rompe (medido, las dos caras): ***
     sin extension -> *** `tsc` VERDE *** y *** `node --test` FALLA ***: `ERR_MODULE_NOT_FOUND`
     con `.ts`      -> *** `node --test` PASA *** y *** `tsc` FALLA ***: `TS5097 ... allowImportingTsExtensions`
  *** -> o sea: `tsc` prohibe la extension, y Node la exige, y el proyecto lo resuelve POR CONSTRUCCION. ***

  *** Y LAS TRES SALIDAS MALAS, que por eso se reverti: ***
     a) activar `allowImportingTsExtensions` -> tocar la config del compilador de TODO el proyecto por un fichero
     b) copiar la logica de `serieDeChispa`   -> y ya esta escrito que no: `Cesta.tsx:139`, «una segunda copia
                                                 que se queda vieja»
     c) dejar `tsc` en rojo                    -> y `tsc` verde es una de las cuatro puertas
  *** -> y queda la (d): la composicion va en un COMPONENTE (`.tsx`), que se prueba con `tsc` y `npm run build`.
     *** Y `logica/` se queda como esta: HOJAS. *** *
  ```

- *** Y EL SITIO DE LA CUARTA PIEZA YA EXISTE: `paginas/Tendencias.tsx` *** *(ronda 290)*:
  ```
  *** SU DOCSTRING YA TIENE LA DOCTRINA DE LA GRAFICA, con sus palabras: ***
    *** «Un dia sin dato no es un dia de cero. Aqui los dias sin energia no llevan barra: llevan la palabra
    "sin dato". Un grafico que dibuja cero donde no hay dato dice que se comio nada, Y ENCIMA HACE PARECER
    QUE LOS DEMAS DIAS ESTAN COMPLETOS.» ***
    *** «Y tampoco se inventa una media... dibujar un cero seria INVENTARSE UN RESULTADO.» ***
    *** «La medida se declara: es lo anotado y lo que se sabe, no "lo que comiste".» ***
  *** Y YA PINTA LA PRIMERA SERIE: *** *`import { useRango } from '../api/diario'`*

  *** -> y por eso la vista de las tres series es AMPLIAR, no un fichero nuevo: ***
     1) el registro  -> *** ya esta (`useRango`) ***
     2) la prevision -> *** `/api/recetas/plan/prevision` ***, que ya existe
     3) el objetivo  -> *** `/api/yo` ***, que ya lo trae (`objetivo:<fecha>`)
     4) `serieDeChispa` TRES VECES -> *** y el import es SIN extension: `from '../logica/chispa'` ***
        *** -> porque un `.tsx` lo resuelve el empaquetador, y `tsc` exige justo eso ***
     5) y la leyenda, con `dibujados` / `total` / `sinFecha` / `dibujable` / `motivoUnidad`
  *** -> y va en CALORIAS, que es donde ya estan el diario y las tendencias; y su fuente de la prevision
     cruza a RECETAS por una ruta que ya existe. *** *
  ```

- *** Y DE ESA COMPOSICION, DOS DE LAS TRES PIEZAS YA ESTAN ESCRITAS *** *(rondas 293-295)*:
  ```
  *** 1) `usePrevision(desde, hasta)` ***  -> *** HECHO (`0a7f602`) ***, en `api/recetas.ts` junto a `usePlan`
     *y con tres tipos que dicen lo que el dato es: *`kcal` puede ser `null`*, *`motivo` dice cual de los
     dos motivos (`sin_catalogo`/`sin_cantidad`)*, *y `cobertura` cuenta **de cuantas lineas sale cada numero***
  *** 2) `useYo()` ***                      -> *** NO HACIA FALTA: `api/cuenta.ts:23` YA consulta `['yo']` *** *
     *con `yo` (de `./cesta`), para calcular la clave de cuenta -- *asi que el objetivo ya esta en la cache*
     *y su `l8-10` explica por que: «son miAS y son CUATRO... **defensa en profundidad**»*
  *** 3) `componentes/LeyendaDeSeries.tsx` *** -> *** HECHO (`5b14928`) *** *
     *-- la leyenda **y LA TABLA ACCESIBLE que `chispa.ts:93` pide**: *dice **cuantas series hay**
     (`sin_objetivo` cuando no lo hay), *lleva **`dibujados` Y `total`** en cada fila, *y **no escribe «0
     puntos» sino «sin serie»** -- *que es lo que `dibujable: false` significa.*
  *** -> y queda UNA COSA: unirlo en `Tendencias.tsx` *** *-- *las tres `serieDeChispa` sobre los tres datos,
     y `<LeyendaDeSeries/>` debajo de la grafica.*
  ```

- *** Y LA COMPOSICION ESTA HECHA *** *(rondas 297-299, y son los commits `2382f53`, `4f4520d`, `a884935`)*:
  ```
  *** `logica/puntosDeLasTres.ts` ***  + *** 7 ensayos *** *-- los tres datos a puntos, con LA REGLA:
     un dia con varias comidas **se suma SOLO si todas traen energia**, y si a una le falta el dia va a
     *** `null` y NO a la suma parcial *** -- *porque una suma parcial no es «lo previsto»: es lo previsto
     menos algo.* *Y respeta el invariante: **solo importa el TIPO**, asi que `logica/` sigue siendo hojas.*
  *** `componentes/LeyendaDeSeries.tsx` *** *-- la leyenda y *** la tabla accesible que `chispa.ts:93` pide ***:
     dice **cuantas series hay** (`sin_objetivo`), lleva **`dibujados` Y `total`** en cada fila, y **no escribe
     «0 puntos» sino «sin serie».**
  *** `componentes/GraficaDeLasTres.tsx` *** *-- la composicion: tabla dia a dia con «sin dato» **con la
     palabra**, el aviso de los ingredientes sin catalogo, y la nota cuando son dos series.*
  *** `api/recetas.ts` *** *-- `usePrevision(desde, hasta)`, con tres tipos que dicen lo que el dato es.*
  *** `paginas/Tendencias.tsx` *** *-- y la costura, con el rango que ya tenia (`haceDias(dias-1)`, `hoy()`).*

  *** Y LAS PUERTAS, tras todo esto: *** *** 2033 pruebas de Python (0 fallan) · `ruff` limpio · `tsc` limpio ·
     81 de frontend (0 fallan) · y el build en 15,64 s. *** *
  *** -> y `B16` ya no declara limitado el eje de la PREVISION: *** *quedan CUATRO limitaciones, y son reales:
     el alcance de Lidl, la nutricion en el aprendizaje, la restauracion sin ejercer, y la rotacion de logs.*
  ```

- *** Y LA ULTIMA COMPROBACION, SOBRE LA SEMANA ENTERA *** *(ronda 305, y es la evidencia mas fuerte)*:
  ```
  $ GET /api/recetas/plan/prevision?desde=2026-10-12&hasta=2026-10-18
  *** comidas: 7 ***  *-- *cinco recetas distintas, del 12 al 17, **todas con `version: 1` y `comensales: 2`*
    2026-10-12  Ensalada  ->  tomate          motivo=*** sin_catalogo ***  kcal=*** None ***
    2026-10-13  Sopa      ->  tomate          motivo=sin_catalogo   kcal=None
    2026-10-14  Ensalada  ->  tomate          motivo=sin_catalogo   kcal=None
    2026-10-14  Sopa      ->  tomate          motivo=sin_catalogo   kcal=None
    2026-10-15  Guiso     ->  200 g tomate    motivo=sin_catalogo   kcal=None
    2026-10-16  Pure      ->  150 g tomate    motivo=sin_catalogo   kcal=None
    2026-10-17  Arroz     ->  *** 3 ud huevos ***  motivo=sin_catalogo   kcal=None

  *** sin_dato     -> ['tomate','tomate','tomate','tomate','200 g tomate','150 g tomate','3 ud huevos'] ***
  *** sin_cantidad -> [] *** *
  ```
  *** -> y confirma las cuatro cosas: *** *el PLAN escalado (`v1`, 2 comensales) · *** `kcal: None` en las
     siete, y NO CERO *** · *** y `sin_dato` con LOS SIETE NOMBRES ENTEROS ***, *incluidos **`200 g tomate`**,
     **`150 g tomate`** y *** `3 ud huevos` *** -- *o sea: *** el ingrediente se conserva CON SU CANTIDAD Y SU
     UNIDAD ***, *que es la clausula «ingrediente sin catalogo conservado».*
  *** -> y `3 ud huevos` es el mejor de los siete: *** *lleva la unidad `ud` -- **la del fallo del dueno** -- y
     **se conserva tal cual**; *y **no se convierte a gramos**, porque `_gramos_de` **solo convierte `g` y `kg`.** *
  *** -> y `sin_cantidad` sale VACIO, y se dice por que: *** *`sin_catalogo` **se comprueba primero** -- *
     *sin producto, los gramos no importan* -- *y **con estas recetas ninguna tiene producto**, asi que **ese
     camino no esta ejercido por estos datos**, y **su ensayo lo cubre.** *

- **Pendiente o límite exacto**: *** y lo que queda es UNA COMPOSICION: *** *tres `serieDeChispa` sobre los tres
  datos, la leyenda con la cobertura de cada serie, y **la tabla accesible**. *Y **no falta una decision ni un
  dato.** *
  *** 1) el ALMACEN del objetivo *** *-- *escribir y leer `preferencia` con la clave `"objetivo:<fecha>"`*
  *** 2) y LAS GRAFICAS de registrado versus previsto versus objetivo *** *-- *y `logica/chispa.ts` **ya tiene
  sus tres reglas**: *«lo que no se observo **no se puede dibujar como si se hubiera observado**»*
  *** y 3) el limite del paso 3, dicho por el codigo: *** *`cesta.py:184` -- *la columna que trae el
  `producto_id` la escribe `emparejar.py`, *y **«ese fichero no la tiene todavia»**; *y **el dia que la
  escriba, «llega sola».** *
- *** Y LOS SEIS PASOS DE LA PREVISION EXISTEN *** *(medido en las rondas 262-268, y cada uno con su linea)*:
  ```
  1) EL PLAN              `GET /api/recetas/plan` (`recetas.py:107`) -> `fecha`, `receta_id`, `version`, `comensales`
  2) LA RECETA ESCALADA   *** `core/recetas.py:134 escala(...)` *** -- *y «las dos cifras»: `raciones` y
                          `raciones_receta`, y `escalada`*
  3) DE LA LINEA AL PRODUCTO  *** `plataforma/api/cesta.py:98` ***: «que producto concreto resuelve una linea
                          *** en una cadena dada ***»; *y `:200`, «el producto mas barato que la resuelve»*
     *** y su limite, DICHO POR EL CODIGO: *** `cesta.py:184` -- «la columna se pide *** si esta ***, y el dia
     que el emparejador la escriba, *** LLEGA SOLA *** -- *sin tocar nada»* **y `emparejar.py` «no la tiene todavia»**
  4) DEL PRODUCTO A NUTRIENTES  `catalogo.producto(id)` + *** `core/diario.py:235 de_ficha(producto, gramos)` ***
  5) LA CANTIDAD          de la linea (`cantidad`, `unidad`)
  6) LA SUMA CON COBERTURA *** `core/diario.py:287` (`_cobertura`, POR NUTRIENTE) y `:307` (`suma -> None`) ***
     *** y el subtotal se llama `conocido` Y NO `total`, A PROPOSITO (`diario.py:296`) ***
  *** -> y `de_ficha`, `suma`, `_cobertura`, `conocido` y `completo` son EXACTAMENTE lo que la prevision
     necesita -- *y por eso la prevision y el consumo suman IGUAL, que es lo que las hace comparables.*
  ```
- *** Y LA ESPECIFICACION ESTA ESCRITA *** (`B08-la-especificacion-de-la-vista-de-previstos.md`):
  *`prevision(con, propietario, desde, hasta, *, cadena=None)`*, *con **los seis pasos citados**, *y **la salida
  obligada**: *** `conocido` *** (no `total`), *** `cobertura` POR NUTRIENTE ***, *y *** `sin_dato` con su nombre.** *
  *** Y el ensayo, con los numeros del plan: `R1=270`, `media=135`, y «ausencia de energia con proteina conocida»
  -- que es el caso que OBLIGA a que la cobertura sea por nutriente, y que `diario.py:323-325` ya resuelve. *** *
  *** -> y NO IMPLEMENTADA, y por eso B08 SIGUE ABIERTA. *** *
- *** Y LA VISTA YA ESTA ESCRITA Y CONTESTA *** *(ronda 274, commit `83753ba`)*:
  ```
  *** `GET /api/recetas/plan/prevision?desde=&hasta=` -> 200 ***
    {"comidas": [{"fecha": "2026-10-12", "nombre": "Ensalada de ensayo B13", "version": 1, "comensales": 2,
      "lineas": [{"texto": "tomate", "producto_id": null, "nutrientes": null,
                  *** "motivo": "sin_catalogo" ***}],
      *** "conocido" ***: {"entradas": 0, *** "kcal": null ***, ...},   <- *** null, y NO CERO ***
      *** "cobertura" ***: {"kcal": {"con_dato": 0, "total": 0, "completa": false}, ...},  <- los CUATRO
      *** "completo": false ***}],
     "sin_dato": [...], "sin_cantidad": [...]}
  *** -> y sale de las piezas que ya existian: *** *`recetas.plan` -> `recetas.leer(raciones=comensales)` ->
     `catalogo.producto(id)` -> `diario.de_ficha(ficha, gramos)` -> `diario.resumen(conocidos)`*
  *** -> y `_GRAMOS_POR_UNIDAD = {"g": 1.0, "kg": 1000.0}` y NADA MAS: *** *`ml` necesitaria la densidad y
     `ud` el peso de una unidad, y **el encargo prohibe inventarlos** -- y los dos van a `sin_cantidad`.*
  *** -> y `de_ficha` ya resolvia el caso dificil del criterio («ausencia de energia con proteina conocida»):
     «se calcula NUTRIENTE A NUTRIENTE, NO EN BLOQUE... RELLENAR CON CEROS SERIA AFIRMAR QUE NO LLEVA
     PROTEINA, y eso no lo sabemos.» ***
  ```

- *** Y UN AVISO DE OPERACION, medido: *** *** el codigo de la API va DENTRO de la imagen ***, *asi que
  *** `docker compose restart api` NO coge los cambios *** *-- *hay que *** `docker compose up -d --build api` ***. *
  *Y **se descubrio porque la primera llamada fallo**, *y **el fallo no era del codigo.** *

- **Siguiente comando o acción**: *** el ensayo de `prevision` con los numeros del plan *** *(`R1=270`,
  `media=135`, «ausencia de energia con proteina conocida»)* *** y despues el objetivo opcional y las graficas
  de registrado versus previsto versus objetivo *** -- *y `logica/chispa.ts` **ya tiene las tres reglas.** *
  pasos de arriba, con la cadena de `lista_linea`, y con el ensayo de los numeros del plan. Y **`ABSTIENE` cuando
  no haya producto: la linea va a `sin_dato` con su nombre, nunca a un numero inventado.** *

- *** Y LA PREGUNTA DEL PROPIETARIO, CONTESTADA CON DATO (rondas 313-316) ***:
  > *** «que dependa de LA REGION que elija el usuario... *** *** verifica si esto le pasa a mas
  > supermercados o solo a lidl *** *** para mejorar la experiencia del usuario» ***
  ```
  *** 1) ES SOLO LIDL, y esta medido: ***
     `precio_diario.parquet` tiene columna *** `region` ***, y: *alcampo, carrefour, dia, mercadona y aldi
     la tienen *** `None` *** (su catalogo es nacional); *y *** lidl es la unica con `'28'`, en 77 filas ***.
     *** Y `regiones distintas en todo el fichero = 1`. *** *
  *** 2) Y LA RAZON ESTA ESCRITA EN SU COLECTOR: *** *«su pagina publica de *** ofertas semanales ***
     publica un numero acotado de fichas *** CON PRECIOS POR REGION ***». *
     *** -> y NO ES EL CATALOGO DE LIDL: *** *son *** «ofertas conocidas» ***, *y el nombre lo dice el
     fichero de cobertura que escribe.*
  *** 3) Y DE DONDE SALE LA REGION: *** *** `config.CODIGO_POSTAL` *** *-- *que es «tu zona», y que
     *** ya fija el almacen de Mercadona y el ambito de Aldi *** -- *y en `lidl.py:59-68` esta escrito: *
     *** «la region sale de la zona del usuario, que YA existe en `config`» ***, *y *
     *** «un CP no es un id de `regionsV2`, y el plan prohibe suponerlo» ***, *asi que *
     *** «se acredita por el nombre que la propia fuente publica (`region_del_cp`), y SI NO CASA, NO HAY
     REGION Y NO SE PUBLICA -- no se elige la mas parecida». *** *
  *** 4) Y QUE ES `'28'`: *** *** el `REGION_POR_DEFECTO` observado ***, *y su comentario dice lo que es:
     *** «la unica observada; NO ES LA ZONA DEL HOGAR DE NADIE» ***, *y *** «elegirla habria publicado
     precios de una zona que no es la de quien los lee». *** *
  *** -> o sea: **la funcion que el propietario pidio YA ESTA ESCRITA**, *y con la regla que el encargo
     exige: **la region depende del usuario, y si no casa, no se publica.** *
  *** y el mecanismo, con su nombre: *** *`regionsV2[region].regionPriceId`, y «se resuelve ANTES de mirar
     el precio».*
  *** Y UNA CORRECCION AL PROPIO COLECTOR, en el mismo hallazgo: *** *`lidl.py:22` decia *** «no esta en la
     tarea de las 06:00, a proposito... se ejecuta a mano» ***, *y la cadena medida lo desmiente: *
     `registrar-tarea.ps1` (06:00) -> `ejecutar.bat:57` -> `run.py:234` (`fuentes = args.solo or ORDEN`) ->
     *** `ORDEN` incluye `lidl` ***. *Asi que *** SI corre a las 06:00 ***, *y **lo que lo protege ya no es la
     ausencia, sino el PRESUPUESTO** -- *y **la frase vieja se corrigio, en el mismo commit** (`090bb54`).*
  ```

### B13 · 13/10/2026 · **los cinco recorridos, y la restriccion del dueno medida por los DOS puentes**

- **Cambio o hallazgo nuevo**: *** los cinco recorridos se hicieron con navegador OCULTO, y la restriccion del dueno
  quedo reproducida y medida. ***

  *** LOS CINCO RECORRIDOS *** *(Chromium 155 oculto, `capture_browser_scenario`, y `click` en vez de `goto`)*:
  ```
  1 · el lanzador        *** HECHO ***  *200; las tres aplicaciones: /compra /recetas /calorias; y la CSP
                              (`content-security-policy` en la respuesta) con el HTML explicando por que nada va en linea*
  2 · `/compra`           *** HECHO ***  *el menu con las CUATRO secciones, el buscador con voz, el escaner,
                              los filtros de cinco ejes, y tres ejemplos pulsables*
  3 · `/recetas` sin sesion *** HECHO ***  *y dice «Hay que entrar primero» -- que es **el 401 pintado**
                              (`sesion.py:22`: `raise HTTPException(401, "Hay que entrar primero.")`)*
  4 · *** el alta y la sesion *** *** HECHO ***  *`POST /api/registrarse` (201) crea Y ENTRA: la cuenta
                              `b13-recorrido-2301` «Ensayo B13», verificada en la base*
  5 · *** la restriccion del dueno *** *** HECHO ***  *ver abajo*
  ```

  *** Y DOS COSAS DE METODO, que costaron rondas y hay que dejar escritas ***:
  ```
  a) *** `goto` NO SIRVE PARA CAMBIAR DE SECCION: *** *una navegacion completa **pierde la sesion**, porque el
     escenario **declara `storage` vacio y el proveedor lo repone.** *-> *** hay que usar `click` en el enlace del
     menu*** (la suite es una SPA). *** Y NO es un fallo de la aplicacion: la cookie esta bien
     (`main.py:93-94`: `httponly` · `samesite="lax"` · `max_age` · `path="/"`). ***
  b) *** pedir POCAS acciones: *** *con 12 acciones la llamada **expira**; con 5-8 va bien. *Y con 8 puede dar
     `cleanup_incomplete` **y la observacion sale entera** -- *se declara cada vez.*
  ```

  *** LA RESTRICCION DEL DUENO — «300 g terminan como una unidad y una nota de 100 g, descartando la segunda
  receta como repetida» — MEDIDA POR LOS DOS PUENTES ***:
  ```
  SE MONTÓ EL ESCENARIO (cuenta de ensayo `b13-recorrido-2301`):
    receta 1 «Ensalada de ensayo B13» · 2 raciones · v1 · ingrediente *** `300 g tomate` ***
    receta 2 «Sopa de ensayo B13»     · 2 raciones · v1 · ingrediente *** `100 g tomate` ***
    y las dos planificadas el 2026-10-14 con *** `comensales: 2` *** y *** `version: 1` ***

  *** PUENTE DE RECETA *** · `GET /api/recetas/{id}/a-la-lista` · *** VISTA PREVIA, NO ESCRIBE ***:
    *** `"cantidad": 300.0, "unidad": "g"` ***   -> *** NO es «1 unidad» ***
    *** `"nota": ""` ***                            -> *** y NO hay nota ***
    *** `"clave": "tomate|kg"` EN LAS DOS ***        -> *** comparten identidad: SE CONSOLIDAN a 400 g ***
    *** `"sin_cantidad": []` · `"sin_consolidar": []` ***

  *** PUENTE DEL PLAN *** · `GET /api/listas/{id}/desde-el-plan?desde=&hasta=` · *** y pide el rango (422 sin el) ***:
    *** `"sin_catalogo": ["tomate"]` ***           -> *** UNA entrada para las DOS recetas: se consolidaron ***
    *** `"sin_cantidad": []` · `"sin_consolidar": []` · `"entrarian": []` · `"total": 0` ***

  *** Y LOS DOS PUENTES DICEN LO MISMO: *** *** NO hay «1 unidad», NO hay «nota de 100 g»,
  y NO se descarta la segunda receta. ***
  *** Y «sin_catalogo: [tomate]» es la clausula del encargo «INGREDIENTE SIN CATALOGO CONSERVADO»:
  el tomate SE CONSERVA, y NO entra porque `recetas.py:147` dice «sin `producto_id` NO SE PONE PRECIO... LO QUE NO
  SE SABE SIGUE SIN SABERSE». Y son CINCO listas y no un `error`. ***
  *** Y NADA SE ESCRIBIO: las dos llamadas son `GET`, y `GET /api/listas` sigue con `"lineas": 0`. ***
  ```

  *** Y UNA DIFERENCIA MEDIDA, PARA B14 ***: *el contenedor monta el `data/` del host en *** `/datos:ro` ***
  (`docker-compose.yml:59`: `${CESTA_DATOS:-../data}:/datos:ro`), *y *** `/app/data` NO tiene montaje ni volumen
  nombrado*** -- *y por eso hay **dos `recetas.sqlite`**: **42 recetas en el host**, y **2 (las de ensayo) dentro del
  contenedor**. *** Y la copia documentada (`robocopy data\raw`) no cubre ninguno de los dos. ***

- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2025 pasan, 0 fallan, 0 se saltan**. *Y **nada de
  codigo**: lo unico escrito son **dos recetas, un plan y una lista de ensayo**, en la cuenta de ensayo.*
- **Evidencia**: `docs/investigaciones/B13-*.md` (**19 documentos**) · los `evidence_id` de las capturas ·
  `plataforma/api/sesion.py:22` · `main.py:93-94`, `l576`, `l1458`, `l1624` · `recetas.py:107/118/199/235` ·
  `docker-compose.yml:59`
- **Y LA ACEPTACION, EJECUTADA**: *** `POST /api/listas/{id}/desde-el-plan?desde=&hasta=` -> `201` ***
  ```
  *** {"anadidos": 0, "ya_estaban": [], "sin_catalogo": ["tomate"]} ***
  y DOS LECTURAS de la lista, IDENTICAS -> *** PERSISTE ***  ("lineas": [], "sin_precio": 0)

  *** y NO se inventa un producto: *** *el tomate **no esta en el catalogo**, *y por eso *
  *** `anadidos: 0` *** -- *y **se dice cual falta.** *Y **«sin_catalogo» tiene UNA entrada para las DOS recetas**:
  *** la consolidacion, medida tambien por este puente. *** *
  ```
  *** Y LA ACEPTACION, COMPLETA *** -- *cinco recetas semanales con cantidades, planificadas del 12 al 17:*
  ```
  2026-10-12  Ensalada de ensayo B13  2 comensales v1   ->  *** 300 g tomate ***
  2026-10-13  Sopa de ensayo B13      2 comensales v1   ->  *** 100 g tomate ***
  2026-10-14  Ensalada y Sopa (las dos, y es legitimo: el mismo dia)
  2026-10-15  Guiso de ensayo B13     2 comensales v1   ->  *** 200 g tomate ***
  2026-10-16  Pure de ensayo B13      2 comensales v1   ->  *** 150 g tomate ***
  2026-10-17  Arroz de ensayo B13     2 comensales v1   ->  *** 3 ud huevos ***
  *** -> 7 entradas, CINCO recetas distintas, y LAS DOS UNIDADES en los datos: `g` y `ud` ***
  ```
  *** Y LA FORMA DEL INGREDIENTE, medida (`recetas.py:43`): *** *`IngredienteIn` tiene *** `texto` OBLIGATORIO y
  `cantidad`/`unidad` OPCIONALES *** -- *o sea: **la web manda SOLO texto** (una linea por ingrediente) **y el PARSER
  decide**; *y **ahi vivia la restriccion del dueno**, *y **acierta**: `300 g tomate` -> `300.0 g`.* *
  *** Y EL catalogo del contenedor esta vacio, y NO se rellena para que la prueba salga bonita: la lista queda
  vacia con su motivo (`sin_catalogo`), que es lo que el encargo pide. *** *
  *** Y HAY UN TERCER PUENTE, que el encargo NO nombra y cierra el ciclo: ***
  ```
  *** `/api/listas/{id}/desde-la-compra` *** (`main.py:1679` GET, `:1719` POST) -- *** COMPRA -> DIARIO ***
    su docstring, literal: *** «No escribe nada: el diario rechaza el tipo `compra` A PROPOSITO --
    COMPRAR NO ES COMER --, asi que esto PROPONE y LA PERSONA CONFIRMA. *** Y dice la cobertura, que es lo que
    hace que esto no mienta: las lineas cuyo producto NO declara nutricion se devuelven aparte, con su nombre.
    *** ANOTAR LAS QUE SE PUEDE Y CALLAR LAS DEMAS CONVERTIRIA UN DATO QUE FALTA EN UNA COMIDA QUE PARECE
    COMPLETA. ***»
    devuelve `anotarian` · *** `sin_dato` *** · *** `cobertura: {con_dato, total}` ***
  *** -> y esa ultima frase es LA DOCTRINA ENTERA, y contesta la clausula del encargo palabra por palabra. ***
  *** -> y NO se ha ejecutado: necesita una compra cerrada con lineas, y la lista de ensayo tiene 0. ***
  ```
  *** Y LOS TRES PUENTES SON EL CICLO: *** *receta->lista (texto) · plan->lista (catalogo) · compra->diario
  (nutricion) -- *y **cada uno dice lo que no sabe**: `sin_cantidad` · `sin_catalogo` · `sin_consolidar` ·
  `sin_dato` · `cobertura`.** *
  ```
- **Pendiente o límite exacto**: *** y YA SE EJECUTO si: `POST` con `201`, y la lista PERSISTE. ***
  *Lo unico que queda es **la decision de B14**: si las recetas y el diario deben vivir en el host (y copiarse) o
  dentro del contenedor -- porque `/app/data` no tiene montaje ni volumen nombrado.*
- **Siguiente comando o acción**: **el POST `desde-el-plan`**, *si el propietario quiere ver la lista escrita; y
  **la decision de B14** sobre donde deben vivir los dos `.sqlite` privados.*

### B16 · 14/10/2026 · **y once rondas mas, midiendo lo que faltaba** · commits `f0eb0db` … `bafc93f`

- **Cambio o hallazgo nuevo**: *cerrado el plan, se siguio midiendo **lo que el dictamen declaraba sin numero**, y
  **cada ronda encontro algo**: *
  ```
  *** 309 ***  la COLA de fichas        -> *`fichas`, *** 79.915 filas ***: 72.319 `pendiente` (90,5 %),
               7.593 `correcto`, 2 `no_publicado`, 1 `error_temporal`; *** y nada atascado *** -- *sin
               `EN_CURSO` colgadas ni `BLOQUEADO`* -- *y por fuente: alcampo 43.603, carrefour 17.280, *
               *** lidl 5.026 *** *
  *** 310 ***  la COBERTURA nutricional -> *** 51.725 productos, y 3.942 con nutricion (7,6 %) ***, *y la
               declara *** UNA SOLA CADENA: `dia` (68,3 %) ***; *alergenos: dia 1.103 y mercadona 2.796; *
               *EAN: dia completo y carrefour 15.095/16.149; *y *** lidl: 0 en los tres *** *
               *** -> y el catalogo es PARQUET con DUCKDB (`catalogo.py:70`), con 63 columnas *** *
  *** 311 ***  las PROMOCIONES          -> *** 8.884 observadas ***, *y el fichero de 0 MB era un *** RESUMEN
               por cadena ***: *medianas *** 5 a 8 dias ***, p90 *** 10 a 15 ***, *y **alcampo el que mas**
               (6.397)*
  *** 312 ***  la SALIDA del oraculo    -> *** 22.873 enlaces ***: `equivalente` 14.528 (63,5 %),
               `identico` 6.617 (28,9 %), `ean` 1.728 (7,6 %); *y **cada enlace lleva `parecido`***
  *** 313-316 ***  *** LA PREGUNTA DEL PROPIETARIO *** -> *** ES SOLO LIDL ***, y **la funcion ya estaba
               escrita** (ver la entrada de B02)*
  *** 318 ***  *** EL WAF ***             -> *** `core/waf.py`: SUPERARLO con un navegador NO es ELUDIRLO ***,
               *y **su primera clausula es literalmente el encargo**: *«se valida por **resultado**, no por el
               nombre de la cookie... una pagina de categoria *** de verdad *** tiene que llegar *** con
               datos» ***. *Y **los siete mecanismos del encargo, localizados**: validacion, checkpoints,
               backoff, limites, observabilidad, recuperacion, *y «no confundir desafio con catalogo vacio»*
  *** 319 ***  *** CASA FRENTE A PUBLICO *** -> *** re-verificado: `cesta-api-1  8000/tcp` SIN el prefijo
               `127.0.0.1:` *** *=> no publicado*, *y **`:8000` no responde desde el host**; *los cuatro
               puertos de loopback siguen (5432, 5434, 8080); *y *** facylf-postgres sigue en 5433 SIN TOCAR *** *
  ```
- **Pruebas ejecutadas**: `ruff` limpio · `pytest -q` **2033 pasan** · y **65 ensayos de `lidl`** verdes tras
  **corregir el comentario viejo de `lidl.py`**.
- **Evidencia**: los once documentos de esta tanda · `docker ps` · `duckdb` sobre `data/gold/v20261013-155356/`
- **Pendiente o límite exacto**: *** y sigue habiendo solo dos cosas, y ninguna es trabajo: *** *la pasada de
  las *** 06:00 *** (que **ya tiene mecanismo medido**: `registrar-tarea.ps1` -> `ejecutar.bat:57` ->
  `run.py:234` -> `ORDEN` con Lidl), *y *** la restauracion ***, *que **el encargo prohibe ejercer.** *

### B04 · 14/10/2026 · **el complemento del 14/10, entero** · commits `6667991` … `59b837c`

> *** Esta entrada **NO sustituye** a la de B04 del 13/10 (que esta al final): *es **su continuacion**.*
> *El 13 se cerro el paquete; el 14 el propietario lo reviso, **corrigio cuatro puntos**, y aqui esta
> lo que se hizo con ellos.* *Se dejan las dos porque **la primera dice como se cerro** y esta **que
> estaba mal en ese cierre** -- *y eso es parte del registro, no un borrador que se tira.* *

- **Cambio o hallazgo nuevo**: *el propietario revisó el cierre y **corrigió cuatro puntos**; los seis del
  complemento están hechos, **cada uno con su regresión probada** (revertida para comprobar que falla): *
  ```
  *** (1) LOS ENVASES ***  *«se calculan dos y se guarda uno»* *** -> HECHO *** *
     *`main.py`: `uno.envases or 1` · `recetas.py`: `ln.envases or 1` · y con tamaño desconocido
     **la nota lo dice** en los DOS puentes* · *** y FALLAN 6 sin el arreglo *** *
     *-- *y el motivo del `1` estaba escrito y era medio cierto: *«poner 400 diria 400 envases»* —
     *cierto; *** «se anade una unidad», no *** *
  *** (2) EL INGREDIENTE SIN CATALOGO ***  *** -> HECHO *** *
     *el `continue` que lo tiraba decia «la base lo rechazaba con un 500», y **la migracion
     `014_la_linea_sin_destino` quitó esa restriccion**; ahora entra como **«pendiente de identificar»*** *
     *-- *y **el ensayo que decia «NO ENTRA» quedó INVERTIDO*** *-- *fijaba el defecto como diseño*
     *-- *y **la previa contaba 0 mientras el POST apuntaba 1**: *los dos números dicen 1*
  *** (2b) EL ORDEN DEL TUPLE ***  *** -> HECHO *** *-- *al seguir la pista: `(producto_id, None)` donde
     tocaba `(None, producto_id)`, *así que **la comprobacion de «ya esta» no encontraba nunca un
     producto**, *y el mismo se podia añadir DOS VECES* — *justo lo que su comentario promete que no pasa*
  *** (3) EL dedupe POR NOMBRE ***  *** -> HECHO *** *-- *`_del_plan` devolvia `{nombre_visto.lower()}`;
     *ahora la identidad es **el DESTINO**, *con el nombre de respaldo **solo si alguno es una pendiente**
     *-- *y entre dos con destino NO se mira el nombre: **dos marcas distintas son dos compras distintas***
  *** (4) LA IDENTIDAD DE LA RECETA ***  *** -> HECHO, y era PEOR *** *-- *`int(...) if isdigit() else None`
     *no degradaba «el articulo elegido» **a veces**: *no lo guardaba **NUNCA**, porque los ids del
     catalogo son **`fuente:id`** y ninguno es `isdigit()` — *y la columna es `text`*
  *** (5) LA TELEMETRIA DE LIDL ***  *** -> HECHO *** *-- *eran **tres** caminos mudos, no uno: la region sin
     acreditar, la peticion y el parseo; *las tres registran ya (0 filas, 1 error, `completa=False`)*
     *-- *la causa va a stdout → `data/ejecuciones.log`; *el CSV dice que HUBO INTENTO*
  *** (6) Y ADEMAS ***  *la clase de las **citas por linea**, eliminada (las tres que habia **estaban las tres
     mal**), *y la **auditoria** del guion de restaurar*
  *** Y EL RESPALDO, que no existia ***  *** -> ver la entrada de B14 *** *
  ```
- **Pruebas ejecutadas**: `ruff` limpio · *y **cada regresión revertida** para comprobar que falla sin el
  arreglo* · `pytest -q -k "lidl or plan or puente or lista or previa or favorito or duplica or receta"`
  → **243 pasan**
- **Evidencia**: los documentos de `docs/investigaciones` de estas rondas · y **dos correcciones al
  propio proyecto**: el comentario de `lidl.py` que decia lo contrario de lo que hace, y las citas por linea
- **Pendiente o límite exacto**: *** dos cosas, y las dos necesitan al propietario ***: *
  *-- *(a) **la prueba de restauracion**: *las guardas están (19 ensayos) y **su hueco tapado** — ahora
  exige `Up` antes de esperar —, *pero el recorrido **necesita quitar el contenedor atascado**
  (`cesta-restauro-82294a5bd651`, en `Created`, 4,1 kB) *y `docker rm -f` **se bloquea** en el*
  *-- *(b) y **la decision**: *¿dos operaciones legitimas del mismo producto **SUMAN** o **SUSTITUYEN**?*
  *-- *y **los permisos/snapshots**, la tercera pata que la prueba pide*

### B00 · 13/10/2026 · commits `9a3a4bb`, `7b33a3f`, `c749405`, `fda0f5c`, `491ac0c`

- **Cambio o hallazgo nuevo**: Docker Desktop estaba parado y su servicio también. Se arrancó el
  ejecutable y el motor respondió. **`cesta-prueba-db` no existía**: `docs/OPERACION.md:13` la crea con
  `--rm`, así que el reinicio de Docker se la llevó. Se recreó y se recrearon `prueba-navegador` y
  `recibo-de-prueba` con `almacen.crea_usuario`. **Y se añadió la guarda que faltaba**:
  `comprueba_que_es_una_prueba(dsn)` rechaza el 5432 (la base de casa) y el 5433 (facylf), y también un
  DSN **sin puerto**, porque «no se sabe» no es «es de pruebas». **Y —lo que la hace servir de algo— está
  puesta donde el daño ocurre**: `prueba_e2e.py` la llama sobre su `CESTA_POSTGRES` **antes de importar
  la plataforma** (su `setdefault` respetaba un DSN heredado), y `prueba_copia.py` la llama sobre el que
  le pasa al hijo. **Dos comprobaciones: quien lanza y quien corre.**
- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2019 pasan, 0 fallan, 0 se saltan**
  (2012 + los 7 de la guarda) · `npm test` 74 pasan · `npx tsc --noEmit` 0. **Los siete de la guarda no
  se conectan a nada**: se corren con Docker parado.
- **Evidencia**: `/api/estado` versión `20261013-135533`, `coherente true`, 6 huellas ·
  `docs/investigaciones/B00-verificacion-inicial.md` §6 · `tests/test_b00_guarda_del_dsn.py` ·
  comprobado con la variable puesta a mano: `CESTA_POSTGRES='…:5432/cesta'` → `ValueError` y salida 1.
- **Pendiente o límite exacto**: **ninguno del criterio de B00.**
- **Siguiente comando**: `uv run pytest tests/test_b00_guarda_del_dsn.py -q`

### B03 · 13/10/2026 · commits `3cc4013` … `bed5639`

- **Cambio o hallazgo nuevo**: Lidl **ya estaba** en `ORDEN` y en `CADENAS_QUE_SE_CAPTURAN`; no corría
  porque `run.py` llamaba `main()` sin argumentos y su CLI los exige (`required=True`). Se añadió
  `ARGUMENTOS` en `run.py` con `["--web","--escribir"]`. La **región** sale de `config.CODIGO_POSTAL`
  acreditada por el nombre que publica la fuente (55 regiones), nunca de un CP supuesto. El **veto**
  estaba en una línea de `en_tienda` (`CADENAS` → `CADENAS_QUE_SE_CAPTURAN`) y el motivo,
  `por_que_no_se_compara`, **no lo llamaba producción**. La **región** viaja ahora bronze → silver →
  gold → vista → API (77 de 77 en Lidl), con el histórico rehecho.
- **Pruebas ejecutadas**: `ruff check .` limpio · `pytest -q` **2012 pasan, 0 fallan** · comprobado por
  HTTP: `/api/estado` con 6 cadenas y la cobertura de Lidl, y `en_tienda` con `lidl` da **401**, no 422.
- **Evidencia**: `data/cobertura/lidl-2026-10-13.json` (`ofertas_semanales_parcial`, `con_precio 77` de
  `79`, `region 28`) · `docs/investigaciones/B03-*.md` (catorce documentos).
- **Pendiente o límite exacto**: **la zona en la comparación de precios.** *Y ahora se sabe **dónde empieza**,
  que no es donde parecía*: `donde_comprar` **no lee `diario`, lee `grupos`** — *el modelo de emparejamiento,
  `data/gold/matching/`* —, y `grupos` **no tiene `region`**. Medido: al añadirla al `SELECT` salta
  `_duckdb.BinderException: Referenced column "region" not found in FROM clause`, y rompe **seis pruebas de
  tres ficheros**. *Se probó y se **revirtió**; el árbol volvió a `2019 pasan, 0 fallan`.*
- **Siguiente comando o acción**: **empezar por `matching`, no por `donde_comprar`.** *Y la decisión de fondo
  es la misma que la del grano de `diario`, una capa más arriba*: **si un producto puede tener precios de dos
  zonas emparejados en el mismo grupo, el grupo deja de ser «un producto» y pasa a ser «un producto en una
  zona»**. *La forma de añadir la columna cuando toque sí está comprobada: **al final del `SELECT`**, que no
  mueve ningún índice.* Ver `docs/investigaciones/B03-la-comparacion-lee-grupos-no-diario.md`.

  **Y el mapa, ya corregido — con una pieza que NO se toca:**

  ```
  NO SE TOCA:  core/grupos_ids.clave_de(fuente, id_fuente)
               -> es el PRODUCTO, y el producto no tiene zona.
               -> Su docstring: «la identidad estable que YA USA MEDIO PROYECTO».
               -> Y es literal: es el `producto_id`, y `estabiliza` hace JOIN sobre ella.
               -> Tocarla rompe el emparejamiento ENTERO, no la comparacion de zonas.

  SE TOCA:     la clave del GRUPO, en `estabiliza` y en el calculo del grupo.
               -> La zona es una propiedad del PRECIO, no del producto.

  Y LA OCTAVA MEDIDA, HECHA — con una corrección importante sobre lo que se creyó al medirla:

  ```
  SE TOCA (1):  projects/cesta/emparejar.py :: grupos_de(...)
                -> AQUI SE FORMA EL GRUPO. Dos zonas, dos `grupo`.

  SE TOCA (2):  core/grupos_ids.tabla_de(filas, grupo_id)
                -> guarda (clave, grupo_id) para manana, y `clave` NO lleva zona.
                -> Con dos zonas habria DOS FILAS CON LA MISMA `clave` y un EMPATE en el join
                   de `estabiliza` cada dia. Determinista -- y conviene que la clave lleve la
                   zona PARA NO TENER QUE DESEMPATAR. Es una MEJORA, no un arreglo.
                -> *** NO HAY NINGUN FALLO ESPERANDO AQUI. Se creyo que si, y era falso. ***

  NO SE TOCA:   core/grupos_ids.estabiliza(...)
                -> recibe `grupo` y le pone numero. Con la clave bien, ya funciona.
  ```

  *Y la corrección, que es lo que más vale de esta serie*: **se midió `estabiliza` con «dos zonas», se vio que
  uno de los dos grupos recibía un id nuevo, y se le puso nombre — «el defecto de las dos zonas».** *Al escribir
  la prueba se vio que **el caso normal hace exactamente lo mismo**:* **es un grupo que se PARTE, y un grupo que
  se parte reparte el número — que es lo único que se puede hacer.** *No hay defecto.*

  ***La lección: no fue una suposición sobre el código, fue una suposición sobre una medida propia.*** *Una
  medida mal interpretada es peor que ninguna, porque viene con números y parece probada. Lo que la caza es
  contrastar: **poner el caso sospechoso al lado del caso normal.*** Ver
  `docs/investigaciones/B03-la-octava-medida-estabiliza-con-dos-zonas.md` (la conclusión falsa) y
  `tests/test_b03_herencia_con_dos_zonas.py` (la que la desmintió, con las tres pruebas que quedan).

  la forma:    `region` AL FINAL del SELECT de `donde_comprar`  (probado: el error no fue de indices)
  el atajo que NO vale: anadir la columna sin tocar la identidad del grupo

  **Y LA NOVENA MEDIDA, HECHA — con esto el mapa esta entero y sin incognitas:**

  ```
  HECHO:    core/grupos_ids.tabla_de -- guarda la zona, si las filas la traen     -- 0d1a50c
  HECHO:    plataforma/api/cesta.py -- donde_comprar la pide, si esta             -- f952c80

  MEDIDO:   projects/cesta/emparejar.py :: grupos_de(...)
            -> la zona va AL LADO DE `cadenas`, en la misma invariante.
            -> «un grupo no puede tener dos productos de la misma cadena» pasa a ser
               «... de la misma cadena EN LA MISMA ZONA».
            -> NO HAY QUE DISENAR NADA: es un parametro al lado de uno que ya existe.

  MEDIDO:   core/matching.py :: agrupar_enlaces(...)
            -> tiene `cadenas: list[str] | None = None` -- ES PARA `cadenas`, NO para atributos.
            -> HAY QUE GENERALIZARLA. Y la condicion que no se puede saltar es:
               *** SIN ZONAS TIENE QUE SALIR EXACTAMENTE LO MISMO QUE ANTES ***
               (es el caso de las otras cinco fuentes, y el de todos los dias hasta hoy).

  FALTA:    (1) generalizar la invariante a (cadena, zona), SIN CAMBIAR el caso sin zona
            (2) que la clave con la que se hereda incluya la zona
            (3) y que donde_comprar HAGA algo con ella -- comparar dentro de la zona, o avisar
  ```

  ***Y LA PRUEBA DE ESE CAMBIO NO ES «con zonas funciona»: ES «SIN ZONAS, SALE LO MISMO».*** *Que es la forma
  de probar una generalizacion, y es lo que hay que escribir primero.*

  **Y ESA PRUEBA YA ESTA ESCRITA — DOS VECES.** *La zona es **el tercer parametro** que entra en
  `agrupar_enlaces`, y los dos anteriores dejaron su prueba:*

  ```
  tests/test_invariante_reparto.py -- 8 pruebas, todas pasan
    test_rechaza_la_union_que_dejaria_una_cadena_repetida      <- LA INVARIANTE
    test_sin_el_parametro_se_comporta_como_antes               <- el parametro `cadenas`
    test_sin_el_parametro_de_nombres_nada_cambia               <- el parametro `nombres`
  ```

  *Y los tres pasos, entonces, no hay que inventarlos — **hay que copiar la forma**:*

  ```
  1) agrupar_enlaces(..., regiones: list[str] | None = None)   -- igual que `cadenas` y `nombres`
  2) que la union por cadena se haga por (cadena, zona) cuando la zona viene
  3) y que con regiones=None salga EXACTAMENTE lo mismo que hoy
  4) y una prueba nueva: test_sin_el_parametro_de_zonas_nada_cambia
  ```

  *De las nueve medidas **ninguna dejo una incognita**; y **las tres que parecian diseno resultaron ser
  precedentes** — `grupos_de` ya tenia la invariante (para las cadenas), y las pruebas ya estaban escritas.*
  Ver `docs/investigaciones/B03-la-red-de-seguridad-ya-existe.md` y `...la-pieza-central-ya-tiene-la-forma.md`.

  **Y LA DECIMA MEDIDA, HECHA — y esta mueve el punto de partida del cambio:**

  ```
  core/matching.py:447 :: enlaces(filas_completas, umbral, ...)
    -> «Lo primero que hace es quedarse con esas SEIS COLUMNAS Y TIRAR EL RESTO: ver `adelgaza`.»
    -> *** POR ESO LA ZONA NO LLEGA: `adelgaza` la tira. ***
    -> El emparejamiento por pares de cadenas NO SABE DE ZONAS -- no por decision,
       porque NADIE SE LAS PASO.
  ```

  *Y el cambio son **cuatro funciones, y el orden de la lista es el orden de la cadena de datos**:*

  ```
  1) matching.py :: adelgaza(...)       -> QUE CONSERVE `region`   *** EL PRIMERO ***
     -> sin esto, los otros tres no sirven de nada.

  2) matching.py :: _asignacion_1a1(...) -> EMPAREJAR POR PAR DE (CADENA, ZONA)
     -> AQUI NACE LA INVARIANTE (el docstring: «dentro de cada bloque y de cada par de cadenas»).

  3) matching.py :: agrupar_enlaces(...) -> `regiones` al lado de `cadenas`; la guarda por (cadena, zona)
     -> con su prueba test_sin_el_parametro_de_zonas_nada_cambia (el molde ya existe dos veces).

  4) grupos_ids.py :: tabla_de(...)      YA HECHO -- 0d1a50c
     -> y `grupos_de` (emparejar.py) pasa `regiones` al lado de `cadenas`.
  ```

  ***Y AL REVES -- EMPEZANDO POR LA GUARDA, QUE ES LO QUE EL PLAN DECIA -- EL CAMBIO HABRIA PASADO LAS PRUEBAS Y
  NO HABRIA HECHO NADA***: *la zona no llega hasta alli.* Ver
  `docs/investigaciones/B03-la-decima-medida-los-enlaces-y-adelgaza.md` y `...la-invariante-nace-en-los-enlaces.md`.

  **Y LAS SIETE PIEZAS, HECHAS** — *la zona recorre ya todo el emparejador:*

  ```
  HECHO:   matching.py :: adelgaza          -> conserva `region`              -- 27756cd
  HECHO:   matching.py :: agrupar_enlaces   -> la guarda por (cadena, zona)   -- 75e625f
  HECHO:   grupos_ids.py :: tabla_de        -> la clave que se hereda         -- 0d1a50c
  HECHO:   emparejar.py :: grupos_de        -> pasa `regiones`                -- 7f0b72d
  HECHO:   api/cesta.py :: donde_comprar    -> pide la zona (si esta)         -- f952c80
  HECHO:   emparejar.py :: COLUMNAS         -> la zona ENTRA por aqui         -- f469015
  ```
  *(`emitir/ocupados` -- dea976a -- y `_bloque` -- 2ad380c -- se **revirtieron** en 0206c2a: **no hacian falta**,
  porque la invariante de la cadena ya separa las zonas.)*

  ***Y EL TRANSPORTE ESTA CERRADO, PUBLICADO Y COMPROBADO***: *`grupos.parquet` con `region`, **63 columnas,
  LIDL 79 de 79**; version `v20261013-155356`; y **38961 grupos sin ninguno con dos zonas**.*
  *Ver `docs/investigaciones/B03-relevo-en-una-pagina.md`.*

  *Y `precio_diario` conserva `1643898 filas, 38 dias` -- el historico rehecho de la ronda 46.*

  ---

  ### ***** CORRECCION IMPORTANTE: LA CONDICION DE LA ZONA NO HACIA FALTA *****

  *Este tramo se dio por cerrado en la ronda 90 con una conclusion que **resulto falsa**, y hay que leer esto
  antes de tocar nada de la zona:*

  **1. La direccion se aplico al REVES, y se revirtio.** *Se relajo la invariante de la cadena a «misma cadena y
  misma zona», con lo que **dos zonas del mismo producto dejaron de estar prohibidas y se juntaron**.*
  *Medido con una prueba de fuego:* `[0, 1, 0]` sin zonas contra `[0, 0, 0]` con zonas -- **al reves**.
  *Revertido en `0206c2a`.* Ver `docs/investigaciones/B03-EL-CAMBIO-ESTA-INVERTIDO.md`.

  **2. Y la condicion que se iba a anadir TAMPOCO hace falta.** *Se escribio la prueba del objetivo con
  `xfail(strict=True)`, esperando que fallara -- **y paso**.* *Y lo que dice ese `XPASS` es la conclusion:*

  > **LA INVARIANTE DE LA CADENA YA SEPARA LOS DOS PRECIOS DE UN MISMO PRODUCTO EN DOS ZONAS**, porque son dos
  > productos de la misma cadena -- y un grupo no puede tener dos.

  *O sea: la zona **separa sola**, y lo unico que hacia falta era **no relajar la invariante que ya estaba**.
  Ver `tests/test_b03_la_zona_separa.py` (dos pruebas, verdes) y el commit `372968b`.*

  ### *** LO QUE QUEDA DE B03, DE VERDAD, Y ES SOLO ESTO ***

  ```
  (1) que `donde_comprar` HAGA ALGO con la zona -- Y `grupos` YA LA TIENE, Y LA API YA LA SIRVE.
      decision escrita: que el precio que se elija sea de la zona del usuario,
      y decir cuando no haya con quien comparar.
      *Y hoy no cambia nada: solo Lidl declara zona, y es una sola.*
  ```

  **NO hay que tocar la guarda del emparejamiento.** *Se quedo como estaba, que es lo correcto.*

  ---

  ### *** EL TRANSPORTE DE LA ZONA: CERRADO Y PUBLICADO (rondas 82-99) ***

  ```
  silver (79 de 79)
    -> projects/cesta/emparejar.py :: COLUMNAS     -- f469015  *** EL SITIO 15, Y EL PRIMERO ***
    -> core/matching.py :: adelgaza                -- 27756cd
    -> groups_de (pasa `regiones`)                 -- 7f0b72d
    -> agrupar_enlaces (acepta `regiones`)         -- 75e625f
    -> core/grupos_ids.py :: tabla_de              -- 0d1a50c
    -> grupos.parquet, la vista `grupos` y LA API  CON region · 63 columnas · LIDL 79 de 79
    -> api/cesta.py :: donde_comprar               la pide SI ESTA -- f952c80
  ```

  *Y comprobado sobre el catalogo entero:* **38961 grupos, y NINGUNO con precios de dos zonas** -- *sin ninguna
  condicion nueva, porque **la invariante de la cadena ya los separa**.* Ver
  `tests/test_b03_la_zona_separa.py` y `docs/investigaciones/B03-relevo-en-una-pagina.md`.

  *Version publicada: `v20261013-155356`.* **Y `precio_diario` conserva `1643898 filas, 38 dias`.**

  *** Y LAS DOS LECCIONES, QUE VALEN MAS QUE EL CAMBIO ***

  *1) **Quince sitios**, cuando el plan decia cuatro funciones -- y **el que faltaba era el PRIMERO de todos**, el
  que LEE el catalogo, porque se hizo el camino **de dentro hacia fuera**.* Lo que lo habria evitado:
  **preguntar «¿por donde ENTRA este dato?» al principio, en vez de «¿donde se usa?».**

  *2) Y **una prueba que PASA puede decir mas que una que falla**: la de la ronda 93 dijo que el trabajo que se
  iba a hacer **no hacia falta** -- y hoy hay 38961 grupos que lo confirman.*

  *Y la leccion de las catorce medidas, que vale mas que el cambio*: **el plan decia cuatro funciones y son siete
  sitios en cuatro ficheros; y el que impone la regla -- `ocupados` -- no estaba en ninguno de los tres planes
  (ni `donde_comprar`, ni la guarda, ni `_asignacion_1a1`).** *Cada uno de esos planes habria producido **un
  cambio correcto, probado, y sin efecto**.* **Y la prueba que mas enseno fue UNA QUE PASO.**

  *La decisión de identidad **está tomada**: la zona entra en el grupo — y por qué, en
  `docs/investigaciones/B03-la-decision-de-identidad-tomada.md` y en `...correccion-la-zona-entra-en-el-grupo-no-en-la-clave.md`.*
  **Un cambio de `SCRAP_CP` reagrupa, no renueva identidades de producto**, y eso se ve en la cobertura del día,
  que ya lleva `region`.

### B04 · 13/10/2026 · commits `e2c3597` … `3ffa9a7`

- **Cambio o hallazgo nuevo**: **el defecto del dueño, reproducido y corregido en los DOS puentes.**
  `_del_plan` no escalaba por comensales y **descartaba la segunda receta**; `recetas.a_la_lista`
  escribía `round(ln.cantidad) or 1` (300 g → 300 unidades) y `None` de nota. **Los dos puentes quedaron
  unificados en `previa_compra.previa_de_compra`**, el id de línea pasó a ser determinista (`uuid5`) y la
  nota dice las recetas, la cantidad, los envases y el sobrante. Además: `grupo_id` y `recetas` se
  añadieron a `LineaDeCompra` (se nombraban y no se leían), la **despensa** se dice y sólo se descuenta
  si la persona lo elige, y `en_tienda` dejó de vetar Lidl.
- **Pruebas ejecutadas**: **13 pruebas de B04**, con **mutación controlada**: las tres mutaciones hacen
  fallar la prueba (`SystemExit`/assert) → **protegidas**. **Aceptación 27 de 27 contra la API real**
  (cinco recetas, dos listas, dos marcas, otra semana, versiones y reintentos). `ruff` limpio · suite
  **2012 pasan, 0 fallan**.
- **Evidencia**: `tests/test_b04_los_dos_puentes.py` · `tests/test_b04_contrato_de_del_plan.py` ·
  `data/debug/b04_mutaciones.py` · `data/debug/b04_aceptacion.py`.
- **Pendiente o límite exacto**: nada del criterio de B04. *La admisión **por línea** de Lidl (con precio
  observado) sigue pendiente, pero eso es de B03.*
- **Siguiente comando**: `uv run pytest tests/test_b04_los_dos_puentes.py tests/test_b04_contrato_de_del_plan.py -q`

## Plantilla de actualización corta

- Paquete / commit / fecha de evidencia:
- Cambio o hallazgo nuevo:
- Pruebas ejecutadas y resultado:
- Evidencia (ruta/version/hash/recibo):
- Pendiente o límite exacto:
- Siguiente comando o acción:

Mantener una entrada por paquete; no copiar conversaciones completas ni actualizar
repetidamente «sigue Running» sin nueva información accionable.
