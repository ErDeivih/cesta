# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F02 · la concurrencia y las unidades**, ya que el reintento está **verificado en la UX**. El ensayo de
navegador (`plataforma/prueba_reintento.py`) **reproduce el defecto y confirma el arreglo**:

    con la regla anterior   claves DISTINTAS · el dia 1 -> 3   (dos entradas de mas)
    con el arreglo          la MISMA clave   · el dia 1 -> 1

*Y se comprobó discriminante simulando la regla vieja.* **Lo que queda de F02**: dos solicitudes
simultáneas con la misma clave y rollback limpio; la política de «misma clave con payload distinto»;
**cantidad, unidad y base** (g, ml, raciones con conversiones trazables, y consumir parte del envase);
y la **vista previa congelada** a compra/líneas y receta/versiones.

Detalle: [`investigaciones/F02-reintentos-del-diario.md`](investigaciones/F02-reintentos-del-diario.md).

**Recursos que quedan levantados para los siguientes ensayos**: API en el **8099** (catálogo de ensayo)
y **Vite en el 5173** con `CESTA_API` apuntando ahí — *los necesita también el recorrido de navegador que
le falta a F01.*

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
| F02 | Reintentos/unidades/privacidad del diario | **en curso** | Reintento **verificado en la UX**: `plataforma/prueba_reintento.py` reproduce el defecto (el día **1→3**) y confirma el arreglo (**1→1**, misma clave). Falta concurrencia, unidades y vista previa. |
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
  **F01 en curso** (motor, cierre y HTTP hechos; cuatro cosas enumeradas); **F02 en curso** con el
  reintento **verificado en la UX** y pendientes concurrencia, unidades y vista previa.
- Fichero / función / recorrido: `plataforma/prueba_reintento.py` (nuevo) — *intercepta la respuesta del
  alta con `route.fetch()` + `route.abort()` y cuenta las entradas del día por la API*.
- Evidencia obtenida y comando/fecha: `CESTA_UI=http://localhost:5173 uv run python -m
  plataforma.prueba_reintento` → **10 comprobaciones, todas ok** (13 oct 2026). *Discriminante
  comprobado*: simulando `resolver(null, …)` el ensayo falla con «el día **1 → 3**». Y las puertas:
  `npm test` → **42 pasan**; `tsc` → 0; **`npm run build` → ✓ 154 módulos**; `ruff` limpio; `uv run
  pytest -q` → **1674 pasan, 0 fallan**.
- Caso que falla o comprobación siguiente: **la concurrencia** (dos solicitudes simultáneas con la misma
  clave) y las unidades (g/ml/raciones), sin hacer.
- Cambios conservados / commit: `plataforma/prueba_reintento.py`, `docs/investigaciones/F02-…` y este
  tablero (el arreglo del cliente y el módulo van en `69f7dbe`).
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* el ensayo usa la **cuenta
  de prueba** y la base desechable; **no toca el diario de casa**.
- **Acción inmediata al retomar:** montar la concurrencia de F02 —dos solicitudes simultáneas con la
  misma clave, y que quede una entrada con rollback limpio—; después las unidades y la vista previa, y
  el recorrido de navegador que le falta a F01.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
