# Verificación de la ingesta diaria — 2026-11-09

**Medido el 2026-11-09 entre las 16:55 y las 17:10 (Europe/Madrid)**, leyendo del disco lo que
la pasada de la mañana ya dejó escrito. No se ha lanzado ninguna colección, no se ha hecho
ninguna petición a las cadenas y no se ha ejecutado `verificar_precios`. Todo lo que sigue está
en un fichero del repo o marcado explícitamente como **supuesto** o **pendiente**.

**Veredicto corto: AMARILLO.** Las seis cadenas tienen captura y partición de bronce del 9/11, el
gold del día está publicado (`v20261109-113939`, 11:39:39) y el vigilante de las 14:00 cerró con
**1 aviso y 0 fallos**. Lo que no está cerrado es la lectura del aviso de Alcampo: **el WAF no ha
vuelto a cortar la pasada** (no hubo `TargetClosedError`, el árbol terminó, 0 errores), pero la
cadena sale al **84,1 %** porque la vara es el 17/10, un día de árbol excepcionalmente profundo.

---

## 1. Tabla por cadena (pasada del 2026-11-09)

| Cadena | Pasada | Filas | Bronce | Vara (fecha) | % | Veredicto | Huecos 30 d | Gold del día |
|---|---|---:|---|---|---:|---|---:|---|
| Carrefour | 10:45 | 16.794 | 16.794 · 1 fichero · 10:45:41 | 16.816 (2026-11-08) | 99,9 | ok | 3/30 | 2026-11-09 |
| DIA | 10:06 | 5.693 | 5.693 · 1 fichero · 10:06:39 | 5.783 (2026-10-11) | 98,4 | ok | 4/30 | 2026-11-09 |
| Mercadona | 09:56 | 4.290 | 4.290 · 1 fichero · 09:56:45 | 4.286 (2026-11-08) | 100,1 | ok | 1/30 | 2026-11-09 |
| Aldi | 09:56 | 2.761 | 2.761 · 1 fichero · 09:56:36 | 2.951 (2026-10-31) | 93,6 | ok | 1/30 | 2026-11-09 |
| **Alcampo** | **11:32** | **23.562** | 23.562 · 1 fichero · 11:32:57 | 28.022 (2026-10-17) | **84,1** | **corta** | 9/30 | 2026-11-09 |
| Lidl | 09:55 | 82 | 82 · 1 fichero · 09:55:05 | — (alcance parcial) | — | ok (parcial) | — | 2026-11-09 |

Fuente: `data/avisos_ingesta.json` (generado 2026-11-09T14:00:02+01:00), `data/cobertura/*-2026-11-09.json`,
`data/vigilante.log` (entrada de las 14:00) y `data/runs.csv`.

- **Errores de catálogo:** Carrefour 1, resto 0. El de Carrefour es el crónico ya declarado:
  `cat32482101` (congelados/comidas-del-mundo/resto-del-mundo) devuelve HTTP 520 desde el 20/09/2026
  (`data/ejecuciones.log:18416-18417`). No es pérdida de datos de hoy.
- **Lidl** no tiene vara porque su alcance declarado es `ofertas_semanales_parcial`, no catálogo completo
  (`data/cobertura/lidl-2026-11-09.json`: 82 fichas leídas, 82 guardadas, 0 fuera de alcance).
- Las varas de DIA (11/10) y Aldi (31/10) son de hace semanas, no de ayer: el veredicto se mide
  contra el **máximo de los 30 días anteriores** (`projects/cesta/cobertura_diaria.py:75,101-157`),
  que puede ser de otro día. En Alcampo eso es justo lo que distorsiona (ver §3.4).

**Qué produjo el día** (novedad frente a la captura anterior, `data/cobertura/*-2026-11-09.json`):

| Cadena | Nuevos | Precios cambiados | Desaparecen |
|---|---:|---:|---:|
| Carrefour | 54 | 1.248 | 76 |
| DIA | 16 | 0 | 9 |
| Mercadona | 5 | 51 | 1 |
| Aldi | 0 | 59 | 63 |
| Alcampo | 282 | 31 | 33 |
| Lidl | — (alcance parcial) | — | — |

