# La ingesta se vigila sola — 2026-11-05

**Medido el 2026-11-05 entre las 11:27 y las 11:38 (hora de Madrid), con la tarea `Cesta diaria`
EN MARCHA**: la pasada de hoy empezó a las 10:14 y a esa hora Carrefour iba por la categoría 550
de 596 y Alcampo por la 340 con 55 en cola. No se ha lanzado, ni parado, ni tocado nada de la
cadena: este trabajo es **sólo lectura local** más un fichero propio (`data/avisos_ingesta.json`).

Instrumento: `scripts/vigilar_ingesta.py`. Pruebas: `tests/test_vigilar_ingesta.py` (17, verdes).
Nada de red y nada de PostgreSQL: se lee lo que la cadena ya dejó en disco.

---

## 1. La pregunta, y por qué no la contestaba nadie

El punto 3 del encargo de David es una frase con tres partes:

> «la ingesta sigue sola y sin errores; avisos si falla»

Se puede descomponer en tres preguntas concretas, y hasta hoy **ninguna se contestaba sola**:

1. **¿Sigue sola?** ¿la tarea programada sigue lanzando la cadena y los días siguen cerrando, o
   lleva tres días sin cerrar ninguno y nadie se ha enterado?
2. **¿Sin errores?** ¿cada cadena trajo lo que esa cadena sabe traer, y llegó a gold?
3. **¿Avisa si falla?** ¿alguien se entera de un fallo **sin abrir nueve ficheros a mano**, que
   es exactamente lo que no se hace el día que uno está liado?

Lo que había escrito estaba bien y era suficiente; lo que faltaba era **leerlo junto**. Nueve
sitios, nueve formatos, y ninguno habla de los otros:

| Dónde | Quién lo escribe | Qué dice |
|---|---|---|
| `data/runs.csv` | `core/runlog.py` en cada colector | una fila por pasada: `ts` (UTC), filas, errores y **`ok`, que lo decide el colector** |
| `data/ultima_ejecucion.txt` | `ejecutar.bat` | el último día que **llegó a cerrarse** (0 o 3) |
| `data/ejecucion_en_curso.txt` | `run.py` | que hay una pasada empezada; se borra sólo si termina entera |
| `data/bronze/fuente=*/fecha=*/` | el pipeline | la captura del día, en particiones |
| `data/gold/precio_diario.parquet` | el pipeline / el emparejador | qué precios, de qué cadena y de qué día hay publicados |
| `data/gold/actual.json` | `core/publicacion.py` | qué **versión** está publicada y cuándo |
| `data/cobertura/<cadena>-<día>.json` | `cobertura_diaria.declara` | lo que cada cadena mide de su día |
| `data/avisos.json` | el paso de avisos (`projects.cesta.avisos`) | cuántos avisos saltaron, o que no se pudieron mirar |
| `metricas-cesta.json` | el paso de métricas | lo que lee el panel de David |

Y dos modos de fallo que este proyecto ya tiene documentados, para que no se repitan:

- **La cadena que no trae nada y nadie lo dice.** Alcampo no dejó una sola captura del 2 al 5 de
  octubre de 2026. `verificar_ingesta` comprueba coherencia —lo que la cadena declaró, lo que
  guardamos— y una cadena que no llega a declarar nada es coherente consigo misma.
- **La captura corta que se convierte en la vara.** Alcampo bajó de 37.019 filas a 24.120 en dos
  días sin que ninguna rama se hundiera de golpe: todas bajaron un poco, y el control que compara
  con «ayer» tomó la captura corta como referencia. De ahí que la referencia sea el máximo de 30
  días (`cobertura_diaria.veredicto`) y no la de ayer.

Lo que este vigilante añade es la tercera pata, que no existía: **la del día que no cierra**. Un
`ultima_ejecucion.txt` de hace tres días, una marca de ejecución que se quedó puesta o un
`avisos.json` de ayer son cosas que hoy sólo se ven si alguien las va a mirar.

