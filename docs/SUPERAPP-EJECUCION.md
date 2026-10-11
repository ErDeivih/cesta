# SUPERAPP · Tablero de ejecución

Objetivo y paquetes: [`SUPERAPP-GOAL-CONTINUACION-2026-10-11.md`](SUPERAPP-GOAL-CONTINUACION-2026-10-11.md).
Estado vivo y resumen vigente: [`SUPERAPP-ESTADO.md`](SUPERAPP-ESTADO.md).

Estados permitidos por paquete: `pendiente` · `en curso` · `implementado sin ensayo real` ·
`verificado` · `limitado por fuente` · `bloqueado`. **«Verificado» exige su criterio de aceptación
completo, no una compilación.**

## Tablero

| Paquete | Estado | Evidencia | Siguiente acción |
|---|---|---|---|
| G01 Diario efectivo | `en curso` | ver abajo | el formulario manda la clave de operación |
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
| **La aceptación por HTTP montado**: recibo `{id, dia}`, cantidad y macros que se vuelven a leer, cobertura 1/2 y 2/2, el rango viendo el alta, negativos/compra/receta inventada rechazados, dos comidas iguales y el borrado con recibo | `tests/test_g01_diario_http.py` — **10 pasan** (1,9 s) | 11 oct 2026 |
| **El formulario**: `Alta` ofrece **cantidad (g)** y los **tres macronutrientes**, con la aclaración de que lo apuntado es lo comido y no los valores de 100 g; vacío es `null` (no `0`) y la coma decimal se acepta | `src/paginas/Diario.tsx` — `aNumero()` | 11 oct 2026 |
| **Al guardar se limpia solo lo guardado**: si el alta falla, el error se ve y no se borra lo escrito | `src/paginas/Diario.tsx` | 11 oct 2026 |
| **El puente compra→diario consume el recibo** (`{anotadas, ya_estaban, ajenas, sin_nutricion}`, tipado) y lo cuenta en pantalla; **invalida `['diario-rango']`**; y **solo usa la lista de casa**, sin elegir otra en silencio | `src/paginas/Diario.tsx`, `src/api/cesta.ts` — `npm run tipos` limpio | 11 oct 2026 |
| `tsc` cazó un comentario sin abrir en el primer intento y se corrigió antes de nada | `npx tsc --noEmit` | 11 oct 2026 |
| **`sin_nutricion` se rellena**: el puente anota sin nutrición y **ahora lo dice**, que era la mitad que faltaba de su propia promesa. *Medido: `sin_nutricion: []` mientras la entrada no llevaba un solo nutriente, y el fichero lo enseñaba* | `plataforma/api/main.py` — arreglo | 11 oct 2026 |
| **Las tres pruebas del recibo contra el almacén real**: las cuatro claves, `anotadas + ya_estaban == 1`, **la segunda vez no anota y lo dice**, una línea ajena **se devuelve en `ajenas`**, y **el recibo y el día dicen lo mismo sobre la nutrición** | `tests/test_g01_recibo_del_puente.py` — **3 pasan** (5,8 s, con `CESTA_POSTGRES` al 5434) | 11 oct 2026 |
| **El diario real, comprobado intacto** (mtime 10-10 13:44) tras sospechar que un ensayo lo había tocado | `data/diario.sqlite` | 11 oct 2026 |
| **Idempotencia por operación, en el almacén y el contrato**: `clave_operacion` opcional, índice único **parcial** por dueño+clave, y repetirla devuelve **la entrada que ya hay** | `core/diario.py`, `plataforma/api/diario.py` — 4 pruebas | 11 oct 2026 |
| Que **dos operaciones distintas con lo mismo son dos**, que **sin clave se comporta como antes**, y que **la clave no cruza entre personas** | `tests/test_g01_diario_aceptacion.py` — **15 pasan** | 11 oct 2026 |
| **La columna `unidad` ya existía** en el esquema del diario: desbloquea el caso `ml`/`g` sin migración nueva | `core/diario.py:47` | 11 oct 2026 |

**Lo que ya existía y se conserva**: `tests/test_de_la_ficha_al_diario.py` (la cuenta de la ficha y
lo ausente-frente-a-cero) y `POST /api/diario/desde-ficha` con `gramos` + valores por 100 g, que
hace la cuenta **en el servidor**.

### Pendiente, y por qué

**Cómo se ejecuta la prueba del recibo** (la cadena se lee al importar, no vale `monkeypatch`):

    $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'
    uv run pytest -q tests/test_g01_recibo_del_puente.py

Sin esa variable **se salta diciendo qué hacer**, no conecta al 5432 por defecto.

1. **El formulario todavía no manda la clave.** El almacén y el contrato ya la aceptan y están
   probados, pero `Diario.tsx:Alta` no la genera: **la función existe y no está enganchada**, así que
   hoy un doble clic sigue duplicando. *Acción: `crypto.randomUUID()` al enviar, **estable mientras
   se reintenta la misma operación** y nueva en cada alta distinta.*
2. **El puente compra→diario usaba el número de la previa**, no el recibo: `Diario.tsx:62` hace
   `setAnotadas(previa?.anotarian.length ?? 0)`. *Acción: consumir `ReciboDeAlta`/lo que devuelva
   `anotarDeLaCompra`, y decir cuántas se anotaron de verdad.*
3. **Idempotencia por operación**: hoy no hay clave. *Acción: una clave por operación (doble clic,
   respuesta perdida, reintento) que no duplique, **sin** deduplicar por nombre+fecha+nutrientes —
   eso ya está probado que debe permitir dos comidas iguales.*
4. **`ml` frente a `g`**: el formulario solo ofrece gramos. Ofrecer mililitros exige una unidad
   declarada en el almacén (`cantidad_g` no puede guardar ml: es justo la equivalencia que el
   documento prohíbe sin densidad trazable). *Acción: decidir con el modelo, no en la pantalla.*
5. **Aislamiento por HTTP montado**: anónimo 401; B no enumera, lee, modifica ni borra entradas de A
   por ID o fecha; cambio A→B sin cachés ni borradores. *Acción: extender las pruebas de la API con
   `TestClient`, que es donde se prueba la ruta y no la función interna.*
6. **Navegador 390 y 1440**: alta efectiva, lectura, recarga, borrado y tendencias, guardando IDs y
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
