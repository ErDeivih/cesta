# Fase 2 de Cesta · matriz de capacidades y veredicto

Fecha: 13 de octubre de 2026. **Todo lo que hay aquí está medido y commiteado**, con el comando al lado.
*Lo que no se ha hecho se dice como no hecho; los números salen de las ejecuciones, no de la intención.*

---

## 0. Aviso: **esta matriz esta desactualizada, y es culpa de mi proceso**

*Escrito en la ronda 131, al descubrirlo.*

**Esta matriz no se ha actualizado desde `3fd8e93`** -- *«F03 CERRADO»* --, **y lo dice su propio numero**:
dice **«1.714 pruebas»** y la suite va por **1.800**. *Y desde F03 hasta aqui se han medido **F04 a F12**.*

### Que paso, exactamente, porque es el mismo error que esta fase lleva diez veces encontrando en el codigo

**Mis actualizaciones se hacian asi:**

```python
m = M.read_text()
m = m.replace("| **Oferta caducada** |", "| **Nueva fila** |\n| **Oferta caducada** |", 1)
M.write_text(m)
```

**Y el ancla `| **Oferta caducada** |` **no existe en este fichero**.** *La tabla es de
`| capacidad | estado | con que se comprueba |`, sin negritas de ese tipo.* **Asi que `str.replace` devolvia
**la misma cadena**, `write_text` la reescribia **igual**, y el commit no cambiaba nada** -- *y **el script decia
«matriz corregida»** igual, porque **no comprobaba el resultado**.*

**Es exactamente lo que esta fase ha encontrado diez veces en el codigo del proyecto**: *`archivar` que no
levanta y no borra, el `.catch` que se traga el fallo, `comparacion: null` que evita una lista vacia.*
**Una operacion que informa de exito y no hace nada.** *Y esta vez la escribi yo, y la repeti **en cada ronda**
desde F03.*

### Y por que se descubrio

**Al intentar anadir una fila de F12 y ver que `grep N06` no encontraba nada.** *El instrumento que lo cazo fue
**buscar el resultado**, no **volver a escribir la operacion** -- que es la unica forma de cazar este error.*

### Lo que hay que hacer, y es de la ronda siguiente

1. **Rehacer la tabla de §1 y §2 desde cero**, con lo medido de **F00 a F12**: *lo que funciona, lo que no
   existe, y lo que espera decision.*
2. **Y actualizar las cifras**: *1.714 -> **1.800 pruebas, 3 xfailed***, y el catalogo real.
3. **Y desde entonces, comprobar cada edicion de este fichero**: *`assert` de que la fila entro, o `git diff`
   no vacio.* **Escribir no es actualizar.**

*Lo que **si** esta al dia, y se ha ido escribiendo sin fallar: `docs/SUPERAPP-FASE2-EJECUCION.md` (el tablero, con
las tres decisiones), y los **diez informes** de `docs/investigaciones/`.*

---

## 1. Qué se puede hacer hoy, de verdad