---

## 2. Qué vigila: nueve chequeos

Seis por cadena (seis cadenas: las cinco de catálogo y Lidl) y tres del día entero. La «gravedad»
no es un adorno: **un fallo es algo que debería haber pasado y no pasó**; un aviso es algo que no
cuadra y puede ser transitorio (una pasada en marcha, una cobertura que se declara al final, una
captura que se quedó corta).

| # | Chequeo | De dónde lo lee | Fallo cuando | Aviso cuando |
|---|---|---|---|---|
| 1 | la pasada del día | `runs.csv`, `ts` en UTC pasado a Madrid | no hay fila de esa cadena ese día | la pasada está en marcha y aún no ha llegado a esa cadena |
| 2 | el `ok` del colector | `runs.csv` | `ok=False` | — |
| 3 | la pasada trajo algo | `runs.csv` | `ok=True` y 0 filas | — |
| 4 | la partición de bronce del día | `bronze/fuente=*/fecha=*/` | hay pasada y no hay parquet | — |
| 5 | filas contra su referencia | `veredicto` de `cobertura_diaria` | — | el veredicto dice `corta` |
| 6 | su precio en gold | `gold/precio_diario.parquet` | no tiene ninguna fecha | se quedó atrás respecto a la versión publicada |
| 7 | el gold del día | `gold/precio_diario.parquet` + `gold/actual.json` | la pasada cerró y gold sigue en otro día | la pasada está en marcha |
| 8 | la cobertura declarada del día | `data/cobertura/<cadena>-<día>.json` | — | falta la de alguna cadena |
| 9 | los avisos que se quedan callados | `avisos.json`, `ejecucion_en_curso.txt`, `ultima_ejecucion.txt`, `metricas-cesta.json` | — | ver el §5 |

Cuatro decisiones que hay que poder discutir, y por qué son así:

**El `ok` se lee, no se reinterpreta.** No es «cero errores»: es lo que decide el colector.
Carrefour tiene siempre cuatro o cinco categorías rotas y su día es correcto; durante diecinueve
ejecuciones `ok` se calculó como `errores == 0` y por eso **ninguna** de sus pasadas constaba como
buena y su aviso de deriva nunca estuvo armado. Aquí se lee la columna y se acabó.

**Lidl no se compara contra el máximo.** Son ofertas semanales parciales: 108 productos el 31/10,
82 el 2/11 y 91 el 3/11 y el 4/11 (medido en `data/bronze`). Comparadas contra el máximo de 30 días
saldrían «cortas» casi todos los días, que es la clase de aviso que enseña a no leer los avisos. Se
vigila igual —pasada, `ok`, bronce, gold— pero sin comparación de filas. **La lista de las que sí se
comparan no la decide este fichero**: es `cobertura_diaria.FUENTES`, la misma que usa el manifiesto
de publicación.

**Las ausencias no se cuentan dos veces.** Si una cadena no dejó ni fila en `runs.csv`, el informe
dice «no hay pasada» y no añade «no hay bronce»: es la misma cosa contada dos veces, y un informe
que repite se deja de leer. El bronce sólo se exige cuando la cadena consta como corrida — que es
el caso que de verdad hay que cazar: **el colector dijo que fue bien y no guardó nada**.

**La marca de ejecución cambia el veredicto, no lo esconde.** Si `ejecucion_en_curso.txt` es de
hoy, lo que aún no ha llegado es «en curso» (aviso) y no «no vino» (fallo). Si es de un día
anterior, esa pasada **murió**: eso es un aviso con nombre propio, porque `run.py` lo único que
hace es imprimirlo en el log de la siguiente pasada. Y si se está reconstruyendo un día pasado con
`--fecha`, la marca de ese día se da por viva: no hay reloj con el que compararla sin inventárselo.

---

## 3. Cómo se ejecuta

```
.\.venv\Scripts\python.exe -m scripts.vigilar_ingesta
```