---

## 2. El gold del día

- **Versión publicada:** `20261109-113939`, `publicado_en` **2026-11-09T11:39:39.793660**
  (`data/gold/actual.json` y `data/avisos_ingesta.json`; log `data/ejecuciones.log:18505`).
- **Fecha del gold:** `2026-11-09`; las seis cadenas aparecen con `captura: 2026-11-09` y
  `de_hoy: true` en `data/gold/manifiesto.json` (fuentes: alcampo 23.562 · aldi 2.761 ·
  carrefour 16.794 · dia 5.693 · lidl 82 · mercadona 4.290).
- **Filas y ficheros de la versión** (`data/gold/manifiesto.json` → `ficheros`):
  `grupos.parquet` 53.182 · `enlaces.parquet` 23.161 · `precio_diario.parquet` **2.813.570** ·
  `precio_derivado.parquet` 2.813.570 · `resumen.parquet` 79.240 · `promos_por_cadena.parquet` 6.
  El puntero `actual.json` lleva la huella SHA-256 de los seis.
- **Histórico:** **2.813.570 filas y 64 días** acumulados (`2026-09-06`..`2026-11-09`, medido sobre
  `data/gold/precio_diario.parquet`).
- **Del día en `precio_diario`:** **52.917 filas** (alcampo 23.550 · carrefour 16.794 · dia 5.679 ·
  mercadona 4.244 · aldi 2.568 · lidl 82). No es una cadena que falte: silver tenía 53.182 filas y
  el pipeline declara **265 filas sin precio por unidad utilizable** (`data/ejecuciones.log:18474,18477-18478`).
  La diferencia bronce → `precio_diario` por cadena suma exactamente esas 265: Aldi 193,
  Mercadona 46, DIA 14, Alcampo 12, Carrefour 0, Lidl 0.
- **¿El día está completo?** Sí para el día: seis de seis cadenas con captura de hoy, las cinco de
  catálogo con cobertura declarada, Lidl con su alcance parcial declarado, manifiesto sin avisos y
  "nada del día se queda sin decir" (`data/ejecuciones.log:18676`). Lo que **no** está entero:
  - el catálogo de Alcampo frente a la vara del 17/10 (aviso `captura_corta`, §3);
  - en el histórico hay **un hueco previo, el 2026-11-01** (65 días de calendario, 64 con datos);
    no es de hoy y no lo he investigado en esta verificación;
  - Lidl es ofertas semanales, no catálogo: 82 fichas hoy frente a 91 los días 3–8/11
    (su `data/cobertura/lidl-2026-11-09.json` lo declara como cobertura parcial).

---

## 3. Alcampo y el WAF: ¿volvió a cortar hoy?

**No. Hoy el WAF no ha cortado la pasada de Alcampo.** Hubo retos (9 renovaciones de sesión) y
cortó la fase **complementaria** del buscador, pero el recorrido de categorías terminó, la captura
se guardó con 0 errores y el día se publicó. El 84,1 % **no** es un corte de hoy.

### 3.1 Qué pasó, con horas

| Hora local | Hecho | Evidencia |
|---|---|---|
| 09:54:47 | arranca la pasada de las 6 cadenas | `data/ejecuciones.log:18317-18318` |
| 09:55–10:45 | terminan Lidl (09:55), Aldi y Mercadona (09:56), DIA (10:06), Carrefour (10:45) | `data/runs.csv`; `data/vigilante.log:268-284` |
| 11:30:33 | el marcador de reanudación de Alcampo se pone a **0** = vuelta completa | `data/alcampo_por_donde_iba.txt` (contenido `0`) |
| 11:32:57 | bronce de Alcampo escrito: 23.562 filas, 0 errores | `data/bronze/fuente=alcampo/fecha=2026-11-09/part.parquet`; `data/alcampo_alcance.txt`; `data/runs.csv` |
| 11:39:39 | pipeline publica `v20261109-113939` | `data/gold/actual.json`; `data/ejecuciones.log:18505` |
| 14:00:02 | vigilante: AVISO, 1 aviso, 0 fallos | `data/avisos_ingesta.json`; tarea "Cesta vigilante" resultado 0 |

