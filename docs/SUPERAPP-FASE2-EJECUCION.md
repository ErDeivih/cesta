# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F06 · publicar la garantía y el límite, y el banco de matching.** **Las 9 discrepancias están
arregladas**, y el arreglo es el que pedía el criterio: *cada asignación se puntúa con **su** conjunto.*

```
antes    _mejor_reparto repartia con la «parte» de cada linea suponiendo que TODAS iban a esa tienda
ahora    por_cadena se queda SIN agrupar, y el reparto agrupa lo que de verdad va a cada tienda

         por debajo de 200.000 asignaciones -> producto cartesiano -> el OPTIMO, exhaustivo = True
         por encima                         -> la heuristica         -> exhaustivo = False, y lo dice
```

**El barrido pasa de 9 discrepancias a cero**, y el `xfail(strict)` **saltó como `XPASS` al arreglarlo**
—*que era exactamente para lo que estaba*—. **Los 41 tests de reparto que ya existían siguen pasando.**

**Lo que queda de F06**: publicar la garantía y el límite **donde se lee el algoritmo** (hoy están en el
código y en el informe); **decidir el alcance del `umbral`** —*«5 € dto comprando 20 €»: 2400 con la
lectura del motor y 1900 con la del ticket, y el folleto no lo dice*—; y el **banco de matching**
(positivos/negativos duros, precisión/recall/abstención con denominadores), **sin empezar**.
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
| F03 | Publicación y uso concurrente | pendiente | Pipeline→matching→puntero; tres recorridos V1/V2. |
| F04 | Privacidad/CSRF/restauración | pendiente | HTTP A/B, origen ajeno y copia aislada. |
| F05 | Fichas de seis cadenas/Lidl | pendiente | Inventario real por campo y workers ejecutados. |
| F06 | Matching y oráculo multi-tienda | **en curso** | **9 discrepancias arregladas**: el reparto puntúa cada asignación con **su** conjunto y **enumera cuando cabe** (200.000), diciendo `exhaustivo`. El `xfail(strict)` saltó como `XPASS`. Falta publicar garantía/límite, el alcance del `umbral` y el banco de matching. |
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
- Fichero / función / recorrido: `plataforma/api/cesta.py:_mejor_reparto` — *recibe las elecciones **sin
  agrupar** y agrupa lo que de verdad va a cada tienda (`_coste_con_lo_agrupado`); enumera el producto
  cartesiano por debajo de `_LIMITE_EXHAUSTIVO = 200_000` y si no usa la heurística, **diciéndolo con
  `exhaustivo`***. Y el write-back de la ronda anterior **se quitó**: era un arreglo a medias.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f06_oraculo_asignaciones.py` →
  **10 pasan** (13 oct 2026), incluido el barrido de 200 escenarios con **cero discrepancias**. *El
  `xfail(strict=True)` que fijaba las 9 saltó como **`XPASS`**, que es lo que obliga a quitar la marca.*
  Y `uv run pytest -q` → **1692 pasan, 0 fallan**; `ruff` limpio; los 41 tests de reparto que ya
  existían siguen pasando.
- Caso que falla o comprobación siguiente: **ninguno abierto en el reparto**. Lo que queda es
  *publicar* la garantía y el límite donde se lee el algoritmo, y decidir el alcance del `umbral`.
- Cambios conservados / commit: `plataforma/api/cesta.py`,
  `tests/test_fase2_f06_oraculo_asignaciones.py`, `docs/investigaciones/F06-reparto-agrupado.md` y este
  tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límites declarados:* por encima de 200.000
  asignaciones **no se promete el óptimo** y la respuesta lo dice; el `umbral` sigue fuera del oráculo
  hasta que se decida su alcance; y el límite exhaustivo es un número de **asignaciones, no de tiempo**
  —*si alguna vez se mide que 200.000 tardan demasiado, el número tendrá que bajar y habrá que decirlo*.
- **Acción inmediata al retomar:** **publicar la garantía y el límite** de `_mejor_reparto` donde se lee
  el algoritmo, **decidir el alcance del `umbral`** con su prueba, y empezar el **banco de matching**
  (positivos/negativos duros por familia/cadena, precisión/recall/abstención **con denominadores**).

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