Sale **0** si todo está bien y **1** si hay algún aviso o algún fallo. **Un fallo no detectable
también sale 1**: si no hay `runs.csv`, ni bronce, ni gold, el informe es un fallo, no un
silencio. Un vigilante que no puede mirar y contesta que sí es peor que no tenerlo.

Opciones:

```
.\.venv\Scripts\python.exe -m scripts.vigilar_ingesta --json          # el informe en JSON por stdout
.\.venv\Scripts\python.exe -m scripts.vigilar_ingesta --fecha 2026-11-04   # reconstruir ese día
.\.venv\Scripts\python.exe -m scripts.vigilar_ingesta --datos <carpeta>    # otra carpeta de datos
```

Siempre deja el informe en **`data/avisos_ingesta.json`** (temporal y renombrado atómico: un
fichero a medias se leería como un informe válido). `--fecha` reescribe ese mismo fichero con el
informe del día que se pida; para mirar un día pasado sin pisar el de hoy, se llama a
`vigilar_ingesta.vigila(fecha=...)`, que no escribe nada.

Tarda unos **4 segundos** (4,1 s medidos con el informe por pantalla; 6,3 s la primera vez, con el
parquet de gold sin cachear): 1,3 s se van en importar `polars` a través de `cobertura_diaria`,
0,6 s en recorrer los ~180 parquet de bronce leyendo sólo metadatos y 0,1 s en el parquet de gold
con duckdb.

En una consola de Windows sin UTF-8, `✓` y `✗` salen mal: `ejecutar.bat` ya pone `PYTHONUTF8=1`,
y a mano se arregla con `set PYTHONIOENCODING=utf-8` (el propio script lo intenta reconfigurando
su salida, y si no puede escribe sin ellos en vez de reventar).

---

## 4. Cómo se lee

Esto es la salida de verdad, la de hoy a las 11:38, con la pasada en marcha:

```
vigilante de la ingesta - 2026-11-05 (11:38, Europe/Madrid)
  la pasada del 2026-11-05 esta en marcha: lo que aun no ha llegado se lee como "en curso", no como "no vino"

    CADENA       PASA    FILAS   BRONCE   REFERENCIA      GOLD
  ✗ carrefour      --       --       --   en curso        2026-11-04
        ✗ [en_curso] aviso: la pasada del 2026-11-05 empezo el 2026-11-05 10:14 y aun no ha llegado a esta cadena
  ✓ dia         10:26    5.704    5.704   5.842 (97.6 %)  2026-11-04
  ✓ mercadona   10:16    4.267    4.267   4.320 (98.8 %)  2026-11-04
  ✓ aldi        10:15    2.709    2.709   2.951 (91.8 %)  2026-11-04
  ✗ alcampo        --       --       --   en curso        2026-11-04
        ✗ [en_curso] aviso: la pasada del 2026-11-05 empezo el 2026-11-05 10:14 y aun no ha llegado a esta cadena
  ✓ lidl        10:14       91       91   alcance parcial 2026-11-04

  EL DIA
  ✗ gold: precio_diario hasta el 2026-11-04, publicada la 20261104-144138
        ✗ [gold_pendiente] aviso: gold sigue en el 2026-11-04: la pasada del 2026-11-05 aun no ha publicado
        ✗ [cobertura_sin_declarar] aviso: falta la cobertura declarada del 2026-11-05 de 5 cadena(s): carrefour, dia, mercadona, aldi, alcampo (se declara al cerrar la pasada)
        ✗ [avisos_de_ayer] aviso: los avisos de la cadena son del 2026-11-04: los del 2026-11-05 no se han mirado (se miran al cerrar la pasada)

  ESTADO: AVISO - 5 aviso(s), 0 fallo(s)
  Todo lo que se esperaba esta, pero algo no cuadra: se lee el motivo de cada linea.

  informe dejado en F:\Proyectos\cesta\data\avisos_ingesta.json
```

