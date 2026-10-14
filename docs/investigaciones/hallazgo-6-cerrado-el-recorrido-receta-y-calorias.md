# Hallazgo 6 · **CERRADO** -- el recorrido recorre Recetas y Calorias, y da verde

*`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:65-66`: *** «El recorrido de Recetas/Calorias del adjunto
observa estados vacios. *Prueba que las paginas abren, *** no cinco recetas, cantidades, consumo y
persistencia»***. *Y el encargo lo repite: *** «La aceptacion principal son cinco recetas semanales con
cantidades, compra y porciones reales que persisten tras recargar».** *

---

## 1. Las cinco puertas, verdes, con esto dentro

```
*** `uv run ruff check .` ***                     *** All checks passed! *** ✓
*** `uv run pytest -q` ***                        *** 2.056 passed · 0 failed · 0 errors · 17 skipped *** ✓✓✓
*** `uv run python -m plataforma.prueba_e2e` ***  *** == TODO BIEN · exit 0 *** ✓✓✓
*** `npm test` ***                                *** 81 pass · 0 fail *** ✓
*** `npx tsc --noEmit` *** y *** `npm run build` ***  *** exit 0 *** ✓
```

## 2. *** Y el recorrido comprueba la aceptacion principal, punto por punto ***

```
*** LAS CINCO RECETAS ***     *** `recetas creadas: 5 de 5` *** *(-- con **datos conocidos** --)* ✓
*** LAS CANTIDADES ***        *las ocho lineas entran **con su nombre y su cantidad** ✓
*** EL DEDUPE ***             *dos recetas con el MISMO ingrediente *** se consolidan en UNA linea *** ✓
*** LA PERSISTENCIA ***       *** `tras recargar: 15 lineas` *** ✓
*** LA IDEMPOTENCIA ***       *misma `clave_operacion` -> **el mismo id**; *clave distinta -> **otro
                              apunte** ✓
*** LA COBERTURA ***          *** `kcal_conocida=None · completo=False` *** *(-- «Compra no es
                              consumo»: *el diario **no inventa** la kcal que la fuente no publica --)* ✓
```

## 3. *** Y la discrepancia que persegui CUATRO rondas **no era un defecto** ***

*Dije, en las rondas 427-430, que *** «la vista previa miente» ***: *«dice 8 entrarian y 0 ya estaban,
*y el POST no trae ninguna».* *** Y era falso, *y el volcado final lo enseña: ***

```
*** LA PREVIA SE PIDE *** ANTES *** DEL POST *** *
   *-- *su `ya_estaban` dice **lo que habia EN ESE MOMENTO** ✓
*** Y EL POST TRAE 0 SI YA ESTABAN *** de una corrida anterior *
   *-- *** el recorrido ACUMULA ESTADO entre corridas *** *(-- crea recetas nuevas cada vez --)* ✓
*** -> **las dos cosas son verdad a la vez** ***, *y **parecen contradecirse si se comparan de memoria** ⚠️
*** Y EL VOLCADO ***, llamando a `main._del_plan` **a mano**: *
   *`planificadas` son las ocho, *con destino *** `(None, None)` ***, *
   *y *** `_ya_estaba` da `True` en las OCHO *** ✓✓✓
*** y **la comprobacion correcta**, ya en el recorrido: *** «el puente no trajo nada, y `_del_plan`
   confirma que *** ya estaban 8 de 8 ***» ✓
*** -> **ni la previa miente, ni `_ya_estaba` esta mal, ni `_del_plan` calcula dos cosas distintas** *** *
```

## 4. *** Y el defecto de tipo, que si era real, y aparecio por abrir esto ***