| capacidad | estado | con qué se comprueba |
|---|---|---|
| Buscar un producto y ver su precio por cadena | **funciona** | `/api/buscar?q=leche` → 200, 40 resultados |
| Estimar la lista, por tienda y repartida | **funciona** | **1.800 pruebas** (3 xfailed); oráculo exhaustivo de asignaciones |
| Repartir entre tiendas **eligiendo el óptimo** | **funciona** (≤200.000 asignaciones) | 200 escenarios al azar con **cero discrepancias** |
| Aceptar una alternativa y que el histórico guarde **la comprada** | **funciona** | prueba HTTP que **discrimina** (simulando lo anterior, falla) |
| Cerrar la compra y ver el importe final | **funciona** | **1.800 pruebas** (3 xfailed), base desechable y PostgreSQL |
| Apuntar una comida, reintentar y **no duplicar** | **funciona** | navegador de verdad: **1→1** con arreglo, **1→3** sin él |
| Reintentar dos veces **a la vez** | **funciona** | dos conexiones y barrera; antes: `IntegrityError` |
| Publicar una versión y que **la API la sirva** | **funciona** | Con un **`uvicorn` real**: publicar V2 cambió lo servido en el 8102 **sin reiniciarlo**, y el 8100 (real) no cambió |
| **Publicar durante el uso, en un navegador** | **funciona, y está probado** | `plataforma/prueba_f03_publicacion.py` **PASA**: la pantalla pasa de 19,81 a 20,81 €; previa de lista, previa de consumir y **alta en el diario** con la publicación a mitad |
| Reanudar una captura **sin volver a pedirla** | **funciona** | `alcampo._cache_limpia` rechaza un reto cacheado |
| Saber **qué se ha capturado, procesado y publicado** | **funciona** | el resumen, corriendo |
| **Calorías y tabla nutricional** | **parcial: 22,8 %** (11.064 de 48.606 grupos) | *Esta fila decía «Día: 6.331 productos» y **el catalogo mide otra cosa**: 11.064 de 48.606 grupos con `kcal_100g` (22,8 %), Día 2.826 (48,9 %), Carrefour 6.512 (40,2 %), Mercadona 1.900 (45,1 %), **Alcampo y Aldi 0**. La fuente es Open Food Facts por EAN. **Las dos cifras pueden ser de cosas distintas y no he vuelto a medir la primera**: se deja dicho en vez de sustituir una por otra.* *Ya extraída por `collectors/dia.py:165 _nutricion`* en cada pasada diaria, **en el maestro, con la base declarada** (`nutricion_por`) y rechazando las bases incomparables. *Mercadona: 4.494 productos, **0 tablas** — su fuente no las publica* |
| Fichas: **ingredientes y alérgenos** | **extractor hecho y probado** | `ficha_mercadona.py` (7 pruebas) y `ficha_dia.py` (9), ambas contra crudo real. *El crudo de hoy trae **3 fichas** de Mercadona (de 155) y **4** de Día (de 547): lo que falta es **pedir*** |
| **Vaciar la lista y volver a comprar, desde el móvil** | **funciona** | `prueba_f07_pasos.py` **PASA**: **4 toques** en la cuenta vacía; y `prueba_f07_lista.py` llega a `/compra/listas` y el encabezado **`'BEBIDAS'`** prueba que `porPasillo` agrupa |
| **Que una receta de otra persona no se vea** | **funciona** | `test_fase2_f09_recetario.py`, **9 pruebas**: el de fuera **no lee, no cambia, no archiva y no ve las versiones**; y `listar` no mezcla dueños |
| **Que editar una receta no cambie lo de ayer** | **funciona** | *v1 sigue diciendo «harina» después de editar a «patata»* — versiones autocontenidas |
| **Escalar raciones sin inventar** | **funciona** | *`kg`+`kg` = 1,5; y **a la sal no le aparece cantidad*** |
| **Ver lo que costaría la compra antes de decidir** | **funciona** | `core/previa_compra`: **la ruta `GET` que no escribe**, y devuelve **lo que no se puede comprar con su motivo** |
| **Saber cuánto usas y cuánto compras** | **funciona** | `logica/costeReceta.ts`: **los dos números separados** (*«200 g» de un envase de 1 kg: usas 0,24 €, compras 1,20 €*) y `ud` sin prorrateo |
| **Leer un código de barras sin cámara** | **funciona** | `Escaner.tsx`: **el texto es el camino principal**, la cámara un botón que **sólo aparece si el navegador sabe leer**; y `comparacion: null` → **«no puedo comparar»** |
| **Meter una receta en el diario y que no se pierda la versión** | **funciona** | `diario.py:154`: **una entrada de receta sin versión no entra** (*`raise`*: *«sin ella no se puede releer»*) |
| **Importar una receta de fuera** | **no existe** | *ni ruta, ni pantalla, ni `fuente` de receta* — `R02` |
| **Cocinar paso a paso, con temporizadores** | **no existe** | *los «temporizador» del código son **debounce de búsqueda*** — `R05` |
| **Tener despensa y descontar existencias** | **no existe** | *ninguna de las 13 tablas es de despensa; `preferencia` está vacía* — `R08` |
| **Que `1 kg` y `500 g` se sumen en la compra** | **no** — *defecto fijado* | `xfail(strict=True)`: `kg+g` **no se suman** y se nombran como incompatibles, cuando la aceptación dice «kg/g **compatible**» |
| Usar Cesta con la API caída | **no medido** | — |
| Defensa CSRF | **hay defensa, y 5 pruebas** | `SameSite=Lax` + `HttpOnly` (`main.py:88`); **26 endpoints que mutan, todos no-GET**; **ningún GET exige escribir**. *Falta el ensayo con navegador: las pruebas del CORS usan un middleware con los mismos parámetros, no la app real* |

---

## 2. Matriz por paquete

