# Cobertura diaria medida — 2026-11-04

**Medido el 2026-11-04 entre las 17:39 y las 18:55 (hora de Madrid), sobre ficheros locales.**
Ventana auditada:
**2026-10-06 → 2026-11-04** (30 días de calendario que acaban en el día de referencia).
Instrumento: `scripts/auditar_cobertura_diaria.py`. Evidencia:
`data/debug/auditoria-cobertura/cobertura_diaria.csv` (150 filas = 5 cadenas × 30 días).

Este documento no reinterpreta `docs/CIFRAS.md` ni `AGENTE.md`: los reconcilia. Todas las cifras
de aquí salen de ejecutar el script; ninguna está copiada de otro documento.

---

## 1. La premisa corregida: «solo Lidl, 21 días» era falsa

La ficha del agente decía «cobertura diaria: **solo Lidl**, 21 días». **De dónde salía, medido**:
en `data/cobertura/` solo había **21 ficheros `lidl-*.json`** (del 13/10 al 4/11), escritos por el
colector de Lidl. Eso es `cobertura_declarada` —lo que un colector dice de su propio alcance—, no
la cobertura **medida**. Leerlo como si fuera la cobertura de la plataforma invirtió el resultado.

Lo medido hoy, en disco:

| Cadena | Días con captura (histórico) | Primera | Última | Días con pasada en `runs.csv` | Filas de bronce | Filas de gold |
|---|---:|---|---|---:|---:|---:|
| Alcampo | 43 | 2026-09-06 | 2026-11-04 | 56 | 1.037.166 | 1.036.745 |
| Aldi | 57 | 2026-09-06 | 2026-11-04 | 58 | 138.629 | 128.228 |
| Carrefour | 51 | 2026-09-07 | 2026-11-04 | 56 | 841.790 | 841.790 |
| DIA | 53 | 2026-09-07 | 2026-11-04 | 57 | 301.921 | 301.257 |
| Mercadona | 57 | 2026-09-06 | 2026-11-04 | 58 | 243.786 | 241.431 |
| *Lidl (contexto, no es catálogo)* | *21* | *2026-10-13* | *2026-11-04* | *20* | *1.884* | *1.856* |

**Corrección**: la comparación diaria es de **cinco cadenas de catálogo**, con 43–57 días de
captura cada una y pasadas registradas casi todos los días. Lidl no es una cadena de catálogo: son
**ofertas semanales parciales** (91 productos el 4/11; su propia declaración lo dice: `cobertura:
"ofertas_semanales_parcial"`). Los «21 días» eran los de Lidl, no los de la plataforma.

La suma de filas de gold por cadena da **2.551.307**, que coincide con el histórico de
`docs/CIFRAS.md` (59 días con algún dato: el único día sin ninguna captura de catálogo es el
**2026-11-01**).

---

## 2. Qué se ha medido y cómo

Solo lectura local, sin red y sin base de datos:

- `data/bronze/fuente=<cadena>/fecha=<día>/part.parquet` — la captura cruda del día (partición).
- `data/gold/precio_diario.parquet` — la tabla diaria publicable.
- `data/runs.csv` — una fila por pasada del colector (`ts` en UTC, día contado en Europe/Madrid).
- `data/cobertura/<cadena>-2026-11-04.json` — la declaración del Lead (se **lee** para contrastar;
  esta auditoría no la escribe).

Definiciones, para que las cifras se puedan discutir:

- **Día con captura**: existe partición de bronce con al menos un `.parquet` para ese día.
- **Novedad**: se mide **sobre BRONCE**, que es la captura del día, contra la **captura anterior de
  esa misma cadena** (el último día con captura, aunque quede antes de la ventana). Se cuentan
  `id_fuente` nuevos, `id_fuente` que ya estaban con otro `precio_cent`, y `id_fuente` de la captura
  anterior que hoy no aparecen. La misma cuenta se publica **también sobre gold**, al lado, con
  nombre explícito. **Gold es bronce filtrado por alcance**, no la captura: sus cifras pueden diferir.
- **Escrito el mismo día**: la fecha local del `mtime` del parquet coincide con la fecha de la
  partición.
- **Pasada buena**: alguna fila de `runs.csv` para ese día con `ok=True`.

---

## 3. Volumen de la ventana, por cadena (2026-10-06 → 2026-11-04)

