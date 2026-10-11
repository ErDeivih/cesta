# SUPERAPP · Tablero de ejecución

Objetivo y paquetes: [`SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`](SUPERAPP-GOAL-CONTINUACION-2026-10-11.md).
Estado vivo y resumen vigente: [`SUPERAPP-ESTADO.md`](SUPERAPP-ESTADO.md).

Estados permitidos por paquete: `pendiente` · `en curso` · `implementado sin ensayo real` ·
`verificado` · `limitado por fuente` · `bloqueado`. **«Verificado» exige su criterio de aceptación
completo, no una compilación.**

## Tablero

| Paquete | Estado | Evidencia | Siguiente acción |
|---|---|---|---|
| G01 Diario efectivo | `en curso` | ver abajo | ofrecer cantidad y macros en `Diario.tsx:Alta` |
| G02 Texto libre | `pendiente` | — | línea sin producto, «Pendiente de identificar» |
| G03 Revocación exacta | `pendiente` | — | fixture de tres líneas, medir la pulsada |
| G04 Dos recorridos | `pendiente` | — | depende de G01–G03 |
| G05 Gráficas | `pendiente` | — | depende de G01 para nutrición |
| G06 Acabado de las tres apps | `pendiente` | — | puede avanzar por pantallas |
| G07 Publicación diaria | `pendiente` | — | auditar `publicacion.publicar()` dentro del pipeline |
| G08 Fichas completas | `pendiente` | — | inventario por cadena |
| G09 Lidl integrado | `pendiente` | — | `run.py:ORDEN` sin Lidl |
| G10 Identidad exacta | `pendiente` | — | banco estratificado |
| G11 Oráculo de coste | `pendiente` | — | enumeración exhaustiva independiente |
| G12 Recetas | `pendiente` | — | versiones y escalado por ración |
| G13 Operación y privacidad | `pendiente` | — | copia/restauración probada en destino |
| G14 Aprendizaje y aceptación | `pendiente` | — | cierre tras los demás |

## G01 — Diario: registrar, persistir y explicar lo conocido

**Estado: `en curso`.** Ficheros: `plataforma/web/app/src/paginas/Diario.tsx`,
`src/api/diario.ts`, `plataforma/api/diario.py`, `core/diario.py`, puente en `api/cesta.py` y
`plataforma/prueba_navegador.py`.

### Hecho, con evidencia

| Qué | Evidencia | Fecha |
|---|---|---|
| Aceptación del **almacén**: números exactos, cobertura 1/2 y 2/2, dos comidas iguales, cero publicado, negativos/NaN/infinito, comida inválida, y aislamiento A/B incluido el borrado cruzado | `tests/test_g01_diario_aceptacion.py` — **11 pasan** | 11 oct 2026 |
| El cliente **devuelve el recibo** del servidor (`{id, dia}` / `{entrada}`) en vez de `undefined`, y los tres tipos están declarados | `src/api/diario.ts` | 11 oct 2026 |
| **Las tendencias se invalidan**: `useApuntar`, `useApuntarDesdeFicha` y `useBorrarEntrada` invalidan `['diario']` **y** `['diario-rango']` | `src/api/diario.ts` | 11 oct 2026 |
| `npm run tipos` limpio tras el cambio | `npx tsc --noEmit` | 11 oct 2026 |

**Lo que ya existía y se conserva**: `tests/test_de_la_ficha_al_diario.py` (la cuenta de la ficha y
lo ausente-frente-a-cero) y `POST /api/diario/desde-ficha` con `gramos` + valores por 100 g, que
hace la cuenta **en el servidor**.

### Pendiente, y por qué

1. **`Diario.tsx:Alta` no ofrece cantidad ni macronutrientes**: manda `cantidad_g`, proteínas, grasas
   e hidratos como `null`. Es el hueco principal del paquete y el que el documento señala primero.
   *Acción: leer `Alta` entero (líneas 96-160) y añadir cantidad, unidad y los cuatro nutrientes con
   su fuente, distinguiendo por porción de por 100 g y sin multiplicar dos veces.*
2. **El puente compra→diario usa el número de la previa**, no el recibo: `Diario.tsx:62` hace
   `setAnotadas(previa?.anotarian.length ?? 0)`. *Acción: consumir `ReciboDeAlta`/lo que devuelva
   `anotarDeLaCompra`, y decir cuántas se anotaron de verdad.*
3. **Idempotencia por operación**: hoy no hay clave. *Acción: una clave por operación (doble clic,
   respuesta perdida, reintento) que no duplique, **sin** deduplicar por nombre+fecha+nutrientes —
   eso ya está probado que debe permitir dos comidas iguales.*
4. **Aislamiento por HTTP montado**: anónimo 401; B no enumera, lee, modifica ni borra entradas de A
   por ID o fecha; cambio A→B sin cachés ni borradores. *Acción: extender las pruebas de la API con
   `TestClient`, que es donde se prueba la ruta y no la función interna.*
5. **Navegador 390 y 1440**: alta efectiva, lectura, recarga, borrado y tendencias, guardando IDs y
   resultados. *Acción: sección nueva en `plataforma/prueba_navegador.py`, con la disciplina del
   fichero: esperar a que el dato esté, y anclarse en los textos de hoy.*

### Limitaciones registradas

- **La ingesta del 11 de octubre estaba en curso** durante esta ejecución (tarea `Cesta diaria`,
  arrancada 11:05, Carrefour 425/596 categorías, WAF y un HTTP 520). La versión publicada seguía
  siendo `20261010-142831`. **No se ha detenido ni alterado**, y ningún ensayo de este paquete
  depende de la versión del catálogo.
- Los ensayos de este paquete usan **base SQLite temporal** (`tmp_path`) y **la base desechable del
  5434**; **no se ha tocado el diario real ni compras reales**.

### Comprobaciones del paquete

```
uv run pytest -q tests/test_g01_diario_aceptacion.py tests/test_de_la_ficha_al_diario.py
uv run ruff check .
cd plataforma/web/app && npx --no-install tsc --noEmit
```
