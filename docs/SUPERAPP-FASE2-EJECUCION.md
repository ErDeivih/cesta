# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F02 · el ensayo de navegador del reintento.** El núcleo está hecho y probado en el cliente: *la clave
la decide ahora la operación pendiente, así que reintentar lo mismo **reutiliza la clave** y el servidor
devuelve la entrada que ya creó.* **Y el defecto estaba peor de lo que decía el hallazgo**:
`clave_operacion` **no impedía nada en la UX real** — el doble clic en vuelo lo bloquea
`disabled={isPending}`, no la clave, y **no hay reintento automático** en ninguna mutación, así que la
premisa del comentario no ocurría nunca.

**Lo que falta es la prueba que el encargo reclama con esas palabras**: *«la prueba de mismo UUID por
HTTP no cubre la UX»*. **Ensayo de navegador: servidor que guarda y respuesta que se pierde, seguido de
pulsar otra vez, y contar entradas.**

Y en la misma línea apareció un **segundo defecto ya arreglado**: `crypto.randomUUID` no existe en
contexto no seguro, y el diario lo llamaba a pelo — *por la IP de Tailscale, en http, «Anotar»
reventaba.*

Detalle: [`investigaciones/F02-reintentos-del-diario.md`](investigaciones/F02-reintentos-del-diario.md).

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
| F02 | Reintentos/unidades/privacidad del diario | **en curso** | Núcleo del reintento hecho: `logica/operacionPendiente.ts` + `Diario.tsx`; **42 tests de cliente**, guarda **comprobada discriminante**. *Arreglado de paso: `crypto.randomUUID` sin respaldo rompía el formulario por la IP.* Falta navegador, concurrencia y unidades. |
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
  **F01 en curso** (motor, cierre y HTTP hechos; cuatro cosas enumeradas); **F02 en curso** con el núcleo
  del reintento hecho y su ensayo de navegador pendiente.
- Fichero / función / recorrido: `plataforma/web/app/src/logica/operacionPendiente.ts` (nuevo) y
  `src/paginas/Diario.tsx` (`Alta`) — *la clave la decide `resolver`, no el `onSubmit`*. Lo que falta:
  el ensayo de navegador con respuesta perdida.
- Evidencia obtenida y comando/fecha: `npm test` (cliente) → **42 tests, 42 pasan**; `npx tsc --noEmit`
  → 0; `uv run pytest -q` → **1674 pasan, 0 fallan**; `uv run ruff check .` → limpio (13 oct 2026). *La
  guarda se comprobó **discriminante**: reintroduciendo el defecto en el código, falla.*
- Caso que falla o comprobación siguiente: **el ensayo de navegador del reintento**, sin hacer.
- Cambios conservados / commit: `logica/operacionPendiente.ts`, `Diario.tsx`, `tests/cocina.test.mjs`,
  `package.json` (**`npm test`**, que recoge todos los tests del cliente), el informe de F02 y este
  tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* está probado el módulo y el
  cableado, **no la UX**; y de F02 quedan sin hacer la concurrencia, la política de «misma clave con otro
  payload», las unidades (g/ml/raciones) y la vista previa congelada.
- **Acción inmediata al retomar:** montar el ensayo de navegador del reintento —servidor que guarda y
  respuesta que se pierde, segundo envío, y contar entradas—, que es el criterio que el encargo reclama
  para F02; después la concurrencia y las unidades.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