| Cadena | Días con captura | Días con gold | Filas bronce media / mín / máx | Filas gold media / mín / máx |
|---|---:|---:|---|---|
| Alcampo | 20/30 | 20 | 23.377 / 22.632 / **28.022** | 23.365 / 22.622 / 28.004 |
| Aldi | 28/30 | 28 | 2.734 / 2.536 / 2.951 | 2.525 / 2.316 / 2.747 |
| Carrefour | 27/30 | 27 | 16.506 / 15.942 / 16.794 | 16.506 / 15.942 / 16.794 |
| DIA | 25/30 | 25 | 5.751 / 5.701 / 5.842 | 5.738 / 5.688 / 5.830 |
| Mercadona | 28/30 | 28 | 4.229 / 4.204 / 4.320 | 4.183 / 4.158 / 4.274 |

Los días con gold coinciden **exactamente** con los días con partición de bronce en las 5 cadenas
(20, 28, 27, 25, 28): gold no añade ni inventa días.

El máximo de Alcampo es el día atípico **2026-10-17 (28.022 filas)**, el que fija su referencia y
hace que el resto salga «corta» (ver `BACKLOG.md`, tarea 2). No es un error de esta medición.

---

## 4. Novedad del día de referencia (2026-11-04)

Medido sobre **bronce**; entre paréntesis, la misma cuenta sobre **gold**:

| Cadena | Filas bronce | Filas gold | Nuevos | Cambiados | Desaparecen | Captura previa | Escrito (mtime) | Pasada |
|---|---:|---:|---:|---:|---:|---|---|---|
| Alcampo | 23.416 | 23.405 | **943** (942) | **4** (1) | **303** (303) | 2026-11-03 | 14:31 | 1/1 buena |
| Aldi | 2.709 | 2.499 | **5** (2) | **62** (62) | **130** (126) | 2026-11-03 | 12:21 | 1/1 buena |
| Carrefour | 16.782 | 16.782 | **75** (75) | **5** (5) | **85** (85) | 2026-11-03 | 13:05 | 1/1 buena |
| DIA | 5.712 | 5.698 | **20** (19) | **425** (425) | **20** (20) | 2026-11-03 | 12:31 | 1/1 buena |
| Mercadona | 4.272 | 4.226 | **4** (4) | **71** (71) | **9** (9) | 2026-11-03 | 12:21 | 1/1 buena |

Las cifras de bronce **coinciden exactamente** con la `novedad` de las declaraciones
`data/cobertura/<cadena>-2026-11-04.json` que escribió el Lead (contrastado con
`verificar_evidencia.py`, en verde). Las de gold difieren en Alcampo (943/4/303 vs 942/1/303) y
Aldi (5/62/130 vs 2/62/126) porque **gold descarta filas de la captura**: el 4/11 Alcampo pasa de
23.416 filas de bronce a 23.405 de gold (11 por alcance) y Aldi de 2.709 a 2.499 — **210 menos**,
de las que **202 venían sin precio** en el bronce y **8 más descarta el alcance**. La declaración
lleva las filas de bronce y la API `productos` las de gold: no son el mismo número y la pantalla
ahora lo dice («filas capturadas»).

**Reconciliación con `AGENTE.md` y `CIFRAS.md`** (no se contradicen, hablan de capas distintas):
- `CIFRAS.md` da las filas **de bronce** del día: mercadona 4.272, aldi 2.709, alcampo 23.416…
- `AGENTE.md` da las filas **de gold**: mercadona 4.226, aldi 2.499, alcampo 23.405…
- `AGENTE.md` cuenta días **desde el 1/10** (mercadona 32, aldi 32, carrefour 31, DIA 29, Alcampo
  21); esta auditoría cuenta **la ventana de 30 días que acaba hoy** (28, 28, 27, 25, 20). Las dos
  cuentas están medidas y son compatibles.

---

## 5. Novedad de los últimos días (sobre bronce)

Del 28/10 al 4/11. Celdas en `nuevos / cambiados / desaparecen`; `—` = sin captura.

