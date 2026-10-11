# Cesta fase 2: tablero operativo

Contrato: [empezar aquí](SUPERAPP-FASE2-EMPEZAR-AQUI.md). Investigación: [competencia y REA](SUPERAPP-COMPETENCIA-Y-REA.md).

Fecha inicial: 11 de octubre de 2026. Base inspeccionada `480ac21`. La revisión no reejecutó tests de Cesta; el laboratorio REA pasó 6/6 básicos, sin nativo. No trasladar esos resultados a la aceptación de Cesta.

## Siguiente acción

**F06 · el oráculo exhaustivo de asignaciones.** Es lo que el hallazgo pide y lo único que convierte
«discrepancias cero» en una afirmación con contenido. *Y ya hay un defecto real detrás.*

**El reparto se decidía con costes sin agrupar**, y estaba en cinco líneas de cableado de
`donde_comprar`:

```
por_cadena[fuente] = [...resolver...]              # SIN agrupar
resueltas = _agrupa_y_reparte([...])               # agrupadas, variable LOCAL
repartido = _mejor_reparto(..., por_cadena, ...)   # recibe las SIN agrupar
```

*`una_tienda` se calculaba agrupado y el reparto comparaba por línea: dos números distintos para la
misma compra.* **Medido**: dos líneas del mismo producto con 3×2 en alcampo y una tercera en día daban
**4,50 €** cuando cuestan **3,50**, con **`ahorro_cent = -50`** y `merece_la_pena = False` — **se le
decía a quien compra que no partiera la lista, cuando partirla ahorraba 0,50 €.** Arreglado, y la
reproducción fue la prueba: `F.` antes, `..` después.

**Lo que falta de F06**: el **oráculo exhaustivo** (enumerar asignaciones, calcular cada conjunto
realmente asignado, exigir discrepancias cero); **publicar la garantía y el límite** de `_mejor_reparto`
—*hoy no está escrito qué promete*—; decidir y decir **el alcance del umbral**; y el banco de matching.
Detalle: [`investigaciones/F06-reparto-agrupado.md`](investigaciones/F06-reparto-agrupado.md).

**Lo que queda de F01**, enumerado y no cerrado: navegador; estabilidad ante reordenación (V1/V2/V3
sobre lista y favorito, «jamás B por ordinal»); elegir comprar A otra vez como acción explícita; y
migrar los consumidores que aún lean el ordinal.
**Y de F02**: las unidades (g/ml/raciones) y la vista previa congelada.

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
| F06 | Matching y oráculo multi-tienda | **en curso** | Defecto del reparto **reproducido y arreglado**: comparaba con costes **sin agrupar** y descartaba el reparto que ahorra (`ahorro_cent = -50`). Falta el **oráculo exhaustivo**, publicar garantía/límite y el banco de matching. |
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
- Fichero / función / recorrido: `plataforma/api/cesta.py:donde_comprar` — *las elecciones agrupadas
  vuelven a `por_cadena`, que es lo que compara `_mejor_reparto`*. **El defecto no estaba en
  `_mejor_reparto`**, que recibe sus estructuras y está bien: estaba en quien se las daba.
- Evidencia obtenida y comando/fecha: `uv run pytest -q tests/test_fase2_f06_reparto_agrupado.py` →
  **2 pasan**; *antes del arreglo esa misma prueba daba `F.`, con `total_cent = 450` (son 350),
  `ahorro_cent = -50` y `merece_la_pena = False`* (13 oct 2026). Y `uv run pytest -q` → **1682 pasan,
  0 fallan**; `ruff` limpio.
- Caso que falla o comprobación siguiente: **el oráculo exhaustivo de asignaciones**, sin hacer.
  **Límite que queda, y hay que publicarlo**: la parte que se atribuye a cada línea se calcula
  suponiendo que **todas** las líneas van a esa tienda, así que una asignación que deje sólo una parte
  del grupo en la tienda sigue valorándose sobre un conjunto que no se compra allí.
- Cambios conservados / commit: `plataforma/api/cesta.py`, `tests/test_fase2_f06_reparto_agrupado.py`
  (nuevo), `docs/investigaciones/F06-reparto-agrupado.md` (nuevo) y este tablero.
- Bloqueo real y alternativa independiente: **ninguno**. *Límite declarado, además del de arriba:* el
  **alcance del umbral** («5 € dto comprando 20 €») no está decidido ni publicado — medido: dos líneas
  distintas de 12 € dan **2400** en el motor y **1900** si el umbral fuera del ticket entero. *No se
  llama defecto: se llama límite sin publicar.*
- **Acción inmediata al retomar:** construir el **oráculo exhaustivo de asignaciones** —enumerar todas,
  calcular cada conjunto realmente asignado, aplicar la promoción a ese conjunto y exigir
  **discrepancias cero** contra `donde_comprar`—, y **publicar la garantía y el límite** del algoritmo.

Mantener este tablero breve. Informes detallados por capacidad en `docs/investigaciones/` (crear al iniciar una investigación), con enlaces a evidencia del laboratorio cuando corresponda. Investigación entregada y función verificada son estados diferentes. No añadir otra bitácora de cientos de rondas aquí.