- **`✓` / `✗` por cadena**: ✓ cuando no hay nada que decir de esa cadena, ✗ cuando hay algo.
- Cada motivo lleva **su gravedad escrita** (`aviso` o `fallo`) y un **código entre corchetes**,
  que es el mismo que viaja en el JSON y el que se busca cuando se engancha a algo.
- La columna **REFERENCIA** es el máximo de los 30 días anteriores y el porcentaje del día contra
  él; «alcance parcial» es Lidl y «en curso» es una cadena a la que la pasada aún no ha llegado.
- La columna **GOLD** es la última fecha de esa cadena en `precio_diario.parquet`, que es lo que
  se puede comparar y publicar.
- **`EL DIA`** es lo que no es de ninguna cadena: el gold publicado, la cobertura, la nota de
  avisos, la marca del día.

El JSON tiene la forma acordada y unas cuantas cosas más, para que lo pueda leer un programa:

```json
{
 "fecha": "2026-11-05",
 "estado": "aviso",
 "generado": "2026-11-05T11:38:43+01:00",
 "en_curso": true,
 "cadenas": [{"fuente": "dia", "estado": "ok", "pasada": {...}, "bronce": {...},
              "referencia": {...}, "gold": "2026-11-04", "motivos": []}],
 "avisos": [{"codigo": "gold_pendiente", "gravedad": "aviso", "cadena": null,
             "texto": "gold sigue en el 2026-11-04: la pasada del 2026-11-05 aun no ha publicado"}],
 "gold": {"fecha_max": "2026-11-04", "version": "20261104-144138",
          "publicado_en": "2026-11-04T14:41:38.061993"},
 "cobertura": {"declaradas": ["lidl"], "faltan": ["carrefour", "dia", "mercadona", "aldi", "alcampo"]}
}
```

`estado` es `ok`, `aviso` o `fallo`; gana el peor. `avisos` sólo lleva lo que no está bien (si está
vacío, el día está limpio). `referencia` es **literalmente** lo que devolvió
`cobertura_diaria.veredicto`, sin recalcular nada.

---

## 5. Cada aviso, qué significa y qué se mira

| Código | Gravedad | Qué significa | Qué se mira |
|---|---|---|---|
| `en_curso` | aviso | la pasada del día está en marcha y aún no llegó a esa cadena | nada: se espera. Si sigue así dos horas, el log |
| `sin_pasada` | **fallo** | esa cadena no corrió ese día: no hay fila en `runs.csv` | `data/ejecuciones.log` de hoy y `data/errores.log` |
| `pasada_no_ok` | **fallo** | corrió y el colector no la dio por buena | `errores.log` y la línea de esa cadena en el log de hoy |
| `pasada_sin_filas` | **fallo** | `ok=True` con cero filas (contradicción del propio registro) | la captura de esa cadena y el log |
| `sin_bronce` | **fallo** | hay pasada y no hay parquet del día | si el colector se negó a escribir, o si escribió en otro sitio |
| `captura_corta` | aviso | el día no llega al 90 % del máximo de 30 días | la referencia (viene en el motivo) y la tendencia de esa cadena |
| `cadena_sin_gold` | **fallo** | esa cadena no tiene ni una fecha en gold | el pipeline y el alcance de esa cadena |
| `cadena_gold_atrasada` | aviso | su gold se quedó atrás respecto a la versión publicada | el pipeline para esa cadena |
| `sin_gold` | **fallo** | no hay `precio_diario.parquet`, no se puede leer o no tiene ni una fila | el pipeline |
| `gold_pendiente` | aviso | la pasada está en marcha y gold sigue en el día anterior | nada: se espera al cierre |
| `gold_atrasado` | **fallo** | la pasada cerró y gold sigue en otro día | el pipeline y `data/gold/actual.json` |
| `sin_version` | aviso | no se puede leer `gold/actual.json` | la publicación |
| `cobertura_sin_declarar` | aviso | falta la cobertura del día de alguna cadena | `cobertura_diaria.declara`, que corre tras el pipeline |
| `sin_dia_cerrado` | aviso | no hay `ultima_ejecucion.txt` | si la cadena llegó a correr alguna vez |
| `marca_ilegible` | aviso | `ultima_ejecucion.txt` no es una fecha | el fichero (lo escribe `ejecutar.bat`) |
| `cadena_parada` | aviso | el último día cerrado es de anteayer o antes | **lo primero**: ¿sigue lanzándose la tarea? |
| `pasada_a_medias` | aviso | la marca de ejecución es de otro día: esa pasada murió | el final del log de ese día |
| `avisos_sin_mirar` | aviso | `avisos.json` no está, o dice que no se pudo mirar (sin base) | si PostgreSQL está alcanzable; si no, es lo esperado |
| `avisos_de_ayer` | aviso | la nota de avisos es de otro día | el paso de avisos al final de la cadena |
| `metricas_atrasadas` | aviso | `metricas-cesta.json` es de anteayer o antes | `projects.cesta.metricas` |
| `informe_sin_escribir` | aviso | no se pudo dejar `avisos_ingesta.json` | permisos o antivirus en `data/` |