Duración de Alcampo: **5.877 s (1 h 38 min)** (`data/ejecuciones.log:18463`). El día anterior por
la mañana el WAF tumbó el navegador a los 486 s (`docs/RECUPERACION-ALCAMPO-2026-11-08.md` y
`data/ejecuciones.log:18063`); hoy no ha pasado nada parecido.

### 3.2 Los retos de hoy: 9, todos resueltos

En `data/ejecuciones.log:18345-18456` hay **27 líneas "el WAF ha saltado en …" = 9 cortes ×
(2 reintentos con la misma sesión + 1 renovación de cookie)** y **9 "sesion renovada (con_ventana)"**.
Las 9 categorías donde saltó: Té e Infusiones (1), Droguería Ecológica y sostenible (2), Lejías y
Amoníacos (3), Accesorios gatos (4), Queso mezcla curado (5), Tomate Frito (6), Galletas sin azúcar
añadido (7), Cervezas sin alcohol (8), Pasta de dientes (9). El último salto fue en la categoría ~370
de ~403; después el recorrido cerró en **400 categorías vistas** (en el último aviso de progreso
quedaban 3 en cola) y **28.967 filas crudas** antes de deduplicar (`data/ejecuciones.log:18455-18458`),
y el marcador se puso a 0 (11:30:33).

Comparación con lo normal: **9 renovaciones/día es la cifra habitual de una pasada que completa el
árbol** (los días completos de las últimas semanas van de 9 a 14; p. ej. 7/11: 9; 5/11: 11;
17/10: 14). Los días con menos renovaciones son capturas que se cortaron antes de terminar. No es
una escalada del WAF.

### 3.3 Lo que sí cortó el WAF: el barrido del buscador (fase complementaria)

Tras el árbol, el colector deduplicó: **28.967 filas → 24.175 productos**
(`data/ejecuciones.log:18458`). Como 24.175 queda por debajo del 95 % de la última captura buena,
entró en el barrido del buscador (`alcampo.py:891-897`): el WAF lo cortó en la primera petición —
**"buscador: 304 terminos, 0 productos nuevos, 0 terminos sin datos (0 min)"**
(`data/ejecuciones.log:18459-18461`). Después se quitaron **613 productos fuera de alcance** y
quedaron las **23.562** guardadas (`data/ejecuciones.log:18462-18463`).

Esto **no es un corte de la captura** (el propio código lo distingue: `alcampo.py:934-938`), y
además es el patrón de casi todos los días: desde el 27/9, **31 de las 42 jornadas con intento**
tienen al menos un corte de la fase de buscador, y hoy es una de ellas. Lo que aporta cuando
*no* lo cortan al principio es pequeño: desde el 27/9 el máximo fueron **247 productos nuevos**
(1/10); en el último mes, **239** (31/10). No es el mecanismo que explica 4.400 productos de
diferencia.

### 3.4 Por qué sale 84,1 %: la vara es un día atípico, no un corte

El veredicto compara con el **máximo de los 30 días anteriores**, y ese máximo es el **17/10
(28.022)**. Cifras medidas:

| Lectura del mismo 23.562 | Valor | % |
|---|---:|---:|
| Contra ayer (8/11: 23.313) | +1,1 % | — |
| Contra el 2.º mayor de la ventana (30/10: 24.297) | — | **97,0 %** |
| Contra la mediana de la ventana (21 capturas, mediana 22.905) | — | **102,9 %** |
| Contra el máximo de la ventana (17/10: 28.022) | — | **84,1 %** |

Qué tenía el 17/10 de especial (medido en `data/ejecuciones.log:9901-10106` y en los parquets):