| Día | Alcampo | Aldi | Carrefour | DIA | Mercadona |
|---|---|---|---|---|---|
| 28/10 | — | 7 / 47 / 83 | 167 / 29 / 88 | 14 / 401 / 19 | 10 / 53 / 7 |
| 29/10 | — | 1 / 2 / 0 | 80 / 14 / 102 | 10 / 150 / 19 | 12 / 58 / 6 |
| 30/10 | 982 / 4.449 / 659 | 147 / 5 / 8 | 105 / 67 / 76 | 19 / 46 / 12 | 10 / 63 / 6 |
| 31/10 | 79 / 17 / 1.679 | **0 / 0 / 0** | 99 / 45 / 73 | 15 / 3 / 32 | 6 / 60 / 11 |
| 01/11 | — | — | — | — | — |
| 02/11 | 210 / 72 / 94 | 13 / 85 / 139 | 70 / **1.338** / 112 | 22 / 1 / 18 | 39 / 88 / 21 |
| 03/11 | 319 / 18 / 356 | 15 / 0 / 6 | 91 / 412 / 51 | 11 / 131 / 12 | 11 / 65 / 6 |
| 04/11 | **943 / 4 / 303** | 5 / 62 / 130 | 75 / 5 / 85 | 20 / **425** / 20 | 4 / 71 / 9 |

Alcampo no capturó el 28/10 ni el 29/10; sus dos capturas inmediatamente anteriores son
24/10 (447 / 62 / 78) y 26/10 (547 / 583 / 33).

Acumulado de la ventana de 30 días (suma de la novedad de cada día con captura):

| Cadena | Días con captura | Ids nuevos | Precios cambiados | Ids desaparecen |
|---|---:|---:|---:|---:|
| Alcampo | 20 | 14.726 | 28.861 | 15.152 |
| Aldi | 28 | 1.092 | 623 | 919 |
| Carrefour | 27 | 3.247 | 8.587 | 3.050 |
| DIA | 25 | 489 | 2.626 | 632 |
| Mercadona | 28 | 300 | 1.532 | 349 |

**Matiz honesto sobre «datos nuevos todos los días»**: de los **128 días con captura**, en **124**
la novedad frente a la captura anterior no es cero. Los **4 días idénticos** son todos de Aldi
(06/10, 13/10, 17/10 y 31/10): la captura se repite sin cambios. Es decir: la plataforma **trae
datos frescos cada día** (mtime del mismo día en 128/128 días), aunque algún día una cadena repita
el mismo surtido y precios. No se sostiene «novedad no nula en cada cadena y cada día»; sí se
sostiene «novedad en 124 de 128 días-cadena».

---

## 6. Escritura de la partición y pasada registrada

En la ventana:

- **128 días con captura; 128 escritos el mismo día** (fecha local del `mtime` = fecha de la
  partición). Ninguna partición se escribió con retraso de días.
- **128/128 con al menos una pasada buena** en `runs.csv`; **0** días con captura sin pasada
  registrada.
- **15 días sin partición y con pasadas no buenas** (`ok=False`): Alcampo 8, Aldi 1, Carrefour 1,
  DIA 4, Mercadona 1. **La causa no se atribuye aquí**: el detalle de cada pasada (filas, errores,
  `ok`) está en `data/runs.csv` y `data/ejecuciones.log`; en el CSV quedan con el estado
  `sin_captura_run_fallido`.
- En todo el histórico: **3 días con pasada buena y sin partición** (Alcampo 18/09, 02/10 y 05/10:
  «trajo y no escribió») y **21** con pasadas fallidas y sin partición. El patrón es histórico y
  raro; en la ventana de 30 días no ocurre.

El caso del **4/11 en Alcampo** se ve en los datos: pasada a las **12:58** (con 23.416 filas y
`ok=True`), partición escrita a las **14:31** — el día se recuperó del crudo después de que la
guarda de cobertura vetara la escritura (documentado en `BACKLOG.md`, tarea 1). La declaración del
Lead registra esa misma escritura (`captura.escrita: 2026-11-04T14:31:00`).

---

## 7. Evidencia y puerta de calidad de datos

Artefactos (todo en `data/debug/auditoria-cobertura/`; `data/` está fuera de git):

| Fichero | Qué es |
|---|---|
| `cobertura_diaria.csv` | 150 filas × 26 columnas: una por (cadena, día), incluidos los días sin captura |
| `mercadona-2026-11-04.csv` | muestra sistemática del bronce de Mercadona: 475 de 4.272 filas (1 de cada 9, orden por `id_fuente`), 55 columnas |
| `auditoria.log` | salida completa de la auditoría en **modo medida** (por defecto, salida 0) |
| `auditoria-estricta.log` | salida de la **puerta estricta** `--exigir-dias 28` (salida 1: cumplen 2/5) |
| `verificar_evidencia.py` | puerta de evidencia: CSV, enum, unicidad y **novedad sobre bronce == declaración**. En verde el 2026-11-04 |

