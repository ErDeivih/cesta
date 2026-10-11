# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F06 · arreglar las 9 discrepancias del reparto.** El **oráculo exhaustivo ya existe**
(`core/oraculo_reparto.py`, sin importar nada de `cesta.py`) y **su barrido ha encontrado el defecto que
F06 describía**: *9 de 176 escenarios (5%) donde el motor propone pagar más de lo que hay.*

```
linea l1: p2, 2u | l2: p1, 3u | l3: p1, 1u
alcampo  l1 80 3x2  l2 120 3x2  l3 120 3x2
aldi     l1 50 -25% l2 100 sin  l3 100 sin
dia      l1 70 sin  (l2 y l3 no estan)

motor    l1->aldi, l2->alcampo, l3->alcampo : 75 + (270+90) = 435
oraculo  l1->aldi, l2->alcampo, l3->aldi    : 75 +  240 + 100 = 415
```

**El motor manda `l3` a alcampo porque su parte del 3×2 allí es 90** (frente a 100 en aldi) — *pero esa
parte sale de un grupo de **cuatro** unidades que **sólo se forma si `l3` se queda**: fuera, alcampo son
240 y aldi 100.* **Es la frase de F06 al pie de la letra**: *«no elegir partes de un descuento calculado
sobre una cesta que al final no se compra en esa tienda»* — la parte que decide sólo existe si la
decisión ya está tomada. *Circular.*

**Fijado con `xfail(strict=True)`**: la prueba afirma el criterio (discrepancias cero), hoy falla, y el
`strict` obligará a quitar la marca al arreglarlo. **No se rebaja el criterio.**

**Lo que falta**: arreglarlo —*enumerar asignaciones en cestas pequeñas, y llamar heurística a la
heurística en las grandes*—, **publicar la garantía y el límite** del algoritmo, decidir **el alcance del
umbral**, y el banco de matching.
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
| F06 | Matching y oráculo multi-tienda | **en curso** | Oráculo exhaustivo **construido** (`core/oraculo_reparto.py`) y **ha encontrado 9 discrepancias en 176 escenarios** (5%): el motor reparte con una «parte» que sólo existe si la línea se queda. Fijado con `xfail(strict)`. Falta el arreglo, publicar garantía/límite y el banco de matching. |
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
- Fichero / función / recorrido: `core/oraculo_reparto.py` (nuevo) — *no importa nada de `cesta.py`: ni
  el optimizador, ni la aritmética de promociones, ni la agrupación; la mecánica entra ya leída*.
  Comparado contra `plataforma/api/cesta.py:donde_comprar`.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f06_oraculo_asignaciones.py`
  → **7 pasan, 1 xfailed** (13 oct 2026). *El barrido de 200 escenarios con semilla fija da **9
  discrepancias en 176**, todas con el motor más caro que el óptimo.* Y `uv run pytest -q` → **1689
  pasan, 1 xfailed, 0 fallan**; `ruff` limpio.
- Caso que falla o comprobación siguiente: **las 9 discrepancias, sin arreglar.** *Caso mínimo medido*:
  `l1(p2,2u)`→aldi, `l2(p1,3u)` y `l3(p1,1u)` en alcampo a 1,20 con 3×2 → el motor propone **435** y el
  óptimo es **415**, porque la parte de `l3` en alcampo (90) sale de un grupo de 4 unidades que sólo se
  forma si `l3` se queda.
- Cambios conservados / commit: `core/oraculo_reparto.py`, `tests/test_fase2_f06_oraculo_asignaciones.py`
  (nuevos), `docs/investigaciones/F06-reparto-agrupado.md` y este tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límites declarados:* el oráculo **excluye
  `umbral`** a propósito (su alcance no está decidido); el precio y la oferta del barrido van **por
  tienda y producto**, no por línea; y el barrido cubre cestas de **2–3 líneas y 2–3 tiendas**, que es
  lo que F06 llama «cestas pequeñas».
- **Acción inmediata al retomar:** **arreglar las 9 discrepancias** —enumerar asignaciones y re-puntuar
  cada una con su conjunto real en cestas pequeñas, y llamar heurística a la heurística en las grandes—,
  y **publicar la garantía y el límite** de `_mejor_reparto`.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
