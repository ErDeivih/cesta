# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Estado de la fase

**Matriz de capacidades y veredicto honesto**: [`SUPERAPP-FASE2-MATRIZ.md`](SUPERAPP-FASE2-MATRIZ.md).
*Que se puede hacer hoy, que no, con que se comprueba y en que orden sigue.*

## F00 · los diez hallazgos, uno a uno

*El encargo empieza por aquí: «contrastar los cierres anteriores con los criterios y pruebas reales».*
**Contrastados los diez.**

| # | hallazgo | estado | con qué se comprueba |
|---|---|---|---|
| 1 | Tablero desactualizado | **contestado** | encabezado reconciliado en este mismo fichero |
| 2 | Aceptación rebajada (G02 «texto libre» / G04 histórico) | **contestado** | *G02 pedía **lista**: migración 014 y «la línea sin destino, medida en pantalla». G04: ver F03* |
| 3 | Multi-tienda sin demostrar | **contestado** | `core/oraculo_reparto.py`: **cero discrepancias** en 200 escenarios |
| 4 | Sustitución estimada frente a compra | **contestado** | prueba HTTP **discriminante** (simulando lo anterior, falla) |
| 5 | Reintento manual del diario | **contestado** | `plataforma/prueba_reintento.py`, en navegador: **1→1** contra **1→3** |
| 6 | Clave escrita después del INSERT | **contestado** | misma clave a la vez → **una** entrada; choque → **400** |
| 7 | Publicación y derivados | **contestado** | publicación al final del ciclo, fallo en el veredicto, API leyendo la versión |
| 8 | Fichas sin ejecución suficiente | **contestado** | **Día: 6.331 productos con tabla**, ya extraída; Mercadona 0; otras cuatro sin maestro |
| 9 | Riesgo de identidad estable | **DEFECTO LOCALIZADO** | *Ningún consumidor **de código** (las 3 menciones son comentarios). **Pero `alerta` guarda `grupo_id NOT NULL` y nada más** (`001_esquema.sql:139`), mientras `linea` y `favorito` tienen `producto_id`: **una alerta puede quedar vigilando otro producto tras una reordenación** — [F01](investigaciones/F01-identidad-estable.md)* |
| 10 | CSRF no ensayado | **medido en código** | *`SameSite=Lax` + `HttpOnly`; 26 que mutan, todos no-GET; el GET sospechoso dice `hace_falta_escribir=False`. **Falta el ensayo cross-origin y leer el 2.º** — [F04](investigaciones/F04-csrf.md)* |

**Los diez contrastados**, y **uno de ellos -- el #9 -- ha resultado ser un defecto localizado**: `alerta` ligada al ordinal. *Del #10 falta el ensayo con navegador (no la medición), y del #9 queda que la línea **sin** producto concreto va por el grupo — **declarado, no un descuido**.*

## El arreglo de `alerta`: **hecho** (ronda 49)

**Lo unico de esta fase que hacía algo mal hoy, y ya no.** *Las cuatro piezas, hechas:*

| pieza | estado |
|---|---|
| migración `016`: `ean text` + `COMMENT` | **aplicada y verificada** (la columna existe, con su comentario) |
| escribir el `ean` al dar de alta | `almacen.py:959`, resuelto con `catalogo.grupo` (import perezoso) |
| resolver el `ean` al grupo **de hoy** al evaluar | `alertas._grupo_de_hoy`, usado en las tres decisiones de `evalua` y en `_clave` |
| prueba | `tests/test_fase2_f01_alerta_identidad.py`, **6 pruebas** |

*La fila que existe se queda con `ean` nulo y su `salto_nombre` como ancla* — **es una decisión, no un
olvido: rellenarla con lo que el grupo contiene hoy escribiría un dato estable equivocado.** *Y su
`salto_nombre` sigue diciendo de qué producto era.*

## Siguiente acción

**F03 · la publicación coherente.** Es el siguiente cierre de tu lista —*«optimización entre tiendas,
**publicación** y cobertura de fichas»*— y el reparto ya está cerrado y verificado.

El hallazgo: *«`pipeline.py` todavía captura fallo de publicar; el ciclo reconstruye grupos después del
pipeline. **Auditar cierre de versión y estado diario.** El arreglo de las fechas del puntero no
demuestra coherencia de todos los artefactos.»* **Y su criterio**: *«tres recorridos V1/V2/V3»*.

**Antes de tocar nada: medirlo.** *Qué artefactos publica el pipeline, cuáles se reconstruyen después, y
si el estado diario que ve quien compra es coherente con el puntero durante el cambio.*