| paquete | estado | lo que falta, concreto |
|---|---|---|
| **F00** reconciliar | **cerrado** | 10 hallazgos contrastados, **1 defecto real** (`alerta.grupo_id` sin identidad estable) — arreglado con la migración 016 (`ean`). |
| **F01** producto efectivo | **cerrado** | A pedido, B aceptada, 3 unidades y 3×2 → **500**, no 900; motor, cierre e **HTTP verificado**. |
| **F02** diario | **cerrado** | Reintento verificado en la UX, carrera arreglada, y la **clave de operación** sostiene los dos casos (`N04`/`N01`). |
| **F03** publicación | **cerrado** | Los recorridos de navegador **medidos y pasando**: `prueba_f03_publicacion.py` **PASA** (19,81 → 20,81 €, con el alta en el diario incluida). |
| **F04** privacidad/CSRF | **cerrado** | `SameSite=Lax` + `HttpOnly`, 26 endpoints que mutan y **ningún GET que escriba**, con 5 pruebas. *Falta el ensayo con navegador.* |
| **F05** fichas | **cerrado** | Reconciliador, `ficha_carrefour` y ejecutor con sus pruebas. **Cobertura real de nutrición: 22,8 %** (11.064 de 48.606) — *Alcampo y Aldi, 0*. |
| **F06** matching y optimizador | **cerrado** | Optimizador con oráculo, garantía y límites publicados. |
| **F07** compra familiar | **medido** | **4 toques** en la cuenta vacía, dos sesiones y otro hogar con sus pruebas (4+1 xfail, 6). **Un defecto fijado**: `cambia_linea` no consulta `momento`. |
| **F08** comparar y presupuesto | **cerrado** | `C06`–`C10` con su parte principal medida y **los cinco casos de su aceptación cubiertos**. **Deja tres decisiones del dueño** (qué es «presupuesto», el coste de desplazamiento, y la unidad de la línea). |
| **F09** recetario | **cerrado** | `R01` hecho, `R03`/`R04` medidos y pasan (9 pruebas), **`R02` no existe** (importar: tres capas lo confirman). |
| **F10** plan y cocina | **medido** | `R07` hecho (`previa_compra`); **`R05` no existe** (ni pasos ni temporizadores: *«no hay pasos que pasar»*); `R06` exige fecha. **Un defecto fijado**: `kg/g` no se suman. |
| **F11** despensa | **medido** | **`R08` no existe** (cuatro capas); **`R09` hecho** (`costeReceta`, con los dos números); `R10` depende de `R08`. |
| **F12** calorías | **cerrado** | Los seis criterios con su parte principal medida, y **cuatro los contesta `core/diario.py`**: `N01`/`N04` (la **clave de operación** — *el cliente la genera y la repite si reintenta; y dos comidas legítimas llevan claves distintas*), `N06` (**versión obligatoria**, con `raise`), `N05` (**fuente declarada**: `NOT NULL` y conjunto cerrado de cuatro, con `raise`), `N02` (el escáner: **texto principal y cámara como botón**), y `N03` (la base: `100g` 2.485, `100ml` 771, *nulo* 689 → «100 g»; y **`porcion`: 0 productos**, así que la base que no tendría tamaño no la usa nadie) |
| **F13–F16** | **sin empezar** | *Van después, según sus dependencias.* |

**Los cuatro criterios que la fase ha encontrado sin cumplir, y su clase:**

1. **`R02`** importar recetas — **no existe** (tres capas).
2. **`R05`** modo cocina — **no existe** (ni pasos ni temporizadores).
3. **`R08`** despensa — **no existe** (cuatro capas).
4. **`R10`** buscar por lo disponible — **depende de `R08`**.

*Ninguno es un defecto: son **funciones que nadie ha escrito**, y las cuatro tienen nombre y casos de aceptación descritos.* **Y hay cuatro defectos reales**, los cuatro **medidos y con su prueba**: la alerta sin identidad, la contabilidad de la cola, la cantidad que gana «el último», y el `kg/g`.

---

## 3. Pruebas reproducibles

**Las puertas**, y lo que dan hoy:

```
uv run ruff check . --output-format=concise          limpio
uv run pytest -q                                     1800 pasan, 3 xfailed, 0 fallan  (~3 min)
npm test          (cliente)                          42 pasan
npx tsc --noEmit                                     0
npm run build                                        154 modulos
```

**Los ensayos que existen y qué demuestran**, por si hay que volver a ellos:

| ensayo | qué demuestra |
|---|---|
| `tests/test_fase2_f01_sustitucion.py` | A pedido, B aceptado, 3 unidades y 3×2 → **500**, no 900 |
| `tests/test_g03_cierre.py` | el cierre archiva **lo que puso el precio**, por HTTP |
| `tests/test_fase2_f02_concurrencia.py` | misma clave a la vez → **una** entrada; choque → **400** |
| `tests/test_fase2_f09_recetario.py` | **9 pruebas**: aislamiento (el de fuera no lee/cambia/archiva/ve versiones), versiones persistentes, `listar` sin mezclar, y el escalado sin inventar |
| `tests/test_fase2_f10_previa_compra.py` | **8 pruebas**: `kg`+`kg` suma, **`kg`+`g` no** (*xfail: el defecto*), `ud` y `ml`/`g` se nombran, la sal no se compra, y **la previa no modifica la entrada** |
| `plataforma/prueba_f07_pasos.py` | navegador: **4 toques** para el recorrido de la cuenta vacía |
| `plataforma/prueba_f07_lista.py` | navegador: llega a `/compra/listas` **pulsando «Ver mi lista»**, y el encabezado `'BEBIDAS'` prueba el agrupado por pasillo |
| `plataforma/prueba_reintento.py` | el reintento **en un navegador**: 1→1 contra 1→3 |
| `core/oraculo_reparto.py` + su prueba | **cero discrepancias** en 200 escenarios al azar |
| `tests/test_fase2_f03_publicacion.py` | publicar tarde, fallo en el veredicto, e invariantes |
| `tests/test_fase2_f03_version_vigente.py` | la versión vigente **sin arrastrar polars** |

