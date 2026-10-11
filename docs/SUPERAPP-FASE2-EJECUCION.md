# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F02 · los reintentos del diario.** El escenario del encargo: *«Simular servidor que guarda pero pierde
la respuesta; pulsar otra vez no duplica»*. **Hoy `Diario.tsx:Alta` genera un UUID en cada submit**, así
que un reintento manual tras una respuesta perdida **usa una clave nueva y el servidor no puede
deduplicar**. *La prueba de «mismo UUID por HTTP» que existe no cubre la UX.*

Antes de tocar nada: **reproducirlo**. *Servidor que registra y respuesta que se pierde, seguido de
pulsar otra vez.*

**Lo que queda de F01**, enumerado y no cerrado: el recorrido de **navegador**; la **estabilidad ante
reordenación** (V1/V2/V3 sobre lista y favorito, «jamás B por ordinal»); elegir comprar A otra vez como
acción explícita; y migrar los consumidores que aún lean el ordinal.
Detalle: [`investigaciones/F01-producto-efectivo.md`](investigaciones/F01-producto-efectivo.md).

No reiniciar el contador ni volver a implementar los campos del diario: existen. Preservar `core/datos/secciones.yml` y `docs/CIFRAS.md`, sin incluirlos en commits. No modificar el estado de investigaciones de RadioPV/CueDigital.

## Estado de paquetes

Estados: pendiente / en curso / implementado sin ensayo / verificado / limitado por fuente / bloqueado / descartado con motivo. Verificado exige todo el criterio, no lectura o build.

| ID | Entregable | Estado | Evidencia / siguiente acción |
|---|---|---|---|
| F00 | Reconciliar aceptación y baseline | **en curso** | Baseline **1.670 pasan, 0 saltan, 0 fallan** (155 s, con `CESTA_POSTGRES` al 5434). Encabezado del tablero G01–G14 reconciliado. Hallazgo 4 **reproducido**. Faltan los otros 8 hallazgos y la matriz S00–S12. |
| F01 | Identidad estable y producto efectivo comprado | **en curso** | Motor, cierre y **HTTP verificado** (la prueba **discrimina**: simulando lo anterior falla). Migración **015**. Falta navegador, estabilidad ante reordenación y migrar consumidores del ordinal. |
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

- Paquete y criterio concreto: **F00 en curso** (los otros ocho hallazgos y la matriz S00–S12);
  **F01 en curso** con motor, cierre y HTTP hechos, y cuatro cosas enumeradas por hacer; **F02
  abierto** con su reproducción pendiente.
- Fichero / función / recorrido: `plataforma/web/app/src/paginas/Diario.tsx` (`Alta`), que genera
  `crypto.randomUUID()` **en cada submit**; `core/diario.py:apunta`, que busca la clave, inserta,
  actualiza la clave y hace commit — *la clave se escribe después del INSERT*.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_g03_cierre.py` → **4 pasan** (13 oct
  2026, base desechable 5434), incluida
  `test_la_compra_archiva_el_producto_aceptado_cuando_la_linea_pide_otro`, **comprobada discriminante**
  simulando el comportamiento anterior. Y la medición del catálogo: **0** pares (grupo, tienda) con dos
  GTIN distintos, **38** con dos productos y un solo GTIN, **25.975** con alguna fila sin GTIN.
- Caso que falla o comprobación siguiente: **el reintento manual del diario**, aún sin reproducir.
- Cambios conservados / commit: `368225a` (F01: motor, cierre, migración 015 y pruebas) y el commit de
  esta ronda con la prueba HTTP.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* en el catálogo actual la
  alternativa es inexistente o el mismo producto —medido—, así que la prueba HTTP discrimina por
  **identidad** y no por precio; y el recorrido de navegador sigue sin hacerse.
- **Acción inmediata al retomar:** reproducir el reintento del diario —servidor que guarda y respuesta
  que se pierde, seguido de un segundo submit— antes de tocar `Diario.tsx`; después la estabilidad de
  identidad de F01 y los ocho hallazgos que quedan de F00.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