**Lo que queda de F06**, enumerado y no cerrado: **el banco de matching** —*positivos/negativos duros por
familia/cadena, precisión/recall/abstención **con denominadores**, y «mismo GTIN no ignora
contradicciones; distinto GTIN no demuestra engaño»*—, sin empezar. *El optimizador sí está cerrado:
**9 discrepancias arregladas, cero en el barrido**, con garantía y límites publicados.*

Y de F06 queda también **decidido y publicado el alcance del `umbral`**, con la evidencia delante: los
tres textos de umbral del catálogo **nombran una marca o familia** (*«PRODUCTOS PASCUAL», «en Nestlé
Cafés», «en PepsiCo»*), dos son `solo_online` y no restan, así que **la exposición viva es 1 de 236** —
*el motor lo aplica por producto, que **subestima** el descuento: cobra de más, el lado conservador*.
Detalle: [`investigaciones/F06-reparto-agrupado.md`](investigaciones/F06-reparto-agrupado.md).

**Lo que queda de F01**: navegador, estabilidad ante reordenación, elegir comprar A otra vez, y migrar
los consumidores del ordinal. **Y de F02**: las unidades (g/ml/raciones) y la vista previa congelada.

No reiniciar el contador ni volver a implementar los campos del diario: existen. Preservar `core/datos/secciones.yml` y `docs/CIFRAS.md`, sin incluirlos en commits. No modificar el estado de investigaciones de RadioPV/CueDigital.

## Estado de paquetes

Estados: pendiente / en curso / implementado sin ensayo / verificado / limitado por fuente / bloqueado / descartado con motivo. Verificado exige todo el criterio, no lectura o build.