Resultados de las herramientas de calidad (`dsh-data-quality`):

| Comprobación | reportKey | Veredicto |
|---|---|---|
| `data_profile` de `cobertura_diaria.csv` | `20261104163954719-profile-b675a291` | 150×26; **99,6 %** global; unicidad 100 %; validez 100 %; consistencia 100 %; completitud 97,9 % |
| `data_verify` de `cobertura_diaria.csv` | `20261104163954740-verify-b675a291` | **PASSED**: 150 filas, 6 reglas (unique `(fuente,fecha)`, not-null `fuente`/`fecha`/`filas_gold`, range `filas_gold>=0`, enum de `estado`) |
| `data_profile` de `mercadona-2026-11-04.csv` | `20261104163954823-profile-c5fcb0a2` | 475×55; unicidad 100 %; validez 100 %; completitud 50,3 % (bronce disperso, ver abajo) |
| `data_clean` (dryRun) de `cobertura_diaria.csv` | — (dryRun no persiste informe) | 150→150 filas, 0 duplicados, 0 celdas no conformes: **no hace falta copia limpia** |

Hallazgos del perfilado, leídos con su significado:

- **Completitud 97,9 %**: los 22 nulos son **semánticos**, no suciedad. 22 días sin captura dejan
  vacíos `captura_previa`, `mtime_particion` y `escrito_el_mismo_dia`; 7 días sin pasada dejan
  vacíos `run_filas`/`run_ts`. Rellenarlos inventaría dato.
- **Sin duplicados**: `(fuente, fecha)` único (150/150) y en gold no hay duplicados
  `(fuente, fecha, id_fuente)` (2.551.307 filas, 2.551.307 claves distintas).
- **Sin tipos mixtos reales**: la primera pasada marcó `si`/`no` como tipos mixtos porque el
  perfilador infiere `si` como booleano; el CSV canónico los escribe **1/0** (celda vacía = sin
  dato) y la primera pasada quedó superada.
- **Bronce disperso por diseño**: en la muestra de Mercadona, `region` está vacía al 100 %,
  `nutricion`/`sellos`/`tipo_producto` también; no es un fallo de la muestra: son columnas que
  Mercadona no publica (comparar con `docs/CADENAS.md`). La muestra conserva el 100 % de unicidad
  de `id_fuente` y precios válidos (`precio_cent` 21–36.800 céntimos).
- Valores extremos de novedad (Alcampo 30/10 con 4.449 cambiados, Carrefour 02/11 con 1.338) no son
  errores: son días de cambio de folleto/precios, coherentes con las filas de la captura.

---

## 8. Cómo reproducirlo

Consola Windows:

```powershell
$env:PYTHONIOENCODING='utf-8'
cd F:\Proyectos\cesta

# 1) La auditoría: tablas + CSV + muestra. Por defecto MIDE (sale 0 si pudo medir; los huecos
#    los dice en la tabla). Para usarla como puerta estricta, --exigir-dias N:
uv run python -m scripts.auditar_cobertura_diaria --hasta 2026-11-04 --dias 30
uv run python -m scripts.auditar_cobertura_diaria --hasta 2026-11-04 --dias 30 --exigir-dias 28
#    (la segunda sale 1: hoy solo 2/5 cadenas llegan a 28/30; el umbral no se rebaja)

# 2) La puerta de evidencia: CSV + enum + novedad sobre bronce == declaración + muestra.
uv run python data/debug/auditoria-cobertura/verificar_evidencia.py --fecha 2026-11-04

# 3) La premisa: qué hay declarado en disco (hoy: 5 declaraciones de catálogo + Lidl del 4/11,
#    y 21 ficheros lidl-* históricos).
Get-ChildItem data\cobertura\*-2026-11-04.json
Get-ChildItem data\cobertura\lidl-*.json

# 4) La puerta de tests completa, EXACTAMENTE como se ejecutó. El `--deselect` es un test
#    preexistente que depende del disco: recorre los 58.760 .json.gz de data/raw de Carrefour
#    y en esta máquina tarda >10 min. Los 782 `skipped` son los ficheros que tocan PostgreSQL:
#    tests/conftest.py los salta cuando no hay base (marcador ancho de 111 ficheros por
#    plataforma.api / plataforma.almacen / almacen / psycopg). Cuadra: 2.187 recogidos =
#    1.404 passed + 782 skipped + 1 deseleccionado.
.\.venv\Scripts\python.exe -m pytest -q --deselect "tests/test_fase2_f05_ficha_carrefour.py::test_contra_la_ficha_real"
```