| | 2026-10-17 | 2026-11-09 |
|---|---:|---:|
| Categorías visitadas | **560** | **400** |
| Filas crudas antes de deduplicar | 34.628 | 28.967 |
| Productos únicos tras deduplicar | **28.754** | **24.175** |
| Productos fuera de alcance (no se guardan) | 798 | 613 |
| Productos en bronce | **28.022** | 23.562 |
| Peticiones a `compraonline.alcampo.es` | 630 | 433 |
| Ficheros de crudo | 579 | 397 |
| Duración | 10.494 s | 5.877 s |
| Aportación del barrido del buscador | 66 productos (y también cortado por el WAF) | 0 |

O sea: **la diferencia de ~4.500 productos está en el árbol de categorías, no en el buscador.**
El 17/10 se visitaron 160 categorías más y salieron 4.579 productos únicos más. El propio código ya
lo tenía documentado antes de hoy (`projects/cesta/cobertura_diaria.py:120-124`): *"el 17 de octubre
de 2026 Alcampo trajo 28.022 cuando lo normal era 22.800-24.300, y desde entonces una captura de
23.416 — normal, y mejor que la de ayer — sale «corta» todos los días"*. Y el 24/09 pasó algo
parecido: 540 categorías, 28.977 productos, 5.442 s (`data/runs.csv` y comentario de `alcampo.py:367-386`).

**Conclusión de §3:** hoy no hay corte del WAF sobre la pasada. El 84,1 % mide que la captura de
hoy es la normal del recorrido actual (~23–24 k) contra un máximo excepcional de un día en el que el
árbol se recorrió mucho más profundo. La vara no se baja sola: es una decisión registrada
(`cobertura_diaria.py:120-124`), no un fallo de hoy.

### 3.5 Qué hizo y qué **no** hizo el automatismo de recuperación

- **No se disparó, porque no había nada que recuperar.** El bronce del 9/11 existe y la pasada de
  hoy consta `ok=true` en `data/runs.csv`; `necesita_recuperar()` sale falso por las dos vías
  (`scripts/recuperar_alcampo.py:61-72`).
- No hay marca de intento: **no existe `data/recuperacion-alcampo-2026-11-09.txt`** (la del 8/11 sí:
  *"intento de recuperacion de alcampo 2026-11-08; codigo 0"*).
- `ejecutar-vigilante.bat` solo llama al recuperador si la vigilancia devuelve fallo; la de las
  14:00 salió 0 (tarea "Cesta vigilante", resultado 0) y en `data/vigilante.log` no hay ninguna
  línea del recuperador (ni "nada que recuperar" ni "recuperando"), así que ni se invocó.
- Comprobación en seco, sin lanzar nada: `python -m scripts.recuperar_alcampo --no-lanzar` →
  *"nada que recuperar: Alcampo tiene bronce o no hay crudo de hoy"*, código de salida 0.
- **No hizo** por tanto: no relanzó Alcampo, no hizo peticiones de red, no tocó el bronce ni el gold,
  no escribió ningún aviso nuevo. `data/INGESTA-DETENIDA.txt` no existe y `data/avisos_ingesta.log`
  no tiene entradas de hoy (la última es del 8/11).

### 3.6 Lo que **no** está medido (pendiente, no supuesto)

- **Por qué** hoy el recorrido visitó 400 categorías y el 17/10, 560. Candidatos: cambio del árbol
  de categorías de Alcampo o cambio de alcance/configuración. El fichero que registra el alcance
  (`data/alcampo_alcance.txt`) **solo existe desde el 4/11**, así que el alcance del 17/10 no está
  registrado. El crudo del 17/10 **sí está** (579 ficheros en `data/raw/fuente=alcampo/fecha=2026-10-17`),
  así que se puede comparar la respuesta de categorías de ese día con la de hoy si hace falta cerrar
  el diagnóstico del todo. No lo he hecho en esta verificación: no era necesario para responder si
  el WAF cortó hoy.
- La propuesta del 7/11 de subir la espera del WAF de 60 a 120–180 s sigue sin aplicarse
  (`docs/DIAGNOSTICO-ALCAMPO-2026-11-07.md` §4). Hoy no habría cambiado nada: los 9 retos se
  resolvieron con el mecanismo actual.

