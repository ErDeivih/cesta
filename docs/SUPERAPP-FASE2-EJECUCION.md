# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F01 · arreglar el producto efectivo del cierre.** El hallazgo **ya no es una lectura: está
reproducido con números.** Con A pedido y B aceptado —3 unidades, 3×2 de B— la **estimación** cobra B a
**500 c** y el **cierre** guarda A a **900 c**: 400 céntimos, y el histórico apunta a un producto que
nadie compró. **Está en dos sitios independientes** —`almacen.cierra_compra:563` no lee `autorizado*`, y
`cesta.coste_por_linea:871` descarta las alternativas—, así que arreglar uno solo no arregla nada.

Detalle y plan: [`investigaciones/F01-producto-efectivo.md`](investigaciones/F01-producto-efectivo.md).
Prueba que lo fija: `tests/test_fase2_f01_sustitucion.py` (**`xfail(strict)`**: pasará al arreglarlo y
entonces **obligará a quitar la marca**).

No reiniciar el contador ni volver a implementar los campos del diario: existen. Preservar `core/datos/secciones.yml` y `docs/CIFRAS.md`, sin incluirlos en commits. No modificar el estado de investigaciones de RadioPV/CueDigital.

## Estado de paquetes

Estados: pendiente / en curso / implementado sin ensayo / verificado / limitado por fuente / bloqueado / descartado con motivo. Verificado exige todo el criterio, no lectura o build.

| ID | Entregable | Estado | Evidencia / siguiente acción |
|---|---|---|---|
| F00 | Reconciliar aceptación y baseline | **en curso** | Baseline **1.670 pasan, 0 saltan, 0 fallan** (155 s, con `CESTA_POSTGRES` al 5434). Encabezado del tablero G01–G14 reconciliado. Hallazgo 4 **reproducido**. Faltan los otros 8 hallazgos y la matriz S00–S12. |
| F01 | Identidad estable y producto efectivo comprado | **defecto reproducido** | `tests/test_fase2_f01_sustitucion.py`: estimación 500 c / cierre 900 c. Dos causas independientes. |
| F02 | Reintentos/unidades/privacidad del diario | pendiente | Respuesta perdida→segundo submit; simultaneidad. |
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

- Paquete y criterio concreto: **F00 en curso** (baseline, reconciliación del tablero anterior) y **F01
  abierto** con su defecto reproducido.
- Fichero / función / recorrido: `plataforma/api/almacen.py:563` (`cierra_compra`, SELECT sin
  `autorizado*`) y `plataforma/api/cesta.py:871` (`coste_por_linea`, filtro `!= "alternativa"`).
- Evidencia obtenida y comando/fecha: `uv run pytest -q` → **1.670 pasan, 0 saltan** (13 oct 2026, base
  desechable 5434); `uv run pytest -q tests/test_fase2_f01_sustitucion.py` → **2 pasan, 1 xfail(strict)**;
  la prueba compara estimación (B, 500 c) y cierre (A, 900 c).
- Caso que falla o comprobación siguiente: la prueba marcada `xfail(strict)` **falla a propósito**: el
  cierre cobra el producto pedido, no el aceptado.
- Cambios conservados / commit: `tests/test_fase2_f01_sustitucion.py`,
  `docs/investigaciones/F01-producto-efectivo.md`, encabezado de `SUPERAPP-EJECUCION.md` reconciliado,
  este tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* la reproducción cubre el
  motor con catálogo en memoria; **no** cubre HTTP ni PostgreSQL, y eso lo cierra F01.
- **Acción inmediata al retomar:** pasar `autorizado*` al `SELECT` de `cierra_compra`, honrar la
  confirmación en `coste_por_linea` y guardar **B** como `producto_id` de la compra (conservando A como
  lo pedido); después quitar el `xfail` y añadir el recorrido HTTP.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