Y las comprobaciones de datos, con las herramientas del harness sobre rutas relativas al proyecto:

- `data_profile` → `data/debug/auditoria-cobertura/cobertura_diaria.csv`
- `data_verify` sobre ese CSV con: `unique (fuente,fecha)`; `not-null fuente`, `not-null fecha`,
  `not-null filas_gold`; `range filas_gold >= 0`; `enum estado` con los seis valores
  `ok`, `captura_sin_run`, `captura_run_fallido`, `run_sin_captura`, `sin_captura_run_fallido`,
  `sin_captura`.
- `data_profile` → `data/debug/auditoria-cobertura/mercadona-2026-11-04.csv`
- `data_clean` (dryRun) sobre `cobertura_diaria.csv` con `trim` + `coerce-type` de fechas y números.

El script **no reimplementa la vara de cobertura**: esa sigue siendo
`uv run python -m projects.cesta.cobertura_diaria` (máximo de 30 días, 90 %). Aquí solo se mide
presencia, volumen y novedad.

---

## 9. Límites reales (lo que estos datos NO dicen)

1. **La puerta 28/30 no la cumplen las cinco cadenas.** Medido: **2/5** — Aldi 28/30 y Mercadona
   28/30 sí; **Carrefour 27/30, DIA 25/30, Alcampo 20/30 no**. Con `--exigir-dias 28` el script
   sale 1 y **no se ha rebajado el umbral**; sin esa bandera el script solo mide y sale 0,
   porque un hueco ya conocido no puede gritar todos los días (la lección del aviso de
   Alcampo). La declaración del Lead, que cuenta los 30 días **anteriores** al día, da el mismo
   cuadro (Alcampo 19/30, Aldi 28/30, Carrefour 27/30, DIA 25/30, Mercadona 28/30;
   `dias_sin_datos` 11, 2, 3, 5, 2). Si lo que se quería decir era «cada cadena tiene ≥28 días de
   captura en su histórico», eso **sí** se cumple: 43, 51, 53, 57 y 57 días.
2. **Convención de ventana.** Esta auditoría cuenta los 30 días **que acaban en el día** (incluye el
   4/11); `cobertura_diaria.py` y las declaraciones cuentan los **30 anteriores** (hasta el 3/11).
   Por eso Alcampo tiene 10 huecos aquí y 11 allí: capturó el 4/11 y no el 5/10. Las dos cifras son
   correctas; no se deben mezclar.
3. **Los huecos no son «los domingos».** En la ventana hay 13 fechas con algún hueco: 10-07 (mié),
   10-12 (lun), 10-15 (jue), 10-18 (dom), 10-20 (mar), 10-21 (mié), 10-22 (jue), 10-24 (sáb),
   10-25 (dom), 10-27 (mar), 10-28 (mié), 10-29 (jue) y 11-01 (dom). Solo **3 de 13** son domingos,
   y de los cuatro domingos de la ventana **tres tienen captura en al menos cuatro cadenas**
   (10-11 las cinco; 10-18 y 10-25 cuatro). El único día sin ninguna cadena de catálogo es el
   **2026-11-01**. El 10-07 faltaron 4 de las 5 cadenas (solo Carrefour capturó).
4. **La causa de cada hueco no está diagnosticada aquí.** Que un día no haya partición no dice si
   fue parada del pipeline, veto de cobertura o fallo de red. Lo que sí se mide: de los 15 días con
   pasadas fallidas, 8 son de Alcampo y el `runs.csv` guarda sus filas y errores. El 18/10 de
   Carrefour está documentado como resistencia de Cloudflare (`BACKLOG.md`, tarea 7); los demás no
   se etiquetan sin evidencia.
5. **«Desaparece» no es «retirado».** Un id de la captura anterior que hoy no está puede ser
   producto retirado, agotado, fuera de alcance o una captura incompleta. Esta auditoría **no
   certifica retiradas**.
