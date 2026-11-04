# Revisión adversarial — cobertura diaria (task-3)

**Revisor**: `verificador` (independiente del Lead y de los demás teammates).
**Fecha**: 2026-11-04, 17:52 (Europe/Madrid).
**Objeto**: entrega de cobertura diaria declarada — `projects/cesta/cobertura_diaria.py`
(`declara`/`declaracion`/`novedad`/`captura_del_dia`/`run_del_dia`), enganche en
`projects/cesta/run.py`, los 5 ficheros de `data/cobertura/` del 4/11, la regeneración de
`data/gold/manifiesto.json`, la respuesta de `GET /api/estado` y la tarjeta de `Ajustes.tsx`.
**Estado revisado**: árbol de trabajo en `master`, HEAD `6484a4d` (**sin commitear**: 13 ficheros
modificados y 6 nuevos de la entrega, más el presente informe). Todo lo que sigue está medido
sobre disco, no leído de un documento.

**Reglas que he respetado**: no he comiteado, no he modificado código ni datos, no he tocado
PostgreSQL ni docker, y la única red usada ha sido `http://127.0.0.1:8080` (para comprobar el
producto). Esta revisión solo escribe este fichero.

---

## 0. Veredicto

**APTO CON RESERVAS.**

La premisa se confirma (hay **cinco cadenas de catálogo**, no una), las declaraciones del 4/11
**cuadran exactamente** con el bronce recalculado, el manifiesto y la API sirven las **seis
cadenas**, las puertas están en verde y el frontend está construido y servido. Pero **dos cosas
no se sostienen** y una tercera es frágil: la cifra publicada como «variación contra la captura
anterior» es falsa en las cinco cadenas (una con el signo cambiado), y la automatización que
debía producir la declaración mañana apunta a una ruta que ya no existe. Condiciones en §7.

> **Actualización (2026-11-04, 18:15).** Las cinco objeciones se corrigieron y se commitearon
> (`62407cc`, `628180b`). Re-verificadas en §8: **el veredicto final de esta revisión es APTO**,
> con la automatización diaria (tarea 12 del BACKLOG, requiere administrador) como condición
> externa que sigue abierta y que este código no puede cerrar.

---

## 1. Qué he medido y con qué

Instrumentos: `duckdb`/`polars` sobre `data/bronze/**/*.parquet`, `data/gold/precio_diario.parquet`,
`data/runs.csv`, los JSON de `data/cobertura/`, `data/gold/manifiesto.json` y `actual.json`.
Nada de confiar en las cifras del Lead: cada número de este informe sale de una consulta propia.

**No he re-ejecutado `scripts/auditar_cobertura_diaria.py`**, porque escribe
`data/debug/auditoria-cobertura/*.csv` y el encargo prohíbe modificar datos. En su lugar he
recalculado por mi cuenta **todas** las cifras que ese script y su documento afirman (§3), y he
ejecutado su puerta de evidencia, que es de solo lectura:
`verificar_evidencia.py` → **VERDE** (contrasta el CSV de la auditoría con las 5 declaraciones).

Comandos base (consola del proyecto, Python del `.venv`):

```powershell
cd F:\Proyectos\cesta
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m projects.cesta.cobertura_diaria --fecha 2026-11-04
.\.venv\Scripts\python.exe data\debug\auditoria-cobertura\verificar_evidencia.py --fecha 2026-11-04
```

---

## 2. La premisa: «una sola cadena (Lidl, 21 días)» era falsa — confirmado

Recuento propio (particiones de bronce con parquet, días con gold, filas, días en `runs.csv`):

| Cadena | Días bronce | Rango bronce | Filas bronce | Días gold | Filas gold | Días en `runs.csv` |
|---|---:|---|---:|---:|---:|---:|
| Alcampo | 43 | 2026-09-06 → 2026-11-04 | 1.037.166 | 43 | 1.036.745 | 57 |
| Aldi | 57 | 2026-09-06 → 2026-11-04 | 138.629 | 57 | 128.228 | 58 |
| Carrefour | 51 | 2026-09-07 → 2026-11-04 | 841.790 | 51 | 841.790 | 56 |
| DIA | 53 | 2026-09-07 → 2026-11-04 | 301.921 | 53 | 301.257 | 57 |
| Mercadona | 57 | 2026-09-06 → 2026-11-04 | 243.786 | 57 | 241.431 | 58 |
| *Lidl* | *21* | *2026-10-13 → 2026-11-04* | *1.884* | *21* | *1.856* | *20* |

- Gold **no añade ni inventa días**: los días con `precio_diario` coinciden con las particiones de
  bronce en las cinco cadenas (43/57/51/53/57).
