# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F02 · las unidades y la vista previa.** El reintento está **verificado en la UX** y **la carrera
arreglada**. El encargo ya había señalado el punto —*«clave de diario escrita tras el INSERT»*— y era
exactamente eso: el `SELECT`, el `INSERT` **sin la clave** y un `UPDATE` **después**. *Con dos envíos a
la vez los dos `SELECT` no veían nada, los dos insertaban, y el índice único **rechazaba al segundo**:
no deduplicaba, **fallaba** — y la fila del que fallaba se quedaba sin clave.*

```
ANTES   F..  IntegrityError: UNIQUE constraint failed: entrada.propietario, entrada.clave_operacion
DESPUES ...  pasa
```

*La reproducción fue la prueba de que discrimina: falló antes y pasa después.* **Y la clave va ahora
dentro del `INSERT`** (`ON CONFLICT … WHERE clave_operacion IS NOT NULL DO NOTHING`), con el que no
inserta devolviendo la fila del otro.

**Lo que queda de F02**: **cantidad, unidad y base** (g, ml, raciones con conversiones trazables, y
consumir parte del envase en vez de la compra entera) y la **vista previa congelada** a compra/líneas y
receta/versiones.

Detalle: [`investigaciones/F02-reintentos-del-diario.md`](investigaciones/F02-reintentos-del-diario.md).

**Recursos que quedan levantados**: API en el **8099** y **Vite en el 5173** — *los necesita el
recorrido de navegador que le falta a F01.*

**Lo que queda de F01**, enumerado y no cerrado: navegador; estabilidad ante reordenación (V1/V2/V3
sobre lista y favorito, «jamás B por ordinal»); elegir comprar A otra vez como acción explícita; y
migrar los consumidores que aún lean el ordinal.

No reiniciar el contador ni volver a implementar los campos del diario: existen. Preservar `core/datos/secciones.yml` y `docs/CIFRAS.md`, sin incluirlos en commits. No modificar el estado de investigaciones de RadioPV/CueDigital.

## Estado de paquetes

Estados: pendiente / en curso / implementado sin ensayo / verificado / limitado por fuente / bloqueado / descartado con motivo. Verificado exige todo el criterio, no lectura o build.

| ID | Entregable | Estado | Evidencia / siguiente acción |
|---|---|---|---|
| F00 | Reconciliar aceptación y baseline | **en curso** | Baseline **1.670 pasan, 0 saltan, 0 fallan** (155 s, con `CESTA_POSTGRES` al 5434). Encabezado del tablero G01–G14 reconciliado. Hallazgo 4 **reproducido**. Faltan los otros 8 hallazgos y la matriz S00–S12. |
| F01 | Identidad estable y producto efectivo comprado | **en curso** | Motor, cierre y **HTTP verificado** (la prueba **discrimina**: simulando lo anterior falla). Migración **015**. Falta navegador, estabilidad ante reordenación y migrar consumidores del ordinal. |
| F02 | Reintentos/unidades/privacidad del diario | **en curso** | Reintento **verificado en la UX** (`prueba_reintento.py`: el día 1→3 sin arreglo, 1→1 con él) y **carrera arreglada** (la clave va en el `INSERT`; antes `IntegrityError`). Falta unidades y vista previa. |
| F03 | Publicación y uso concurrente | pendiente | Pipeline→matching→puntero; tres recorridos V1/V2. |
| F04 | Privacidad/CSRF/restauración | pendiente | HTTP A/B, origen ajeno y copia aislada. |
| F05 | Fichas de seis cadenas/Lidl | pendiente | Inventario real por campo y workers ejecutados. |
| F06 | Matching y oráculo multi-tienda | pendiente | Evaluación independiente y asignaciones completas. |
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

- Paquete y criterio concreto: **F00 en curso** (los otros ocho hallazgos y la matriz S00–S12);
  **F01 en curso** (motor, cierre y HTTP hechos; cuatro cosas enumeradas); **F02 en curso** con reintento
  y carrera hechos, y pendientes unidades y vista previa.
- Fichero / función / recorrido: `core/diario.py:apunta` — *la clave va **dentro** del `INSERT` con
  `ON CONFLICT … WHERE clave_operacion IS NOT NULL DO NOTHING`; antes era un `UPDATE` **después** del
  `INSERT`*. Y `_respuesta_del_reintento`, que **dice el conflicto** en vez de devolver la entrada
  vieja en silencio.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f02_concurrencia.py` →
  **5 pasan**; *antes del arreglo esa misma prueba daba `F..` con
  `IntegrityError: UNIQUE constraint failed`* (13 oct 2026). Y `tests/test_g01_diario_http.py` →
  **16 pasan**, con el choque de clave devolviendo **400 con el motivo**.
- Caso que falla o comprobación siguiente: **las unidades** (g/ml/raciones) y la vista previa congelada,
  sin hacer.
- Cambios conservados / commit: `core/diario.py`, `tests/test_fase2_f02_concurrencia.py` (nuevo),
  `tests/test_g01_diario_http.py`, el informe de F02 y este tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* la carrera se prueba con
  dos conexiones y una barrera contra el **mismo fichero SQLite**; *no* se ha probado con la API
  levantada y dos peticiones HTTP a la vez — eso queda para el ensayo de navegador si hiciera falta.
- **Acción inmediata al retomar:** las **unidades** de F02 —g, ml y raciones con conversiones trazables,
  y consumir parte del envase en vez de la compra entera—, que es lo que queda del paquete después del
  reintento y la carrera.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