| ID | Entregable | Estado | Evidencia / siguiente acción |
|---|---|---|---|
| F00 | Reconciliar aceptación y baseline | **en curso** | Baseline **1.670 pasan, 0 saltan, 0 fallan** (155 s, con `CESTA_POSTGRES` al 5434). Encabezado del tablero G01–G14 reconciliado. Hallazgo 4 **reproducido**. Faltan los otros 8 hallazgos y la matriz S00–S12. |
| F01 | Identidad estable y producto efectivo comprado | **en curso** | Motor, cierre y **HTTP verificado** (la prueba **discrimina**: simulando lo anterior falla). Migración **015**. Falta navegador, estabilidad ante reordenación y migrar consumidores del ordinal. |
| F02 | Reintentos/unidades/privacidad del diario | **en curso** | Reintento **verificado en la UX** (`prueba_reintento.py`: el día 1→3 sin arreglo, 1→1 con él) y **carrera arreglada** (la clave va en el `INSERT`; antes `IntegrityError`). Falta unidades y vista previa. |
| F03 | Publicación y uso concurrente | **en curso** | Publicación al final del ciclo, fallo en el veredicto, **resumen con las cuatro patas** —capturado/procesado/publicado/**reanudable sin red**—, fallos inyectados, **la API lee la versión publicada** (probado) y **una conexión ve una sola versión**. **Y el recorrido de navegador PASA entero**: búsqueda, previa de lista y previa de consumir, con la pantalla pasando de 19,81 a 20,81 € al publicar. |
| F04 | Privacidad/CSRF/restauración | pendiente | HTTP A/B, origen ajeno y copia aislada. |
| F05 | Fichas de seis cadenas/Lidl | **en curso** | **Medido**: la cola tiene **79.887 pendientes y 28 correctas** (todas en Lidl) — *coincide con el número de la revisión, así que no se ha movido*. **La ausencia no es limitación de fuente: es trabajo sin ejecutar.** Falta ejecutar la cola, medir por campo/cadena separando «no lo publica» de «no lo hemos pedido», y el parser. |
| F06 | Matching y oráculo multi-tienda | **en curso** | **Optimizador cerrado**: 9 discrepancias arregladas, **cero en el barrido**, garantía y límites **publicados** en `_mejor_reparto`, y el **alcance del `umbral` decidido con los folletos** (3 textos, los tres por marca; 1 vivo de 236). **Falta el banco de matching.** |
| F07 | Compra rápida y familiar | pendiente | Investigar C01–C05 y medir UI real. |
| F08 | Comparación/presupuesto/ahorro | pendiente | C06–C10, costes y ámbito elegibles. |
| F09 | Recetario/importación/borradores | pendiente | R01–R04 con referencias y fixtures permitidos. |
| F10 | Plan/cocina/puentes | pendiente | R05–R07, HTTP real además del helper. |
| F11 | Despensa/aprovechamiento | pendiente | R08–R10 después de integridad/unidades. |
| F12 | Registro nutricional rápido | pendiente | N01–N06; recientes, porciones, barcode con fallback. |
| F13 | Analítica honesta | pendiente | N07–N09 y gráficos de compra/receta. |
| F14 | Sistema visual aplicado | pendiente | Antes/después de todas las pantallas servidas. |
| F15 | Offline/rendimiento/aprendizaje | pendiente | Recuperación/mediciones y ejemplos locales. |
| F16 | Ensayo integral y cierre | pendiente | Matriz F y capacidades con evidencias. |

## Continuación obligatoria antes de pausar

- Paquete y criterio concreto: **F00 en curso** (ocho hallazgos y la matriz S00–S12); **F01 en curso**
  (navegador, estabilidad de identidad); **F02 en curso** (unidades, vista previa); y **F06 en curso**
  con el defecto del reparto arreglado y el oráculo exhaustivo pendiente.
- Fichero / función / recorrido: `plataforma/api/cesta.py:_mejor_reparto` — *lleva ahora un bloque
  **«Garantía y límites»**: el óptimo por debajo de 200.000 asignaciones, la heurística por encima, que
  el límite es un número de **asignaciones y no de tiempo**, y el alcance del `umbral` con su medición*.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f06_alcance_del_umbral.py` →
  **4 pasan** (13 oct 2026). *Y la medición que decide*: de **236** textos de oferta del silver, **3** son
  de umbral y **los tres nombran una marca o familia**; **2 son `solo_online`** y no restan → **1 vivo**.
  `uv run pytest -q` → **1696 pasan, 0 fallan**; `ruff` limpio.
- Caso que falla o comprobación siguiente: **el banco de matching**, sin empezar. *Y el siguiente cierre
  de la lista del encargo es **F03, la publicación**, que no se ha medido todavía.*
- Cambios conservados / commit: `plataforma/api/cesta.py` (docstring de garantía y límites),
  `tests/test_fase2_f06_alcance_del_umbral.py` (nuevo), `docs/investigaciones/F06-reparto-agrupado.md` y
  este tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límites publicados:* por encima de 200.000
  asignaciones no se promete el óptimo y la respuesta lo dice; el `umbral` se aplica **por producto** y
  eso **subestima** el descuento —*cobra de más, el lado conservador*—, con **1 texto vivo de 236**.
- **Acción inmediata al retomar:** **F03** —medir qué artefactos publica el `pipeline`, cuáles se
  reconstruyen **después**, y si el estado diario es coherente con el puntero durante el cambio—, y
  después el **banco de matching** de F06.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.

---

## Continuación exacta -- 88 rondas, 26 de octubre de 2026

**Estado verificado al cerrar esta sesión:**

```
ruff check .            All checks passed
uv run pytest -q        1.775 pasan · 0 fallan
catalogo real           20261007-103000 · publicado_en 2026-10-07T10:30:00   (intacto)
cola de fichas          72.319 pendientes · 7.593 correctas   (era 79.887)
arbol                   solo los 3 ficheros ajenos
```

**Los seis primeros paquetes, cerrados.** *Y los tres defectos reales de la fase, los tres con el mismo
recorrido: medir → localizar → especificar → arreglar → probar.*

| # | defecto | estado |
|---|---|---|
| 1 | **`alerta` ligada al ordinal** (`grupo_id bigint NOT NULL`, sin identidad estable) | **arreglado**: migración 016 (`ean`), `almacen.py:959`, `alertas._grupo_de_hoy`, 6 pruebas |
| 2 | **la cola contaba como pendiente lo ya hecho** (7.565 fichas) | **arreglado**: reconciliador + **el ciclo lo corre** tras el pipeline, 11+4 pruebas, **colar real corregida 79.887 → 72.322** |
| 3 | **dos vías de ficha que no se hablaban** | **el mismo que el 2**, visto desde el otro lado |

### La siguiente acción, con el punto exacto

**F07, la concurrencia de la cantidad.** *Medido (§2 de `docs/investigaciones/F07-compra-familiar.md`):*

- **el tachado cumple el criterio** -- `LEAST`+`COALESCE` sobre la hora **del móvil**: *gana el primero y el
  otro ve lo que quería ver*
- **la cantidad no**: `cantidad = %s` **«gana el último, a propósito»**, y `momento` **no se usa**

**Falta un ensayo, y su diseño está claro:** *dos sesiones con la misma línea, cantidad cambiada a horas de
móvil distintas y **en los dos órdenes de llegada***; ver quién gana. **El patrón de conexión y lista está en
`tests/test_lineas_api.py` (`monkeypatch.setattr(almacen, "cambia_linea", ...)`).**

*Y decide si es defecto o decisión:* **si la cantidad vieja gana sobre la nueva, es defecto**; *si gana la
última llegada aunque su hora sea anterior, es una decisión que hay que escribir en el criterio.*

**Después, por este orden:** *la lista por pasillos (`¿hay `categoria` en las líneas?`), C01–C05 con
Bring!/AnyList/Listonic, los pasos de la tarea con una mano, y el recorrido de cuenta vacía.*

### Lo que me llevo, y conviene que no se pierda

*En 88 rondas "descubrí" ocho veces cosas que ya estaban escritas en el código -- la última, `kcal_100g`, una
columna **que la aplicación enseña** y que no había mirado en 82 rondas. Y más de la mitad de los fallos de
**mis propias pruebas** fueron **el instrumento midiendo algo distinto de lo que yo creía**: precios leídos del
`body` entero, la caché del cliente, 3 s fijos de espera, una lista vacía contando como distinta, una ventana
de 1.600 caracteres que cortaba antes del `except`.*

**Lo que corrigió cada uno fue leer el mensaje del servidor, pedir el esquema al proyecto, o mirar la
estructura -- nunca suponer.** *Es la regla que ha funcionado en esta fase, y la dejo escrita.*

---

## Lo que espera una decision tuya -- tres cosas, y las tres bloquean un arreglo

*Todo lo demas que se ha medido esta **cerrado, hecho, o fijado con su prueba**. Estas tres **no** son
mediciones que falten: son **decisiones que nadie puede tomar por ti**, y por eso estan aqui y no en un
informe.*

### 1. ¿Qué es «presupuesto»? -- de `C09`, F08

**El criterio pide** *(SUPERAPP-COMPETENCIA-Y-REA.md:97)*: *«**Previsto contra guardado/pagado sin mezclar**;
cobertura de lineas desconocidas.»*

**Hoy hay tres numeros posibles y solo dos existen:**

| pieza | **estado** |
|---|---|
| **lo que va a costar la lista ahora** (*estimacion*) | **hecho y en pantalla** (`cesta.coste_por_linea`) |
| **lo que se pago** | **hecho** (`compra.total_cent`) |
| **lo que la persona se propone gastar** | **NO EXISTE** |

**Y la palabra «presupuesto» en el proyecto es de colector** -- *presupuesto de tiempo y de peticiones* --, **no
de dinero**. *Asi que hay que decidir **cual de las tres** es la que el criterio llama «previsto»* -- *y si es
la tercera, **hay que construirla**.*

### 2. ¿Cuánto cuesta ir a una tienda? -- de `C07`, F08

**El criterio pide**: *«Maximo de tiendas y **coste de desplazamiento optativo**; ahorro neto definido».*

**El maximo de tiendas esta** (`CESTA_MAX_TIENDAS`, por defecto 2, y lo usan el optimizador **y** el oraculo), y
**el ahorro neto esta definido** (*«si gana a ir a una sola»*). **Lo que no existe es el coste de ir.**

**Y no puede venir de los datos**: *depende de donde vivas, de si vas andando o en coche, y de si de todas
formas pasabas por alli.* **El criterio dice «optativo» precisamente por eso** -- *pero hay que decidir **como
se pide**: un numero fijo, un coste por tienda, o nada.*

### 3. ¿La línea de la compra se guarda en la unidad que vino, o en la canónica? -- de F10

**El defecto esta medido**: *`previa_compra._unidad_canon` no usa `normalize._UNIDADES`, asi que `1 kg` + `500 g`
**no se suman**, y la aceptacion de F10 dice «mezcla **kg/g compatible** y ud **incompatible**».*

**El arreglo se probo, y funciona** -- *da `1,5 kg`, y deja `kg/ud` y `ml/g` separados, que es lo correcto.*
**Pero cambia lo que se ensena**: *`test_g12_previa.py` espera `500` (en g) y el arreglo da `0,5` (en kg).*

| guardar en... | a favor | en contra |
|---|---|---|
| **la unidad que vino** | *«500 g» es como se dice en una cocina* | *hay que convertir para comparar, en cada consolidacion* |
| **la canonica** | *una sola forma, y sumar es directo* | *«0,5 kg de harina» es como se dice en un almacen, **no en una receta*** |

**Son dos funciones de `core/previa_compra.py`**, y estan escritas y probadas: *lo unico que falta es **cual de
las dos**.*

---

### Y las tres, en una linea cada una

1. **«Presupuesto»**: *¿la estimacion de la lista, lo pagado, o un numero que se ponga la persona?*
2. **«Coste de desplazamiento»**: *¿se pide, y como -- fijo, por tienda, o no se pide?*
3. **«Unidad de la linea de compra»**: *¿la que vino, o la canonica?*

**Ninguna de las tres es un descuido del proyecto, y ninguna se puede contestar mirando el codigo** -- *las tres
son «que quiere la persona que usa esto», y eso se pregunta.*
