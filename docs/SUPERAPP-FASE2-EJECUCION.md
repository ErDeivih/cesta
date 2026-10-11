# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Estado de la fase

**Matriz de capacidades y veredicto honesto**: [`SUPERAPP-FASE2-MATRIZ.md`](SUPERAPP-FASE2-MATRIZ.md).
*Que se puede hacer hoy, que no, con que se comprueba y en que orden sigue.*

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
| F03 | Publicación y uso concurrente | **en curso** | Publicación al final del ciclo, fallo en el veredicto, **resumen con las cuatro patas** —capturado/procesado/publicado/**reanudable sin red**—, fallos inyectados, **la API lee la versión publicada** (probado) y **una conexión ve una sola versión**. Falta los dos recorridos de navegador. |
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