---

## 6. El enganche a la cadena diaria — **propuesto, no aplicado hoy**

Hoy **no se ha enganchado nada**, y es a propósito: hay una ingesta corriendo y tocar
`ejecutar.bat` o `run.py` en este momento es exactamente lo que no hay que hacer. Lo que sigue es
el cambio, con la línea exacta, para aplicarlo cuando la pasada haya cerrado.

### La opción recomendada: dos líneas en `ejecutar.bat`

Al final de `ejecutar.bat`, **después** del `powershell ... -Tail 24` y **antes** de
`exit /b !CODIGO!`:

```bat
REM El vigilante de la ingesta: informe, data\avisos_ingesta.json y codigo 0/1.
REM Su codigo NO cambia el del dia: un aviso no puede convertir un dia bueno en fallido.
uv run python -m scripts.vigilar_ingesta >> "data\ejecuciones.log" 2>&1
if !errorlevel! neq 0 echo Cesta: el vigilante ha visto algo; mira data\avisos_ingesta.json
```

(El intérprete es el mismo que usa la línea de arriba, `uv run python`, que es el del `.venv`;
`.\.venv\Scripts\python.exe -m scripts.vigilar_ingesta` es la misma cosa sin pasar por `uv`.)

**Por qué ahí y no en `run.py`:** `ejecutar.bat` es el único sitio que sigue vivo cuando `run.py`
**se muere**. Si el proceso se cae a mitad —lo que ya pasó el 21 de septiembre de 2026, con
Carrefour por la categoría 525 de 651 y Alcampo por la 250—, el `.bat` sigue, el vigilante ve la
marca de ejecución puesta, y saca `pasada_a_medias` y las cadenas que faltan. Colgado de `run.py`,
ese caso no se cuenta nunca: el que tenía que avisar es el que se murió.

Y las dos razones por las que **no** se propaga su código de salida: el código del día lo decide
`run.py` (`_veredicto`), y un aviso de cobertura no puede hacer que se reintenten noventa minutos
de red —la misma doctrina que ya siguen `cobertura_diaria` y `verificar_docs` en esa cadena.

### La otra opción: cuatro líneas en `run.py`

Si se prefiere que el informe salga etiquetado en el log, como los demás pasos, va en `_main()`,
**entre `quita_la_marca()` y `return _veredicto(resultados, fallos)`** — después de quitar la
marca, para que el vigilante no crea que la pasada sigue en marcha cuando ya ha cerrado:

```python
    # El vigilante: dice en una pantalla lo que hasta hoy habia que ir leyendo por nueve sitios.
    # Va con `[]` por lo mismo que los demas pasos, y su codigo no cambia el del dia.
    try:
        importlib.import_module("scripts.vigilar_ingesta").main([])
    except Exception as exc:  # noqa: BLE001
        print(f"[vigilante] no se pudo mirar la ingesta: {exc}")
```

