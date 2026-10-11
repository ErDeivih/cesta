# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F01 · el recorrido HTTP con una sustitución distinguible.** El motor y el cierre **ya están
arreglados y probados**: con A pedido y B aceptado —3 unidades, 3×2— la estimación y el cierre dan
**B, alcampo, 3 y 500 céntimos**; antes el cierre guardaba **A a 900**. *Lo que falta es el ensayo
servido*, y **el fixture que había no puede hacerlo**: medido el 13 de octubre de 2026, en `alcampo`
hay **un solo candidato** para el grupo 6803 y ocupa **las dos casillas** —la principal y la de
alternativa—, así que aceptar y no aceptar archivan lo mismo.

Hace falta un caso donde **A y B difieran en precio o en oferta**, por HTTP y contra PostgreSQL.
Detalle: [`investigaciones/F01-producto-efectivo.md`](investigaciones/F01-producto-efectivo.md).

No reiniciar el contador ni volver a implementar los campos del diario: existen. Preservar `core/datos/secciones.yml` y `docs/CIFRAS.md`, sin incluirlos en commits. No modificar el estado de investigaciones de RadioPV/CueDigital.

## Estado de paquetes

Estados: pendiente / en curso / implementado sin ensayo / verificado / limitado por fuente / bloqueado / descartado con motivo. Verificado exige todo el criterio, no lectura o build.

| ID | Entregable | Estado | Evidencia / siguiente acción |
|---|---|---|---|
| F00 | Reconciliar aceptación y baseline | **en curso** | Baseline **1.670 pasan, 0 saltan, 0 fallan** (155 s, con `CESTA_POSTGRES` al 5434). Encabezado del tablero G01–G14 reconciliado. Hallazgo 4 **reproducido**. Faltan los otros 8 hallazgos y la matriz S00–S12. |
| F01 | Identidad estable y producto efectivo comprado | **en curso** | **Motor y cierre arreglados**: estimación y cierre dan B, alcampo, 3 y **500 c** (antes el cierre guardaba A a 900). Migración **015**. `test_g03_cierre.py` corregido con su límite medido. **Falta el HTTP distinguible.** |
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

- Paquete y criterio concreto: **F00 en curso** (los otros ocho hallazgos y la matriz S00–S12) y
  **F01 en curso** con motor y cierre ya arreglados; falta su ensayo HTTP.
- Fichero / función / recorrido: `plataforma/api/cesta.py:coste_por_linea` (honra la confirmación y
  devuelve `promo` y `producto_id`), `plataforma/api/almacen.py:cierra_compra` (guarda el efectivo en
  `producto_id` y el pedido en `producto_pedido_id`), `plataforma/sql/015_lo_pedido_y_lo_comprado.sql`.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f01_sustitucion.py` → **3
  pasan**; `uv run pytest -q` → **1673 pasan, 0 fallan** (13 oct 2026, base desechable 5434). La
  estimación y el cierre dan el mismo número; antes 500 contra 900.
- Caso que falla o comprobación siguiente: **la sustitución por HTTP**. *El fixture de
  `test_g03_cierre.py` no puede distinguirla*: en `alcampo` el grupo 6803 tiene **un solo candidato**
  que ocupa las dos casillas. Hace falta un caso con A y B distintos en precio u oferta.
- Cambios conservados / commit: `sql/015`, `cesta.py`, `almacen.py`, `tests/test_fase2_f01_sustitucion.py`,
  `tests/test_g03_cierre.py` (prueba sustituida con su límite medido y docstring corregido),
  `tests/test_cesta_api.py` (forma de retorno), `docs/investigaciones/F01-producto-efectivo.md`.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado:* el motor está probado con
  catálogo en memoria y el cierre contra PostgreSQL, pero **no hay un caso HTTP que discrimine la
  sustitución**; eso es implementación sin ensayo servido.
- **Acción inmediata al retomar:** buscar o fabricar un grupo donde la alternativa aceptada **difiera**
  del candidato principal en precio u oferta, y montar con él el recorrido HTTP completo —estimar,
  aceptar, cerrar, leer `compra_linea`— comprobando **B, tienda, cantidad e importe**; después, los
  otros ocho hallazgos de F00.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