- Histórico de `precio_diario.parquet`: **2.551.307 filas, 59 fechas** (09-06 → 11-04). Coincide
  con `docs/CIFRAS.md` y con el documento de auditoría.
- Días con precio en gold **desde el 1/10**: Mercadona 32, Aldi 32, Carrefour 31, DIA 29,
  Alcampo 21, Lidl 21 — exactamente la tabla de `AGENTE.md`.
- `data/runs.csv`: 352 filas de pasadas, 59 días distintos.

**Veredicto de la premisa: cinco cadenas de catálogo con 43–57 días de captura; Lidl es otra
cosa (ofertas semanales parciales, 21 días). La premisa del encargo era falsa y el Lead la
corrigió bien.**

---

## 3. Contraste de cifras (declarado/dicho vs medido por mí)

### 3.1 Ventana 2026-10-06 → 2026-11-04 (30 días, la del documento de auditoría)

| Cadena | Días captura | Bronce media/mín/máx | Gold media/mín/máx | Escritas el mismo día | Con pasada buena |
|---|---:|---|---|---:|---:|
| Alcampo | 20/30 | 23.377 / 22.632 / **28.022** | 23.365 / 22.622 / 28.004 | 20/20 | 20/20 |
| Aldi | 28/30 | 2.734 / 2.536 / 2.951 | 2.525 / 2.316 / 2.747 | 28/28 | 28/28 |
| Carrefour | 27/30 | 16.506 / 15.942 / 16.794 | 16.506 / 15.942 / 16.794 | 27/27 | 27/27 |
| DIA | 25/30 | 5.751 / 5.701 / 5.842 | 5.738 / 5.688 / 5.830 | 25/25 | 25/25 |
| Mercadona | 28/30 | 4.229 / 4.204 / 4.320 | 4.183 / 4.158 / 4.274 | 28/28 | 28/28 |

- **128 días-cadena con captura; 128/128 escritos el mismo día; 128/128 con al menos una pasada
  buena.** ✅
- **15 días sin partición y con pasadas no buenas**: Alcampo 8, Aldi 1, Carrefour 1, DIA 4,
  Mercadona 1. ✅ Exacto.
- **Histórico completo**: 3 días con pasada buena y sin partición — Alcampo 18/09, 02/10 y 05/10
  — y 21 con pasadas fallidas y sin partición. ✅ Exacto.

### 3.2 Novedad del 4/11 (recalculada desde BRONCE contra el 3/11)

| Cadena | Nuevos | Cambiados | Desaparecen | Declarado en `data/cobertura/` | ¿Cuadra? |
|---|---:|---:|---:|---|---|
| Alcampo | 943 | 4 | 303 | 943 / 4 / 303 | ✅ |
| Aldi | 5 | 62 | 130 | 5 / 62 / 130 | ✅ |
| Carrefour | 75 | 5 | 85 | 75 / 5 / 85 | ✅ |
| DIA | 20 | 425 | 20 | 20 / 425 / 20 | ✅ |
| Mercadona | 4 | 71 | 9 | 4 / 71 / 9 | ✅ |

Contraste adicional sobre gold (el documento publica las dos capas): Alcampo 942/1/303,
Aldi 2/62/126, Carrefour 75/5/85, DIA 19/425/20, Mercadona 4/71/9. ✅ Coincide con la tabla §4 del
documento de auditoría.

### 3.3 Cifras declaradas en los 5 JSON y servidas por la API

| Cadena | `filas` (bronce) | `productos` API (gold) | Referencia (fecha) | % | Veredicto |
|---|---:|---:|---|---:|---|
| Alcampo | 23.416 | 23.405 | 28.022 (2026-10-17) | 83,6 | corta |
| Aldi | 2.709 | 2.499 | 2.951 (2026-10-30) | 91,8 | ok |
| Carrefour | 16.782 | 16.782 | 16.794 (2026-10-31) | 99,9 | ok |
| DIA | 5.712 | 5.698 | 5.855 (2026-10-05) | 97,6 | ok |
| Mercadona | 4.272 | 4.226 | 4.321 (2026-10-05) | 98,9 | ok |

`filas`, `referencia`, `referencia_fecha`, `pct`, `dias_sin_datos` (11, 2, 3, 5, 2), `captura` y
`run` recalculados: **cuadran** con los ficheros escritos. ✅

### 3.4 Producto publicado

- `data/gold/manifiesto.json` (generado 17:35:18): `cobertura_declarada` = **26 entradas**
  (21 `lidl-*` + las 5 de catálogo del 4/11) y `cobertura_medida` con las **5 cadenas de
  catálogo** (intacta: mismas filas/pct/veredicto que la medición). ✅
- Las 5 declaraciones incrustadas en el manifiesto son **idénticas byte a byte** (mismo JSON) que
  los ficheros de `data/cobertura/`. ✅