Lo que se pierde: si `run.py` muere antes de llegar ahí, no hay informe (la marca se queda puesta y
lo dice la pasada siguiente). **No se ponen las dos**: serían dos informes del mismo día.

### Lo que sigue sin cubrirse, y se dice

Ni el `.bat` ni `run.py` pueden avisar de lo que nunca se lanzó: si el Programador de tareas deja
de disparar `ejecutar.bat`, ese día no escribe nada y sólo lo caza el chequeo `cadena_parada`
**cuando alguien ejecuta el vigilante**. Para cubrirlo haría falta una segunda tarea programada
(por ejemplo a las 23:00) que lance el vigilante — y eso no se instala hoy ni se da por hecho aquí.

---

## 7. Las pruebas (rojo → verde)

```
.\.venv\Scripts\python.exe -m pytest tests/test_vigilar_ingesta.py -q
```

**17 pruebas, todas con datos sintéticos en `tmp_path`** — `bronze/fuente=*/fecha=*/`, `runs.csv`,
`precio_diario.parquet`, `actual.json`, `cobertura/`, la marca y la nota de avisos, montados
fichero a fichero. Ni el `data/` de verdad, ni PostgreSQL: una prueba que mira el disco real mide
el calendario, no el código.

Las cuatro que pedía el encargo, y qué afirman exactamente:

| Prueba | Qué monta | Qué exige |
|---|---|---|
| `test_todo_bien_sale_cero_y_sin_avisos` | seis cadenas, bronce, gold de hoy, todo declarado | `estado == "ok"`, `avisos == []`, **exit 0**, y ni un `✗` en pantalla |
| `test_una_cadena_sin_captura_es_fallo_y_la_nombra` | Mercadona sin fila en `runs.csv` ni bronce | `estado == "fallo"`, `sin_pasada` **con la cadena nombrada**, exit 1, y `✗` en su línea |
| `test_una_captura_corta_es_aviso_con_la_referencia_de_la_regla` | Carrefour 600 donde sus días son 1.000 | `captura_corta`, y el veredicto con `filas=600`, `referencia=1.000`, `pct=60.0` — **el de la regla**, no un 90 % escrito aquí |
| `test_gold_atrasado_con_la_pasada_cerrada_es_fallo` | gold y `actual.json` en el día anterior, sin marca | `gold_atrasado` como **fallo**, `gold.fecha_max` de ayer, exit 1 |

Y las que cubren lo que de verdad se va a ver en producción: la pasada **en curso** (no es fallo),
la pasada **que murió**, los avisos **de ayer**, los avisos **que no se pudieron mirar**, la
**cobertura sin declarar**, **dos días sin cerrar**, **un gold sin filas**, que **Lidl no se
compara** contra el máximo, y que **un `data/` vacío no sale 0**.

El rojo que hubo que arreglar de verdad fue éste: la primera versión, cuando una cadena no traía
nada, decía **dos veces lo mismo** (`sin_pasada` y `sin_bronce`) y la prueba que exige «sin pasada
ya lo dice todo» se puso roja; el arreglo fue no exigir bronce cuando no hay ni pasada. Y el rojo
inicial, antes de que existiera el módulo, fue el `ImportError` de la colección.

---

## 8. Límites (lo que este vigilante **no** dice)

- **No sale a la red.** Mira lo que la cadena dejó en disco. Que la web de una cadena se caiga, se
  reintente y acabe bien no se ve aquí; se ve lo que quedó. Para eso está `verificar_precios`.
- **No juzga el contenido.** No mira precios, ni el emparejamiento, ni si los productos son los
  mismos. Eso es `verificar_ingesta`, `cobertura_diaria` y las auditorías.