6. **Novelty sobre gold no es la de la declaración.** Gold filtra por alcance y quita filas; se
   publica al lado con nombre explícito y no debe usarse como «la captura del día». Ejemplo medido:
   Alcampo 4/11, 943/4/303 en bronce vs 942/1/303 en gold.
7. **La muestra de bronce es una muestra.** 475 de 4.272 filas (1 de cada 9), suficiente para
   perfilar tipos y nulos, no para afirmar totales del catálogo. Además, el CSV infiere `ean` como
   número (en parquet es texto): puede perder ceros a la izquierda; el dato bueno sigue en el
   parquet.
8. **Sin red y sin base de datos.** No se ha consultado `GET /api/estado` ni Postgres: la
   verificación de que la API sirve `cobertura` para las 6 cadenas la hizo el Lead el 2026-11-04
   sobre `http://127.0.0.1:8080/api/estado`; no es una medición de esta auditoría.
9. **`data/` está fuera de git** (salvo tres scripts heredados de `data/debug/` que vienen de
   commits antiguos). El CSV, la muestra y el log no se commitean; sí el script y este
   documento. La reproducibilidad está en los comandos de la sección 8.

---

## 10. Estado de las declaraciones y verificación

- En `data/cobertura/` hay, comprobado en disco el 2026-11-04: **21 ficheros `lidl-*.json`**
  históricos (13/10–04/11) y **6 declaraciones con fecha del 4/11**: las cinco cadenas de catálogo
  (su `mtime` final es **18:54:57**, tras la última regeneración de la sesión; el manifiesto quedó
  con `mtime` 18:54:59 / `generado_en` 17:54:59Z) más Lidl (12:19, la escribe su colector). Esta
  auditoría **no las escribe**; las lee para contrastar. La auditoría se reejecutó a las 18:46
  (CSV y muestra); los tiempos cambian si se repite la pasada o se regeneran las declaraciones,
  y eso es normal: el dato es el contenido, que se verifica por recomputo y sha256.
- `verificar_evidencia.py` comprobó, en verde: el CSV tiene 150 filas, `(fuente,fecha)` único,
  estados dentro del enum, y la **novedad sobre bronce del 4/11 coincide exactamente** con la
  `novedad` declarada en los 5 JSON (nuevos/cambiados/desaparecen), además de las filas de bronce y
  el `mtime` de la partición.
- Verificación operativa de la API (`GET /api/estado` sirviendo `cobertura` para 6 cadenas):
  hecha por el Lead el 2026-11-04 sobre `http://127.0.0.1:8080/api/estado`. Esta auditoría, que no
  usa red, no la repite.

---

## 11. El ciclo que debe producir esto **todos los días**: estuvo roto y ya está arreglado

Todo lo anterior mide **el dato**; esto mide **el reloj que lo produce**, porque la petición era
«demuestra que produce datos nuevos todos los días» y un histórico diario no garantiza el mañana.

Medido el 2026-11-04 a las 17:47 con `Get-ScheduledTask` / `Get-ScheduledTaskInfo`, y
re-verificado sin cambios a las 19:05 (seguía en la ruta vieja, mismo código de error y misma
próxima ejecución):

| Qué | Valor medido (estado roto) |
|---|---|
| Tarea registrada | `Cesta diaria`, estado **Ready** |
| Disparadores | 3: diario 06:00, al arrancar (+3 min), al iniciar sesión (+2 min) |
| **Acción registrada** | `F:\aprendizaje\scrap\ejecutar.bat` (directorio de trabajo `F:\aprendizaje\scrap`) |
| **¿Existe esa ruta?** | **No.** `Get-Item F:\aprendizaje\scrap` no devuelve nada |
| Última ejecución | 2026-11-04 **15:31:14**, resultado **2147942667** = `0x80070003` (`ERROR_PATH_NOT_FOUND`) |
| Próxima ejecución | 2026-11-05 **05:00** |

**Qué pasó.** El proyecto se movió hoy de `F:\aprendizaje\scrap` a `F:\Proyectos\cesta`
(commit `b8425ae`, 14:20:35). El `ejecutar.bat` es portable (`cd /d "%~dp0"`), pero **la tarea
del Programador guarda la ruta absoluta** de cuando se registró. Las capturas de hoy
(11:19–12:58, en `runs.csv`) se hicieron **antes** del movimiento; el disparo de las 15:31 ya
encontró la ruta vacía. Es decir: **el histórico diario es real, y la automatización que lo
mantiene llevaba rota desde el movimiento de hoy**. Los huecos del §9 no se explican solo por
esto (son de días anteriores al movimiento).