- `data/gold/actual.json` **no se ha movido**: versión `20261104-144138`, publicada 14:41:38. Las
  huellas de los 6 parquet del manifiesto **coinciden** con las de `actual.json` (comparadas como
  prefijo de 12 frente a las 64 completas): lo publicado es el gold actual. ✅
- `GET http://127.0.0.1:8080/api/estado` devuelve `cobertura` para **las 6 cadenas**: Lidl con
  `ofertas_semanales_parcial` y las 5 con `catalogo_diario`, `novedad` y `metodo`. ✅

### 3.5 Declaración: comportamiento pedido

| Comprobación | Resultado |
|---|---|
| Escribe 5 ficheros, uno por cadena de catálogo | ✅ `declara()` itera `FUENTES` (5); `data/cobertura/` tiene los 5 del 4/11 |
| **No toca Lidl** | ✅ `lidl-2026-11-04.json` sigue con mtime 12:19:43 (el de su colector) |
| Sin captura del día ⇒ «sin datos» y novedad `null`, no 0 | ✅ `declaracion('aldi','2026-09-01')` → veredicto `sin datos`, `novedad{nuevos:null,…,motivo:'no hay captura de ese dia'}`, `captura:null` |
| Idempotente y atómica | ✅ recomputado el JSON con `declaracion()` y con el `json.dumps(indent=1)` de `declara()`: **sha256 idéntico** al de disco en los 5 (p. ej. mercadona `a20ca9f6dd28cc21`); escritura con `.json.tmp` + `os.replace` (líneas 353-355); **0 ficheros `.tmp`** en `data/cobertura/` y `data/gold/` |
| La fecha que recibe es la que usa | ✅ `declaracion('carrefour','2026-10-30')` → `fecha=2026-10-30`, `novedad.vs=2026-10-29` |

### 3.6 Puertas

| Puerta | Resultado |
|---|---|
| `pytest` (test_cobertura*, test_manifiesto*, test_run, test_la_pasada_publica, test_g07_manifiesto) | ✅ **76 passed, 10 skipped** (los 10 son las pruebas de PostgreSQL, esperado) |
| `pytest` extra (test_cobertura_en_pantalla, test_sin_cobertura, test_cola_sin_cobertura) | ✅ 17 passed |
| `ruff check` (código y tests tocados, `core/manifiesto.py`, `plataforma/api/main.py`) | ✅ limpio |
| Frontend `npm run tipos` | ✅ 0 errores |
| Frontend `npm test` (node) | ✅ 376/376 |
| Frontend `npm run test:componentes` (vitest) | ✅ 24/24 (incluye `Ajustes.test.tsx`, 2 pruebas) |
| Build en `dist` | ✅ `plataforma/web/dist` compilado 17:44:42 (posterior a las fuentes); `:8080/` sirve el paquete (`index-uqZHEgG-.js`) y el chunk `assets/Ajustes-ByROTNQd.js` contiene «catálogo diario», «Frescura y cobertura» y «precios cambiados» |

### 3.7 Cifras de la documentación que he podido contrastar

- `docs/COBERTURA-DIARIA-2026-11-04.md` §1, §3, §4, §6, §7 y §10: **todas las cifras que he
  recalculado cuadran**; sus `reportKey` de `data_profile`/`data_verify` existen en el almacén
  (`20261104163954719-profile-b675a291`, `20261104163954740-verify-b675a291`,
  `20261104163954823-profile-c5fcb0a2`).
- `DECISIONES.md` §5: «8.851 de los 39.837 grupos con precio tenían 2+ cadenas (22,2 %)» →
  **reproducible**: filtrando `precio_comparable=true` salen 39.837 grupos y 8.851 con 2+ cadenas.
- Commits/redes/base: `.github/` sin cambios, sin workflows nuevos, `data/` ignorado por git
  (solo hay 3 scripts antiguos de `data/debug/` versionados de commits viejos, ninguno tocado), y
  ningún fichero de base de datos con mtime de esta sesión (`diario.sqlite` 16/10,
  `inventario.sqlite` 11/10). No hay rastro de docker/PostgreSQL en el diff ni en los artefactos.

---

## 4. Objeciones, por gravedad

### O1 — ALTA. `vs_anterior_pct` no mide «contra la captura anterior»: mide contra la captura MÁS ANTIGUA de la ventana

El campo que el CLI imprime como «% sobre la captura anterior» y que viaja en los 5 JSON, en el
manifiesto y en `/api/estado` **está mal calculado en las cinco cadenas**, y en Aldi con el signo
cambiado:

| Cadena | Publicado (`vs_anterior_pct`) | Real vs 11-03 (captura anterior) | «Anterior» que usa el código |
|---|---:|---:|---|
| Alcampo | **+1,7 %** | **+2,8 %** (23.416 / 22.776) | 2026-10-06 (23.019) |
| Aldi | **+6,8 %** | **−4,4 %** (2.709 / 2.834) | 2026-10-05 (2.536) |
| Carrefour | **+1,2 %** | **−0,1 %** (16.782 / 16.792) | 2026-10-05 (16.585) |
| DIA | **−2,4 %** | **0,0 %** (5.712 / 5.712) | 2026-10-05 (5.855) |
| Mercadona | **−1,1 %** | **−0,1 %** (4.272 / 4.277) | 2026-10-05 (4.321) |

**Causa**: `projects/cesta/cobertura_diaria.py:140`

```python
anterior = next((serie[f] for f in reversed(calendario) if serie.get(f)), None)
```

`calendario` está ordenado de ayer hacia atrás; `reversed(calendario)` lo recorre **del día más
antiguo al más reciente**, así que `next` devuelve la **primera** captura de la ventana (hace ~30
días), no la última. El propio comentario de la línea 137-139 dice que debería dar «+2,8 % sobre
ayer», y da 1,7 %: el código y su comentario se contradicen.

**Reproducción**:

```powershell
cd F:\Proyectos\cesta
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m projects.cesta.cobertura_diaria --fecha 2026-11-04
# imprime: alcampo ... "+1.7% sobre la captura anterior"  (real: +2.8%)
Select-String projects\cesta\cobertura_diaria.py -Pattern 'anterior = next'
Get-Content data\cobertura\alcampo-2026-11-04.json | Select-String vs_anterior_pct   # 1.7
```

**Por qué no lo caza nadie**: `tests/test_cobertura_honesta_20261104.py:138-142` prueba con una
serie que solo tiene **un** día anterior (`{"2026-11-03": 22776, "2026-11-04": 23416}`), y ahí el
más antiguo y el más reciente coinciden; con dos o más días anteriores falla. La prueba se llama
«dice cuánto cambió contra la última captura» pero no lo prueba.

**Y los documentos lo dan por bueno**: `BACKLOG.md:55` («cuánto cambió contra la captura
anterior»), `DECISIONES.md:101-102` (mismo texto) y el CLI (`cobertura_diaria.py:422`). El dato
publicado hoy en API/manifiesto es falso para el 100 % de las cadenas. **No lo he corregido**
(regla del encargo): hay que arreglar la expresión (recorrer `calendario` sin invertir, o
`max(f for f in calendario if serie.get(f))`), añadir una prueba con 2+ días anteriores y
regenerar los 5 JSON + manifiesto.

*Nota: `referencia_fecha` (líneas 125-127) usa el mismo `reversed(calendario)` y, si el máximo
aparece varios días, informa del más antiguo (Aldi: 2.951 el 30/10 y el 31/10; declara 30/10). No
es falso, pero la etiqueta «referencia del 30 oct» elige el día más viejo de los empatados.*

### O2 — ALTA (operativa). La automatización que debía producir la declaración mañana está rota

El trabajo que añade `declara()` a `run.py` solo se ejecuta si **la cadena diaria se lanza**. La
tarea del Programador de Windows apunta a la ruta **anterior al movimiento del proyecto**:

```text
Get-ScheduledTask -TaskName 'Cesta diaria'  → Action: F:\aprendizaje\scrap\ejecutar.bat (wd=F:\aprendizaje\scrap)
Get-ScheduledTaskInfo -TaskName 'Cesta diaria' → LastRunTime 04/11/2026 15:31:14
                                                LastTaskResult 2147942667 = 0x80070003 (ERROR_PATH_NOT_FOUND)
                                                NextRunTime 05/11/2026 05:00
Test-Path F:\aprendizaje\scrap → False          Test-Path F:\Proyectos\cesta\ejecutar.bat → True
```

Es decir: **el reloj que produce la cobertura no dispara**; mañana a las 05:00 volverá a fallar y
no habrá declaración nueva si nadie lanza el ciclo a mano. Lo que sí se ha hecho es documentarlo
(`docs/COBERTURA-DIARIA-2026-11-04.md` §11, `BACKLOG.md` tarea 12, `ESTADO-AGENTE.md`), y el
arreglo exige administrador. Pero `DECISIONES.md:163` sigue afirmando «La pasada diaria ya lo hace
sola y en el orden correcto», que **no se sostiene** con la medida de arriba. Condición: corregir
esa frase o re-registrar la tarea antes de dar la cobertura por «automática».

### O3 — MEDIA. `declara()` se pierde cuando el día no llega al emparejador, y los 5 ficheros no son atómicos en conjunto