- **No mira `data/errores.log`, a propósito.** Sus líneas son en buena parte errores tolerados
  (Carrefour tiene 4-5 categorías rotas todos los días y su día es bueno) y además lleva basura de
  pruebas: el 4/11 hay 26 líneas de `RuntimeError: se cayo la web` inyectadas por pruebas con
  `mock`. Un aviso que salta todos los días deja de leerse, y el día que avise de algo de verdad
  tampoco.
- **No distingue «tardó más» de «se atascó»**: no hay reloj por cadena. La marca sólo dice que hay
  una pasada viva; con más de 6 horas se da por muerta.
- **El aviso de Alcampo va a salir todos los días** mientras no se decida otra cosa: su máximo de
  30 días es del **17/10 (28.022 filas)** y desde entonces sus 22.000-24.000 salen «corta». El
  vigilante lo dice porque la regla lo dice; **no baja la vara**, porque bajar la vara es
  precisamente el fallo que `cobertura_diaria` documenta. Arreglarlo es una decisión sobre la
  referencia (por ejemplo, una ventana móvil), no un parche aquí.
- **Sin canal externo de notificación.** No hay correo ni push: el aviso es **informe + JSON +
  código de salida**, y lo que se haga con el código lo decide el enganche del §6.
- **No escribe nada más que su informe.** `data/avisos_ingesta.json` y nada más; `data/`, `gold`,
  `runs.csv` y la cobertura se abren en lectura.

---

## 9. El estado real de la ingesta del 5/11/2026

Mirado por el vigilante, con la pasada en marcha (11:38, hora de Madrid):

| Cadena | Pasada | Filas | Bronce | Referencia (30 d) | Gold | Estado |
|---|---|---:|---:|---|---:|---|
| Carrefour | — | — | — | en curso | 2026-11-04 | en curso |
| DIA | 10:26 | 5.704 | 5.704 | 5.842 (97,6 %) | 2026-11-04 | ✓ |
| Mercadona | 10:16 | 4.267 | 4.267 | 4.320 (98,8 %) | 2026-11-04 | ✓ |
| Aldi | 10:15 | 2.709 | 2.709 | 2.951 (91,8 %) | 2026-11-04 | ✓ |
| Alcampo | — | — | — | en curso | 2026-11-04 | en curso |
| Lidl | 10:14 | 91 | 91 | alcance parcial | 2026-11-04 | ✓ |

Y del día entero: **gold sigue en el 2026-11-04** (versión 20261104-144138), **falta la cobertura
declarada del 5/11** de las cinco cadenas de catálogo (sólo está la de Lidl, que la escribe su
colector) y **la nota de avisos es del 4/11**.

**Veredicto: 5 avisos, 0 fallos, exit 1.** No es un día roto: es un día **que aún no ha cerrado**, y
el vigilante no puede decir «ok» de algo que está a medias (sería el silencio que se quiere evitar).
A las 11:38 Carrefour iba por la categoría 550 de 596 y Alcampo por la 340 con 55 en cola. Cuando
la cadena cierre, esos cinco avisos desaparecen por su orden: cobertura y avisos en el cierre, gold
al publicar, y las dos cadenas al dejar su pasada.

**Lo que diría del día de ayer**, reconstruido con `--fecha 2026-11-04` (un día que todo el mundo
dio por bueno): **1 aviso, 0 fallos** — Alcampo, 23.416 filas contra 28.022 (83,6 %, la vara del
17/10). Ni una cosa más en seis cadenas. Eso es lo que se quiere de un vigilante: que el día normal
haga ruido sólo por lo que de verdad no cuadra.

---

## 10. Lo que se ha tocado

- `scripts/vigilar_ingesta.py` — nuevo. Sólo lectura local; escribe `data/avisos_ingesta.json`.
- `tests/test_vigilar_ingesta.py` — nuevo. 17 pruebas, datos sintéticos, sin PostgreSQL.
- `docs/INGESTA-VIGILANCIA-2026-11-05.md` — este documento.

Nada más: **ni `ejecutar.bat`, ni `run.py`, ni el Programador de tareas, ni una línea de `data/`
aparte del informe propio**. Y sin commit.