**El arreglo lo hizo David, y está verificado.** Re-registrar la tarea desde la ruta nueva exige
**elevación** (la tarea corre con `RunLevel Highest`); el agente no podía (`Set-ScheduledTask`
devolvía «Acceso denegado»). David lo ejecutó en PowerShell como administrador:

```powershell
powershell -ExecutionPolicy Bypass -File F:\Proyectos\cesta\registrar-tarea.ps1
# -> Tarea 'Cesta diaria' registrada.
```

Medido después, el 2026-11-04 a las 19:18: acción `F:\Proyectos\cesta\ejecutar.bat`, directorio
`F:\Proyectos\cesta`, **3 disparadores** (diario 06:00, al arrancar, al iniciar sesión),
`State Ready`, `NextRunTime 2026-11-05 06:00`. Y se probó de punta a punta con un disparo manual
(`Start-ScheduledTask`): **`LastRunTime 19:18:35`, `LastTaskResult 0`** — el día ya estaba hecho,
así que `ejecutar.bat` salió al instante sin tocar la red, que es justo lo que tiene que hacer.

**Lo que esto significa para «todos los días».** Desde ahora el ciclo se lanza solo (06:00, o al
encender/iniciar sesión, con `StartWhenAvailable`); el histórico de que produce datos nuevos está
medido arriba (128/128 capturas escritas el mismo día, 124/128 con novedad). Ya no hay una
promesa que dependa de que alguien se acuerde de lanzarlo.

---

## 12. Lo que encontró la revisión adversarial, y cómo se corrigió

La revisión independiente (`docs/REVISION-COBERTURA-2026-11-04.md`) dio **APTO CON RESERVAS** y
encontró dos defectos reales y tres deudas. Esto es lo que se hizo después, con la prueba en
rojo→verde de cada uno (rojo = la prueba falla con el código de antes; verde = pasa con el de
después; el cronómetro de cada mutación está en la sesión, no aquí).