En `projects/cesta/run.py` la declaración está **dentro** del bloque que exige emparejar:

```text
327:  if not (args.sin_pipeline or args.sin_emparejar):
329:      importlib.import_module("projects.cesta.emparejar").main([])   # dentro del try
337:      importlib.import_module("projects.cesta.cobertura_diaria").declara()
345:      importlib.import_module("core.manifiesto").escribe()
```

- El **orden es correcto** (línea 337 antes de 345) y está dentro de un `try` que no tumba el día:
  eso se cumple. ✅
- Pero con **`--sin-emparejar`** (modo documentado en `--help`: «no reconstruir grupos») o si
  `emparejar.main([])` lanza, el flujo cae en el `except` de la línea 366 y **no se declara, ni se
  escribe el manifiesto, ni se publica**. La declaración se calcula **solo del bronce**, así que
  podría escribirse igualmente; hoy queda atada al emparejador. Es exactamente el caso que el
  encargo pedía mirar.
- Los 5 ficheros se escriben **en secuencia** (líneas 350-356), cada uno atómico por separado pero
  **el conjunto no**: si el fichero 3 falla (permiso, disco), quedan 2 del día y 3 del día anterior;
  `run.py` se traga la excepción y el manifiesto de después lista una mezcla. Lo que se escribió
  «a medias» es publicable.

Reproducción / evidencia:

```powershell
Select-String projects\cesta\run.py -Pattern 'sin_emparejar|declara\(\)|manifiesto' |
  Select-Object LineNumber,Line
Select-String projects\cesta\cobertura_diaria.py -Pattern 'for fuente in FUENTES|temporal =|os.replace'
```

No lo he ejecutado (lanzar la cadena haría red y capturas, fuera de alcance); es inspección del
flujo real. Arreglo sugerido: mover la declaración a su propio `try` **independiente del
emparejador** (solo depende del bronce), antes del manifiesto; y verificar al final que están los 5
del día, o escribir el conjunto fuera de la ruta publicable hasta completarlo.

### O4 — MEDIA. La API/UI mezclan «filas de bronce» con «productos de gold» sin decirlo; el tipo del frontend lo documenta al revés

En la **misma respuesta** de `/api/estado` conviven dos medidas distintas del mismo día y cadena:

| Cadena (4/11) | `productos` (gold) | `cobertura.filas` (bronce) | Diferencia |
|---|---:|---:|---:|
| Aldi | 2.499 | 2.709 | +210 (**+8,4 %**) |
| Mercadona | 4.226 | 4.272 | +46 (+1,1 %) |
| DIA | 5.698 | 5.712 | +14 |
| Alcampo | 23.405 | 23.416 | +11 |
| Carrefour | 16.782 | 16.782 | 0 |

- `plataforma/web/app/src/tipos.ts:283` dice literalmente «**Las filas de hoy en gold**» y no es
  cierto: son del bronce.
- En `Ajustes` la frase visible es «catálogo diario · **2709 filas** · 91,8 % de su referencia…»
  (`Ajustes.test.tsx:103` la fija; el mismo objeto de prueba declara `productos: 2499`), así que la
  pantalla puede leerse como «Aldi tiene 2.709 productos» cuando el catálogo publicado tiene 2.499.
- `DECISIONES.md:157-159` reconoce que las filas son bronce, pero explica la diferencia solo con
  Alcampo 23.416→23.405 y la atribuye al «filtro de alcance»; en Aldi el grueso del hueco son
  **202 filas sin precio en el bronce** (210−202 = 8 por alcance), no el filtro. El documento de
  auditoría §4 sí lo dice; `DECISIONES` lo simplifica de más.

No es un fallo de cálculo —bronce contra referencia de bronce es coherente—, es una **etiqueta
que induce a error** en el producto y un comentario de tipo que miente. Arreglo: rotular «filas
capturadas (bronce)» en la frase, corregir `tipos.ts:283`, y completar la explicación de Aldi.

### O5 — MEDIA-BAJA. Las pruebas no cubren las dos afirmaciones centrales del enganche (orden y contrato de API)

- **No hay prueba de contrato de `/api/estado`** para el bloque `cobertura` (lo pedía la tarea 5
  del BACKLOG: «prueba de contrato de la respuesta y del componente»). `Select-String tests\*.py
  -Pattern 'catalogo_diario'` solo aparece en `test_cobertura_declarada_20261104.py`, que prueba el
  módulo, no el endpoint. La parte de API la he tenido que verificar a mano (§3.4).
- La prueba del enganche en `run.py` es un grep del código fuente:

  ```python
  # tests/test_cobertura_declarada_20261104.py:154-162
  fuente = inspect.getsource(run)
  assert ".declara(" in fuente
  ```

  **Pasaría igual** si la llamada estuviera después del manifiesto, dentro de un `if False` o en
  una rama inalcanzable. No prueba el orden (declara < manifiesto) ni el `try` que no tumba el día,
  que es lo que el encargo exige.