---

## 4. Veredicto operativo y siguientes acciones

**Veredicto: AMARILLO.** Día verde en ingesta (6/6 cadenas, gold publicado, 0 fallos, ninguna
excepción registrada en `data/errores.log`) y amarillo en la señal de Alcampo (aviso esperado pero
mal calibrado y un mecanismo de reserva —el barrido— que en la práctica no funciona).

Acciones que propongo, por orden:

1. **Decidir la vara de Alcampo (David / nivel 2-3).** El aviso `captura_corta` lleva 6 días
   consecutivos midiendo contra el máximo del 17/10 (4/11: 83,6 %; 5/11: 81,4 %; 6/11: 81,6 %;
   7/11: 81,5 %; 8/11: 83,2 %; 9/11: 84,1 %). Opciones, sin tocar código todavía: (a) mantener el
   máximo como vara pero añadir al aviso la mediana y el 2.º mayor —hoy daría 102,9 % y 97,0 %—;
   (b) cambiar la referencia a la mediana de la ventana; (c) dejar el veredicto y quitar el aviso
   cuando la captura supere la mediana. Cualquiera de las tres evita que el panel diga "corta"
   todos los días. **No he cambiado nada**: es una decisión de producto.
2. **Decidir el barrido del buscador (N30).** Hoy aportó 0 productos y lo cortó el WAF al empezar;
   desde el 27/9 lo ha cortado el WAF en 31 de las 42 jornadas con intento y, cuando no, aportó
   0–247 productos. O se le da una vía que no compita con el WAF (sesión/ritmo propios), o se retira
   la promesa de que es la red de seguridad del hueco de Alcampo. Evidencia para decidir:
   `data/ejecuciones.log:18459-18461` (hoy) frente a `:10099-10103` (17/10).
3. **No relanzar Alcampo hoy y dejar correr la vigilancia.** No hay error, el crudo está completo y
   relanzar solo repetiría el mismo recorrido (no aplica `ejecutar.bat --forzar`, que es para
   capturas fallidas). Seguir el vigilante de las 20:00 y la pasada de mañana a las 06:00. Si mañana
   Alcampo repite ~23,5 k, el diagnóstico queda cerrado: **es el techo normal del recorrido actual,
   no el WAF**. Dato útil para no alarmarse el 17/11: ese día el 17/10 sale de la ventana de 30 días
   y, si no aparece antes una captura mayor, la referencia pasará a 24.297 (30/10) y el mismo ~23,5 k
   dará ~97 % sin que haya cambiado nada en la captura.

---

## 5. Evidencia usada y método

**Ficheros leídos (rutas completas):**

| Ruta | Para qué |
|---|---|
| `data/avisos_ingesta.json` | informe del vigilante de las 14:00: pasadas, bronce, referencia, %, veredicto, gold |
| `data/vigilante.log:268-286` | entrada de las 14:00: AVISO, 1 aviso, 0 fallos |
| `data/ejecuciones.log:18317-18681` | pasada del 9/11 completa (WAF, dedupe, barrido, pipeline, cobertura) |
| `data/ejecuciones.log:9901-10273` | pasada del 17/10 (el día de la vara) |
| `data/ejecuciones.log:17544-17790` y `:18026-18316` | 7/11 (reto que sí cortó) y 8/11 (`TargetClosedError`) |
| `data/cobertura/{alcampo,aldi,carrefour,dia,mercadona,lidl}-2026-11-09.json` | filas, vara, %, huecos, novedad |
| `data/cobertura/alcampo-2026-11-04..09.json` | serie de los 6 días con aviso de Alcampo |
| `data/gold/actual.json`, `data/gold/manifiesto.json` | versión, fecha, ficheros, filas, fuentes, cobertura |
| `data/gold/precio_diario.parquet` | 2.813.570 filas, 64 días, 52.917 filas del 9/11 |
| `data/bronze/fuente=*/fecha=*` | recuento real por fecha (sin usar los JSON) |
| `data/runs.csv` | última pasada por cadena (filas, errores, segundos, ok) |
| `data/peticiones/alcampo-2026-11-09.json` y `…-10-17.json` | peticiones (433 y 630) |
| `data/raw/fuente=alcampo/fecha=2026-11-09` y `…-10-17` | ficheros de crudo (397 y 579) |
| `data/alcampo_por_donde_iba.txt`, `data/alcampo_alcance.txt` | marcador a 0 (vuelta completa) y alcance |
| `data/avisos.json`, `data/avisos_ingesta.log`, `data/errores.log` | avisos de precio (0), sin entradas hoy salvo las del 8/11 |
| `scripts/recuperar_alcampo.py`, `projects/cesta/collectors/alcampo.py`, `core/waf.py`, `projects/cesta/cobertura_diaria.py` | lógica de recuperación, WAF, barrido y veredicto |