| Objeción | Qué estaba mal | Corrección y prueba (rojo → verde) |
|---|---|---|
| **O1** (alta) | `vs_anterior_pct` comparaba con la **captura más antigua** de la ventana: Alcampo publicaba +1,7 % cuando era +2,8 %; Aldi +6,8 % con el signo cambiado (−4,4 % real) | `veredicto` recorre el calendario en orden (la primera captura es la penúltima). Prueba con **dos capturas anteriores** (rojo: 340,0 % vs 10,0 %) y con un día sin captura. Regenerados los 5 JSON y el manifiesto: ahora +2,8 / −4,4 / −0,1 / 0,0 / −0,1 |
| **O1b** (menor) | `referencia_fecha` elegía el día **más viejo** entre los empatados al máximo (Aldi 30/10 y 31/10) | Se elige el **más reciente** (31/10). Prueba con el empate |
| **O2** (alta, operativa) | `DECISIONES.md` afirmaba «la pasada diaria ya lo hace sola» y la tarea del Programador estaba rota desde el movimiento (apuntaba a `F:\aprendizaje\scrap`) | Frase corregida en `DECISIONES.md` §5; **resuelto el 4/11 a las 19:18**: David re-registró la tarea como administrador y se verificó (acción nueva, 3 disparadores, disparo manual con `LastTaskResult 0`, próxima 5/11 06:00). Detalle en §11 |
| **O3a** (media) | `declara()` vivía dentro del `try` del emparejador: con `--sin-emparejar`, o si el emparejador fallaba, no se declaraba nada | Movida a su **propio `try`, antes del emparejador** (solo depende del bronce). Prueba de orden en el fuente: rojo si se mueve detrás del manifiesto (17761 < 16406 en la mutación) |
| **O3b** (media) | Los 5 ficheros se sustituían de uno en uno: un fallo a mitad dejaba 2 del día y 3 de ayer, y el manifiesto lo publicaba | Se escriben los 5 temporales y solo después se sustituyen; si falla uno, se borran los temporales y no se sustituye ninguno. Prueba forzando el fallo en el tercero: antes dejaba `aldi-2026-11-04.json` publicado, ahora no deja ninguno ni `.tmp` |
| **O4** (media) | La misma respuesta mezclaba `productos` (gold) y `cobertura.filas` (bronce) sin decirlo; `tipos.ts` lo documentaba al revés; `DECISIONES` simplificaba la diferencia de Aldi | La pantalla dice «**filas capturadas**»; comentario de `tipos.ts` corregido; Aldi explicado con sus 202 sin precio + 8 de alcance (aquí §4 y `DECISIONES` §5) |
| **O5** (media-baja) | La prueba del enganche era un `grep` (`.declara(` en el fuente) y no había contrato de `/api/estado` | Prueba de **orden** y de no depender del emparejador; prueba de **contrato del endpoint** montada sin PostgreSQL (duckdb en memoria y `AJUSTES` de prueba), rojo al quitar el merge de cobertura de `/api/estado` |
| **O4b** (menor) | `run_del_dia` comparaba el prefijo **UTC** de `runs.csv` con el día local: una pasada a las 00:30 de Madrid se perdería | Se convierte el `ts` a Europe/Madrid y se compara el día local; prueba con `23:30Z` = 5/11 en Madrid |
| **O6** (alta, encontrada en la verificación por dimensiones) | La sustitución de los 5 ficheros tampoco era atómica **en el renombrado**: si el tercer `os.replace` falla, los dos primeros ya son de hoy y quedan tres de ayer; el manifiesto publica una mezcla. La prueba de O3b solo cubría el fallo al preparar | Antes de sustituir se guarda el contenido anterior; si falla un renombrado se restaura lo ya sustituido y se borran los temporales. Prueba nueva forzando el fallo en el `os.replace` número 3: rojo (quedaban dos ficheros del día) → verde (los cinco vuelven a su contenido anterior, sin `.tmp`) |
| **O7** (media, criterio literal) | El contrato pedía una clave `huecos` y el JSON solo traía `dias_sin_datos` + `dias_en_la_ventana` | Se añade `huecos` (= `dias_sin_datos`) además de los dos números; prueba que exige la clave y su igualdad |
| **O8** (media) | Si `filas_por_dia()` no podía leer el bronce devolvía `{}` y las cinco declaraciones decían «sin datos» aunque la partición del día existiera: un fallo de medición se publicaba como ausencia de captura | Si la captura del día existe y tiene filas, el veredicto es `sin referencia` (con filas, y `pct`/`referencia` a `null`) y el aviso dice que no se pudo leer el histórico. Prueba con `filas_por_dia` vacío: rojo (decía «sin datos» con 2 filas en la captura) → verde |
| **O9** (media, revisión de fallos) | Si fallaba la **lectura** del contenido anterior (fichero bloqueado, el caso que cita el propio código), el diccionario se construía **fuera** del `try` y quedaban los cinco `.tmp` en `data/cobertura/` | La lectura entra en el `try`; el borrado de temporales va protegido para no tapar el fallo original. Prueba forzando el fallo de lectura: rojo contra `ccf145f` (quedaban `.tmp`) → verde |
| **O10** (media, revisión de fallos) | En la rama `sin referencia` el JSON mezclaba `filas: 2` con `huecos: 30`/`dias_sin_datos: 30`: números de una ventana que no se pudo leer | `huecos`, `dias_sin_datos` y `dias_en_la_ventana` van a `null` en esa rama; sin precio hoy tampoco se publica `pct: 0.0` ni `referencia: 0` (son números inventados) |
| **O11** (media, revisión de fallos) | Una partición que existe pero cuyo parquet es ilegible (`filas: 0`, `ficheros: 1`) seguía saliendo «sin datos» con «no hubo captura» al lado | Pasa a `sin referencia` con aviso propio: una partición ilegible no es una ausencia de captura. Prueba con parquet corrupto: rojo → verde |
| **O12** (media, revisión de fallos) | `run.py` llamaba a `declara()` sin fecha y el módulo usaba el reloj: una pasada que empieza a las 23:25 y acaba pasada la medianoche declaraba el día nuevo (vacío) en vez del capturado | `fecha_de_la_pasada` se fija al empezar la pasada y se pasa a `declara()`; prueba de orden/fuente contra `ccf145f`: rojo → verde |

Las cifras del documento no cambian con O1 (solo la «variación», que ahora se publica bien) y
siguen cuadrando con la revisión independiente.