Esto no invalida lo entregado (el orden real es correcto, verificado por inspección), pero es la
razón por la que O1 y O3 han podido pasar puertas en verde: ninguna prueba falla si se rompen.
Arreglo: prueba de flujo del orden con dobles (`declara` y `manifiesto.escribe` espías, comprobar
orden y que una excepción en `declara` no impide el manifiesto) y prueba de contrato del endpoint.

---

## 5. Observaciones menores (no bloquean, pero están)

1. **`BACKLOG.md:15-17` mezcla dos fotos distintas**: «El catálogo son 52.982 productos» (actual)
   con «8.864 grupos… 22,9 % de 38.682» (foto de las 14:30, **antes** del reproceso de Alcampo).
   Medido hoy: 52.982 productos; grupos con precio: 39.178 y 8.841 con 2+ cadenas (22,6 %) si se
   exige `precio_cent`; 39.837 y 8.851 (22,2 %) con `precio_comparable` (la definición de
   `DECISIONES`); «grupos comparables» de `CIFRAS.md` es 8.875 (≥2 fuentes, con o sin precio). Son
   tres definiciones distintas; conviene decirlas con su nombre o fecharlas.
2. **`AGENTE.md`** conserva la tabla «Estado real… 14:30» con 52.342 productos y 2.527.902 filas de
   histórico; es una foto previa al reproceso (la diferencia son exactamente las 23.405 filas
   recuperadas de Alcampo). Está fechada, así que no es un error si se lee como foto; pero
   `BACKLOG` tarea 6 dice «la tabla está corregida» y la cabecera de la tabla no lo está.
3. **`docs/COBERTURA-DIARIA-2026-11-04.md` §4**: «Aldi de 2.709 a 2.499 (de esas 202 filas… sin
   precio)» — 2.709−2.499 = **210**, no 202; las 8 restantes salen del filtro de alcance.
4. **`run_del_dia`** compara el prefijo de fecha **UTC** de `runs.csv` con el día local: una pasada
   que cruce medianoche UTC puede quedar como «sin run». No se ha dado hoy; es un borde.
5. **Árbol sin commitear**: HEAD sigue en `6484a4d`, con 13 ficheros modificados y 6 nuevos. El
   código de la entrega está en el árbol, no en un commit. Yo no comiteo (regla del encargo); la
   puerta de la doctrina («sin commit no está terminado») la cierra el Lead.
6. `data/` tiene 3 scripts antiguos versionados (`data/debug/b04_*.py`, `recorrido_a09.py`) de
   commits anteriores: la regla «`data/` no entra en git» se cumple para **esta** entrega (nada
   nuevo versionado), pero no es literal en el repo.

---

## 6. Lo que sí queda demostrado (y no hay que volver a dudar)

- La premisa errónea está corregida con medición: **5 cadenas de catálogo**, 43–57 días de bronce,
  57/58/56/57/58 días de pasada; Lidl 21 días y alcance parcial.
- Las **5 declaraciones del 4/11 cuadran exactamente** con el bronce recalculado (filas, novedad,
  referencia, mtime y run), y **no tocan Lidl**.
- La declaración es **idempotente** (bytes idénticos recomputados) y no deja `.tmp`.
- El manifiesto pasa a **26 declaraciones** con la `cobertura_medida` intacta y **sin mover la
  versión publicada**; las huellas del manifiesto coinciden con `actual.json`.
- La **API sirve cobertura para las 6 cadenas** y el build servido en `:8080` contiene la tarjeta.
- La **documentación de auditoría** (`docs/COBERTURA-DIARIA-2026-11-04.md`) resiste el recálculo:
  sus tablas de 30 días, novedad, frescura y agregados son correctas, y sus `reportKey` existen.

---

## 7. Veredicto y condiciones

**APTO CON RESERVAS.** La entrega consigue lo que se proponía (declarar la cobertura medida de las
cinco cadenas, hacerla viajar en manifiesto/API y verla en pantalla) y las cifras del contraste
cuadran; no es «NO APTO» porque el flujo principal está medido y funciona. Las reservas son dos
defectos reales y tres deuda, y se levantan así:

1. **O1 (obligatoria antes de decir «cuánto cambió»)**: corregir `vs_anterior_pct` (o retirarlo de
   JSON/manifiesto/API y de los documentos), añadir la prueba con 2+ días anteriores y regenerar
   los 5 JSON + manifiesto. Hoy el 100 % de los valores publicados es falso y uno tiene el signo
   cambiado.