**Comprobaciones hechas:** recuento de filas por fecha en bronce y gold con Polars en modo lectura;
conteo por día de las señales del WAF en `ejecuciones.log` (saltos, renovaciones, corte del buscador,
`TargetClosedError`); `python -m scripts.recuperar_alcampo --no-lanzar` (no lanza nada); consulta de
las tareas programadas con `Get-ScheduledTask`/`Get-ScheduledTaskInfo`.

**Tareas de Windows (medidas hoy):** "Cesta diaria": estado Ready, última 09/11 09:59:54, resultado 0,
próxima 10/11 06:00; disparadores 06:00 + al arrancar + al iniciar sesión. "Cesta vigilante": última
09/11 14:00:01, resultado 0, próxima 09/11 20:00; disparadores 08:00, 14:00, 20:00 e inicio de sesión.

**Cabos sueltos:**
- La tarea "Cesta diaria" registra última ejecución a las **09:59:54**, pero la pasada abre en el log
  a las **09:54:47**. No lo he podido atribuir: el historial operativo del Programador de tareas no
  tiene eventos de hoy para estas tareas. No afecta a ningún dato (la recolección fue una sola, de
  09:54 a 11:40).
- `data/ejecuciones.log` **no contiene la salida del relanzamiento de Alcampo del 8/11** (el que
  recuperó 23.313): no hay ningún bloque suyo en `ejecuciones.log` ni en `vigilante.log`. El
  resultado sí está en `data/runs.csv` (16:50:59, 23.313 filas, 0 errores, 6.163 s) y en
  `data/recuperacion-alcampo-2026-11-08.txt`. La vía exacta por la que se lanzó no está registrada.

## 6. Cómo rehacer estas medidas (para el siguiente agente)

Todo es lectura; no hace falta red.

```powershell
Get-Content data\avisos_ingesta.json -Raw | ConvertFrom-Json          # cuadro del vigilante
Import-Csv data\runs.csv | Where-Object { $_.ts -like '2026-11-09*' }  # pasadas de hoy
Select-String -Path data\ejecuciones.log -Pattern '^#{3,} 2026-11-09'  # linea del bloque de hoy
Get-Content data\gold\manifiesto.json -Raw | ConvertFrom-Json         # version publicada
# filas por fecha de bronce/gold (Polars del venv del proyecto, solo lectura):
.\.venv\Scripts\python.exe -c "import polars as pl, pathlib; [print(p.parent.name, pl.read_parquet(p).height) for p in sorted(pathlib.Path('data/bronze/fuente=alcampo').glob('fecha=*/part.parquet'))]"
# ¿tocaría recuperar Alcampo? (no lanza nada con --no-lanzar)
.\.venv\Scripts\python.exe -m scripts.recuperar_alcampo --no-lanzar
```

Para contar las señales del WAF por día, recorrer `data/ejecuciones.log` llevando la fecha de la
última cabecera `############ AAAA-MM-DD` y contar `el WAF ha saltado`, `sesion renovada`,
`el WAF corta la fase de buscador` y `TargetClosedError`.