```
*** `sqlite3.ProgrammingError: Error binding parameter 3: type 'UUID' is not supported` *** *
*** -> `core/recetas.py` y `core/diario.py` declaran `propietario: str` en *** QUINCE *** funciones -- *
   *y **su docstring lo dice**: *** «**Privacidad, implementada** … y *** TODAS *** las operaciones lo
   exigen» *** -- *y **no lo comprobaba ninguna** ⚠️
*** -> se arregla en *** `core/dueno.py` ***, *un decorador que **lee el tipo y convierte**, *
   *aplicado a **las diez del recetario y las cinco del diario** ✓ *(-- `10` y `5` --)*
*** -> y **se convierte, no se rechaza** ***, *porque **el criterio lo tiene escrito el proyecto**
   *donde el error aparecio la primera vez: *** «El id, siempre como texto… *** Aqui se lee, y se
   convierte ***» *** ✓
*** -> **y no se ve por HTTP**: *el `id` de la sesion **ya es cadena**; *el `UUID` solo aparece cuando
   **lo inyecta un ensayo** con `dependency_overrides[usuario_actual]` *-- *que es **lo que hace
   `prueba_e2e.py`**, *y **por eso lo encontro** ✓✓✓
```

## 5. *** Y las cuatro conclusiones mias que cayeron al medirlas ***

```
*** 1) «EL CSRF ES UN HUECO» ***  *-- *y el plan **ya lo habia avisado** en su bibliografia:
   *«revisar *** la conclusion excesiva de SameSite ***… **no convertir la recomendacion en un
   requisito de token impuesto sin analizar contexto**»* ⚠️
*** 2) «LA EXCLUSION DE LIDL SIGUE EN PIE» ***  *-- *y se quito **el 13/10**, *con el motivo escrito
   en `main.py:827-843`, *a **quince lineas de donde yo mire** ⚠️
*** 3) «LA PREVIA USA `calculada.ya_estaban`» ***  *-- *y usa **`ya_en_la_lista`** ⚠️
*** 4) «LA VISTA PREVIA MIENTE» ***  *-- *y **no miente**: *era **el orden en que yo leia** ⚠️
*** -> y **las cuatro son el MISMO error**: *** leer una pieza y creer que es el todo *** *
*** -> y **dos las coge yo mismo al medir** *(-- los nombres de los campos, *y el caso limpio --), *
   *y **las otras dos solo midiendo** ✓
```

## 6. Y lo que queda del plan, con esto

```
*** (1) LIDL EN EL CICLO ***  *** CORRE *** ✓ *(-- 79 filas, `ok=True`, en el ciclo del 14/10 --)*
*** (2) LA EXCLUSION GLOBAL ***  *** HECHA el 13/10 *** ✓✓ *-- *y queda **el grano**: *la cesta se
   decide **por cadena**, *y el plan la quiere **por articulo, region y fecha*** ⚠️ *(-- diseño --)*
*** (3) EL ESCALADO Y EL DEDUPE ***  *** HECHO *** ✓✓ *(-- medido en vivo: 3.800 g -> 4 envases --)*
*** (4) LA IDENTIDAD `fuente:id` ***  *** HECHA *** ✓✓
*** (5) EL DESTINO SILENCIOSO ***  *** HECHO *** ✓✓ *(-- y eran **dos** defectos, *no uno --)*
*** (6) EL RECORRIDO ***  *** HECHO *** ✓✓✓ *(-- esto --)*
*** (7) EL CSRF ***  *** MEDIDO *** ✓
*** -> *** SEIS de los siete, hechos o medidos ***, *y **una pregunta de diseño** en el (2) ⚠️
```

## 7. *** Y tres decisiones que son del propietario, no mias ***

```
*** 1) ¿LA LISTA **SUMA** O **SUSTITUYE**? ***  *-- *y **el diario ya respondio que suman**:
   *** «Dos comidas legitimas llevan claves distintas *** y se registran las dos ***» *** ✓
*** 2) ¿QUE ORIGENES SE PERMITEN, Y QUE SE HACE **SIN `Origin`**? ***  *-- *rechazar sin `Origin`
   **rompe el movil**; *aceptarlo **deja el hueco** *(-- *y **esta medido**: *tres mutaciones con
   origen ajeno, *las tres `201` --)* ⚠️
*** 3) ¿LA MARCA DE VISITA SE MUEVE A UN `POST`, O SE DECLARA QUE EL `GET` NO ES SEGURO? ***  *
   *`main.py:724`: *`ver_lista -> marca_visita`, *que hace `INSERT … ON CONFLICT DO UPDATE` ⚠️
   *-- *y **ese lo encontro una herramienta que escribi hoy**, *`scripts/auditar_gets_que_escriben.py`,
   *que **usa `ast` y tiene su propio ensayo de siete casos** ✓
```