2. **O2 (obligatoria antes de prometer «todos los días»)**: re-registrar la tarea `Cesta diaria`
   con administrador **o** dejar escrito en `DECISIONES.md` que el ciclo es manual hasta entonces;
   quitar/corregir la frase «La pasada diaria ya lo hace sola».
3. **O3 (recomendada, antes de ampliar)**: desacoplar `declara()` del emparejador y comprobar que
   quedan los 5 ficheros del día (declaración conjunta o aviso si falta).
4. **O4 (recomendada)**: rotular bronce vs gold donde se enseña (API/tipos/pantalla) y completar la
   explicación de Aldi.
5. **O5 (recomendada)**: prueba de contrato de `/api/estado` y prueba de flujo del orden
   `declara → manifiesto` (no un grep).

Con O1 y O2 corregidas, la entrega pasa a **APTO**; ninguna de las dos requiere tocar los datos ya
medidos (las declaraciones se regeneran a partir del mismo bronce).

---

## Anexo — trazabilidad de la revisión

- Hora de las medidas: **17:40–17:52** del 2026-11-04. Estado del árbol durante la revisión:
  HEAD `6484a4d`, 13 modificados / 6 nuevos (los documentos se estaban actualizando mientras
  revisaba; la última pasada sobre `docs/COBERTURA…` es de 17:46 y sobre `manifiesto.py`/API de
  17:48 — solo docstrings y rutas, sin cambio de comportamiento).
- Ficheros de datos que **no** he tocado: todas las lecturas son de solo lectura. No he ejecutado
  `declara()` sobre el día real; la idempotencia la he comprobado recomputando el contenido y
  comparando sha256 con el disco (mismo resultado que reescribir, sin escribir).
- Herramientas de calidad del harness: `data_report` confirma que existen los informes `profile` y
  `verify` citados por el documento de auditoría.

---

## 8. Addendum — re-verificación tras las correcciones

**Cuándo y sobre qué**: 2026-11-04, **18:12–18:18**, sobre los commits **`62407cc`** (núcleo y
evidencia) y **`628180b`** (pantalla y estado), con HEAD en `628180b`. El árbol estaba limpio
salvo una aclaración **solo documental** en `AGENTE.md` (18:14: la tabla de las 14:30 se marca
como foto fechada). No he tocado código ni datos: todo lo de abajo está medido con comandos
propios y sin escribir nada.

### O1 — cerrada (variación contra la captura anterior y referencia en empate)

`veredicto` ya recorre `calendario` en orden (la primera captura con datos es la penúltima). Mis
tres cálculos coinciden entre sí, con los JSON regenerados y con la API en vivo:

| Cadena | Código (`veredicto`) | Mi recálculo independiente | JSON en disco | Manifiesto | API `:8080` |
|---|---:|---:|---:|---:|---:|
| Alcampo | **+2,8** | +2,8 (23.416/22.776) | +2,8 | +2,8 | +2,8 |
| Aldi | **−4,4** | −4,4 (2.709/2.834) | −4,4 | −4,4 | −4,4 |
| Carrefour | **−0,1** | −0,1 | −0,1 | −0,1 | −0,1 |
| DIA | **0,0** | 0,0 | 0,0 | 0,0 | 0,0 |
| Mercadona | **−0,1** | −0,1 | −0,1 | −0,1 | −0,1 |

- **Referencia en empate**: Aldi tenía el máximo (2.951) el 30/10 **y** el 31/10; ahora declara
  `referencia_fecha = 2026-10-31` (el más reciente), como pedí.
- **Regeneración**: los 5 JSON del 4/11 (18:09) y el manifiesto (18:09:18) llevan los valores
  corregidos. El manifiesto tiene **26 declaradas** (21 Lidl + 5) y **5 medidas**, y sus 5
  entradas de catálogo son **idénticas** a los ficheros. Las huellas de los 6 parquet siguen
  coincidiendo con `actual.json`, que **no se ha movido** (`20261104-144138`, 14:41:38).
- **Idempotencia**: recomputado el contenido con `declaracion()` y comparado byte a byte con el
  disco, los 5 son idénticos; la `novedad` sigue siendo 943/4/303, 5/62/130, 75/5/85, 20/425/20 y
  4/71/9.
- Pruebas nuevas: dos capturas anteriores (10,0 % vs el 340 % del código viejo), hueco de un día
  sin captura y empate de referencia; verdes en la suite de abajo.

### O2 — cerrada la parte documental; la operativa sigue abierta (externa)

- La frase «la pasada diaria ya lo hace sola» **ya no está** en `DECISIONES.md` (solo aparece
  citada en `COBERTURA…` §12 como la objeción que era). §5 dice ahora que la declaración se hace
  antes del manifiesto y aunque el emparejador falle, y que **no puede lanzarse sola** por la
  tarea del Programador.