**Y el estado del dato, hoy**: `/api/estado` dice **`coherente: False`** —*los precios son del 11 y el
puntero del 7*—, y el resumen lo dice con las cuatro patas.

---

## 4. Veredicto honesto sobre uso doméstico local

**Lo que está listo para usarse en casa, hoy:**

**La compra.** *Buscar, estimar, repartir entre tiendas, aceptar alternativas, cerrar y consultar el
histórico.* **Es la parte más madura y la que tiene las pruebas más duras**: un oráculo independiente que
enumera asignaciones, un cierre que guarda el producto efectivo, y **1.800 pruebas** que pasan (3 xfailed). *Si algo
de esto se rompe, hay una prueba que lo dice.*

**El diario.** *Apuntar comidas, reintentar sin duplicar, y que dos envíos a la vez no dupliquen.*
**Verificado en un navegador de verdad, no sólo en el motor**: *el ensayo reproduce el defecto (1→3) y
confirma el arreglo (1→1).*

**Lo que NO está listo, y conviene decir por qué:**

- **Las fichas de producto.** *La cola medida es **72.319 pendientes / 7.593 correctas** (`data/inventario.sqlite`); esta linea decia 79.887 y 28, y **no he vuelto a medir esos dos numeros**, asi que se dejan los mios y se dice que discrepanan.* **Cualquier cifra de nutrición o de
  ingredientes que se enseñe hoy cubre el 0,04 % del catálogo**, y *la ausencia no es una limitación de
  fuente: es trabajo sin ejecutar.*
- **Usar la app con la API caída.** *No medido.*
- **La publicación**: funciona y está probada por API, pero **falta el recorrido de navegador**, y
  **`/api/estado` lleva desde el 7 de octubre declarando el catálogo incoherente** porque el puntero no
  se ha movido. *Publicar lo arregla y es reversible; es una decisión de operación, no de código.*

**El veredicto, en una frase**: **para hacer la compra y llevar el diario, esto sirve hoy y está
probado; para mirar nutrición, todavía no, y la razón es que no se ha ejecutado el trabajo, no que no se
pueda saber.**

---

## 5. Lo que hay que hacer a continuación, en orden

1. **Pedir las páginas de producto de las cadenas de las que se sabe la forma** — *Mercadona ya tiene
   extractor (`ficha_mercadona.py`) y el crudo de hoy sólo trae 3 fichas: lo que falta es **pedir**, no
   extraer* —, y **escribir el lector de Día**, que tiene otra forma y hoy da 0 de 547. *El mapa está cerrado*: **ninguna de las cinco cadenas medidas
   publica nutrición numérica** (mercadona 6 fichas, alcampo 59 claves, aldi 18, dia, lidl documentado),
   así que **las calorías no se pueden enseñar con estas fuentes**; los ingredientes y alérgenos **sí**.
   Queda **carrefour** (HTML) sin medir. *Medido
   para Aldi, leyendo el crudo que el colector ya guarda: su API trae 18 campos y **ninguno es
   nutrición** — no es «no lo hemos pedido», es que **la fuente no lo publica en la API que se usa**.*
   La salida es la misma que Lidl documenta: **parsear el HTML o ir a fuente externa**. *La misma
   pregunta, para alcampo, carrefour, dia y mercadona, antes de escribir nada.*
2. **Los dos recorridos de navegador de F03** —*la receta está en
   `docs/investigaciones/F03-publicacion.md` §15: `CESTA_GOLD` a un sandbox, API en el 8101*—.
3. **Decidir sobre el puntero** (`20261007-103000` contra un gold del 11): publicar o dejarlo. *Es de
   operación.*
4. **Las unidades del diario** (g/ml/raciones) y la vista previa congelada —*lo que queda de F02*—.
5. **Los ocho hallazgos de F00** que siguen sin contrastar, y **F04** (CSRF) —*que el informe anterior
   aplazó con una inferencia que el encargo no acepta*—.
6. **El banco de matching de F06**, y después **F07–F16**.

*Los puntos 1, 3 y 4 son pequeños y concretos. El 6 y los paquetes F07–F16 son el grueso que queda.*