- **La automatización sigue rota** (medido ahora, no depende del código): acción
  `F:\aprendizaje\scrap\ejecutar.bat`, `LastTaskResult 2147942667` (`0x80070003`),
  `NextRunTime 05/11/2026 05:00`, ruta inexistente. Está en `BACKLOG.md` tarea 12 y
  `COBERTURA…` §11; re-registrarla exige administrador. El histórico es real; **el mañana
  depende de ese arreglo**, y mientras tanto el ciclo se lanza a mano (`ejecutar.bat`).

### O3 — cerrada (declaración antes del emparejador y conjunto atómico)

- `run.py`: la declaración vive en **su propio `try`** (líneas 337-343), **antes** del bloque del
  emparejador (348) y, por tanto, antes del manifiesto. Se ejecuta también con `--sin-emparejar` y
  si el emparejador lanza. Solo se salta con `--sin-pipeline`, coherente: en ese modo tampoco hay
  manifiesto ni publicación.
- `declara()`: prepara los **5 temporales** y solo después hace los `os.replace`; si una
  declaración falla a mitad, borra los temporales y **no sustituye ninguno**. Verificado en el
  código y con la prueba que fuerza el fallo en el tercero; en disco **0 `.tmp`**.
- Prueba de orden: exige `.declara()` antes de `core.manifiesto` **y antes de `emparejar`**.

### O4 — cerrada (bronce vs gold etiquetado; día local del run)

- Pantalla: la frase dice «**filas capturadas**» (`cobertura.ts:53`) y el comentario explica que
  son del bronce; `tipos.ts:283-284` documenta la diferencia (Aldi 2.709 en bronce vs 2.499 en
  gold). El build servido en `:8080` contiene «filas capturadas».
- `DECISIONES.md` explica **Aldi 210 = 202 sin precio + 8 de alcance**; comprobado: bronce 2.709,
  202 sin `precio_cent`, gold 2.499.
- `run_del_dia` convierte el `ts` a **Europe/Madrid** antes de comparar (antes usaba el prefijo
  UTC): prueba con una pasada a las 23:30Z que pertenece al día local siguiente.

### O5 — cerrada (contrato de `/api/estado` y orden)

- `tests/test_contrato_estado_cobertura_20261104.py` monta la API **sin PostgreSQL** (duckdb en
  memoria y `AJUSTES` de prueba), pide `/api/estado` y comprueba que la cobertura declarada viaja
  con filas y novedad, y que una cadena sin fichero sale **sin** `cobertura`. Verde.
- La prueba del enganche ya no es un `grep`: exige el orden `.declara()` < `manifiesto` <
  independencia del `emparejador`. Verde.

### Puertas sobre el estado commiteado

| Puerta | Resultado |
|---|---|
| `pytest` del subconjunto relevante (+ contrato y cobertura declarada) | ✅ **83 passed, 10 skipped** |
| Suite completa | ✅ **1395 passed, 782 skipped, 1 deselected** (el lento preexistente de la ficha real de Carrefour), exit 0, 132,75 s |
| `ruff check` (ficheros tocados) | ✅ limpio |
| Web `npm run tipos` | ✅ 0 errores |
| Web `npm test` / `npm run test:componentes` | ✅ 376/376 · 24/24 |
| Build servido en `:8080` | ✅ dist 18:10:25; `index` 200 y chunk de Ajustes con la frase nueva |
| `docs/CIFRAS.md` reescrito por la pasada | ✅ 52.982 productos · 8.875 grupos · 2.551.307 filas / 59 días |

### Lo que sigue abierto

1. **La automatización diaria** (O2 operativa): la tarea `Cesta diaria` apunta a la ruta vieja y
   exige administrador para re-registrarla (`BACKLOG.md` tarea 12, `COBERTURA…` §11,
   `DECISIONES.md` §5). No es un defecto del código entregado y no se puede cerrar desde esta
   sesión; sí es condición para que la cobertura se produzca sola mañana.
2. Nada más de O1–O5. La foto del `AGENTE.md` de las 14:30 queda aclarada como foto fechada
   (cambio documental pendiente del commit del Lead).

### Veredicto final

**APTO.** Las cinco objeciones están cerradas y las he re-verificado por mi cuenta (cifras de
variación y referencia, JSON, manifiesto, huellas, API en vivo, suite completa y puertas del
frontend). La única condición abierta es **externa al código**: re-registrar la tarea del
Programador (administrador) para que el ciclo diario se lance solo; hasta entonces, lanzar
`F:\Proyectos\cesta\ejecutar.bat` a mano. No he commiteado: este addendum queda para que lo
incluya el Lead en su commit/push.

