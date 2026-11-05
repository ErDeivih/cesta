# Decisiones de nivel 2 — sesión del 4 de noviembre de 2026

Nivel 2 del protocolo de autonomía: **se decide solo, se ejecuta y se deja escrito aquí el
motivo**. David lo revisa cuando quiere. Cada decisión dice qué se ha hecho, con qué
evidencia, qué se gana, qué riesgo se acepta y cómo se revierte.

---

## 1. Un folleto de campaña ya no veta el día entero de una cadena

**Qué se ha hecho.** El control de cobertura (`core/cobertura.py`) separa desde hoy dos
preguntas que antes eran una sola: *qué ramas se han hundido* (`revisa`, que se sigue
diciendo en el registro) y *qué ramas impiden guardar la captura* (`que_vetan`). Las ramas
de folleto van en `RAMAS_DE_CAMPANA` — hoy solo `alcampo: {"Folletos y Promociones"}` — y
avisan pero **no vetan**. Los cinco colectores de catálogo usan la misma función.

**La evidencia, medida sobre el bronze del día.** El 4/11/2026 Alcampo terminó con 23.416
productos y **cero errores**, y su bronze no se escribió. Las ramas, comparadas con el
3/11/2026:

    15 ramas de comida SUBEN   Frescos +6 %  Perfumeria +10 %  Drogueria +15 %  Bebe +38 %
     1 rama baja               Folletos y Promociones  1472 -> 727  (-51 %)

El total del día (23.416) es **mayor** que el de ayer (22.776). Lo que se hundió es el
folleto de la campaña, cuyo contenido lo pone la campaña de la semana.

**Qué se gana.** 23.416 precios frescos de una cadena que participa en **7.210 grupos
comparables** — la que más — y un día más en una ventana donde ya faltaban 11 de 30.

**Riesgo que se acepta, y por qué es pequeño.** La regla existía para el 18/09/2026, cuando
faltó la rama **Frescos** entera y el catálogo salió a la app sin fruta, carne ni pescado.
Eso **sigue vetando**, y está como prueba de regresión
(`test_una_rama_de_estanteria_hundida_sigue_vetando`, `test_un_folleto_y_un_fresco_hundidos_a_la_vez_siguen_vetando`).
La excepción es **por cadena y por nombre de rama**, escrita en el código, no inferida: no
se hereda a DIA ni a ninguna otra (`test_la_excepcion_no_se_hereda_a_otra_cadena`).

**Cómo se revierte.** Vaciar `RAMAS_DE_CAMPANA` en `core/cobertura.py`. Una línea, sin
migración de datos: el comportamiento vuelve al de ayer.

---

## 2. El día de Alcampo se recupera del crudo, no relanzando la ingesta

**Qué se ha hecho.** `uv run python -m projects.cesta.reprocesar --fuente alcampo --fecha
2026-11-04` → 23.416 productos. Después, el tramo final del ciclo **sin red**
(`pipeline → emparejador → manifiesto → publicación`) con `scripts/rehacer_dia_sin_red.py`.

**Por qué así.** El crudo del día ya estaba en disco (394 ficheros, 21 MB): volver a pedirle
23.000 páginas a una cadena que acaba de cortar por WAF sería peor que no hacer nada.
Comprobado antes de lanzar nada que **no hubiera una ingesta en marcha** (ningún proceso de
`python`/`uv` de cesta, `runs.csv` con la última cadena a las 12:58 y el día cerrado a las
14:11) — la especificación prohíbe duplicar una captura activa.

**Qué se gana.** El día entra en gold y en la publicación sin una sola petición nueva, y
`cobertura_diaria` deja de decir «alcampo: sin datos».

**Riesgo.** El bronze nuevo se escribe en una partición que **no existía** (2026-11-04):
nada se sobrescribe, y si hiciera falta se aparta a `data/debug/descartados/` como manda
`docs/OPERACION.md`. Comprobado antes de escribir: 23.416 ids únicos, 0 duplicados y 0 filas
sin precio.

**Cómo se revierte.** Apartar la partición `data/bronze/fuente=alcampo/fecha=2026-11-04` y
volver a publicar.

---

## 3. El manifiesto cuenta las filas que hay, y declara la cobertura de las cinco cadenas

**Qué se ha hecho.** `core/manifiesto.py`: las filas se leen del **índice** del parquet
(`pyarrow.num_rows`), no con `pl.read_parquet(ruta, columns=[]).height`; y se añade
`cobertura_medida` con el veredicto de cada cadena, reutilizando
`projects.cesta.cobertura_diaria.veredictos()` (una regla, un sitio).

**La evidencia.** El manifiesto publicado a las 13:09 del 4/11 decía:

    "precio_diario.parquet": {"sha256": "85e3d256aad0", "filas": 0, "bytes": 33.873.856}
    "cobertura_declarada": {"lidl-2026-10-13": ..., "lidl-2026-10-14": ...}

y ese fichero tenía **2.527.902 filas**. En polars, pedir cero columnas devuelve cero filas:
sin columnas no hay nada que contar. `"filas": 0` no era un redondeo, era un contrato que
mentía — y el recuento es justo lo que se lee para saber si una publicación trae algo.

La segunda mitad es el «solo Lidl tiene cobertura, 21 días» de `AGENTE.md`: `cobertura_declarada`
solo lleva lo que los colectores escriben en `data/cobertura/`, y ahí **solo escribe Lidl**.
El documento no mentía: leía el único sitio donde había cobertura. Ahora el manifiesto lleva
también la cobertura **medida** de las cinco cadenas de catálogo.

**Qué se gana.** Cualquiera que lea lo publicado —persona, panel o documento— puede
distinguir «Alcampo no trajo nada» de «Alcampo trajo 23.416 y su vara son 28.022 del 17/10».

**Riesgo.** El manifiesto tarda algo más en generarse (lee el pie de seis parquet). No puede
tumbar el día: todo va en `try` y sin cobertura medida sale sin esa sección.

**Cómo se revierte.** Quitar la clave `cobertura_medida` de `construye()`.

---

## 4. La vara de la cobertura **no** se cambia en esta sesión

**Qué se ha hecho.** Nada sobre el umbral. Se ha añadido al veredicto **de qué fecha es la
referencia** (`referencia_fecha`) y **cuánto cambió** contra la captura anterior
(`vs_anterior_pct`).

**Por qué no se cambia.** La referencia es el **máximo de 30 días** a propósito: con la
mediana, la bajada lenta del caso Alcampo (37.019 → 24.120 → 0) se daba por buena. Pero ese
máximo lo fija hoy un día suelto — 28.022 el 17/10/2026, cuando lo normal es 22.800–24.300 —
y el efecto es que **Alcampo sale «corta» todos los días**: 23.416 contra 28.022 = 83,6 %,
siendo la mejor captura en una semana y +2,8 % sobre ayer.

Un aviso que salta siempre deja de mirarse, así que **hay que hacer algo**; lo que **no** se
hace por cuenta propia es bajar una guarda de seguridad. Las opciones (percentil 90, marcar
el día atípico, ventana móvil) cambian qué defectos se cazan, y eso es una decisión de
producto: queda en `BACKLOG.md` tarea 2 con los números medidos.

**Mientras tanto** el informe dice contra qué mide, que es la mitad del arreglo y no debilita
nada.

## 5. La cobertura de cada cadena se declara **medida**, y dice qué produjo el día

**Qué se ha hecho.** `projects/cesta/cobertura_diaria.py` gana `declara(fecha)`: escribe
`data/cobertura/<fuente>-<fecha>.json` para las **cinco cadenas de catálogo**, con lo medido
sobre su bronce — filas, referencia y de qué día es, %, huecos y veredicto (la misma regla de
`veredicto`, no una copia) y, además, **la novedad del día**: ids nuevos, precios cambiados e
ids que desaparecen frente a la captura anterior. Se llama al cerrar la cadena diaria
(`run.py`), **antes** de que se escriba el manifiesto —que lee esa carpeta—, y a mano se puede
repetir con `--escribir` (idempotente: dos pasadas dejan los cinco ficheros con el mismo
sha256; comprobado).

**La evidencia, escrita y comprobada el 4/11/2026.** Medido sobre el bronce del día contra la
captura anterior (3/11), que es lo que se declara:

| cadena | filas | referencia (fecha) | % | novedad vs 3/11 |
|---|---:|---|---:|---|
| mercadona | 4.272 | 4.321 (05/10) | 98,9 | +4 nuevos, 71 cambiados, 9 menos |
| dia | 5.712 | 5.855 (05/10) | 97,6 | +20 nuevos, 425 cambiados, 20 menos |
| carrefour | 16.782 | 16.794 (31/10) | 99,9 | +75 nuevos, 5 cambiados, 85 menos |
| aldi | 2.709 | 2.951 (31/10) | 91,8 | +5 nuevos, 62 cambiados, 130 menos |
| alcampo | 23.416 | 28.022 (17/10) | 83,6 | +943 nuevos, 4 cambiados, 303 menos |

Efecto en lo publicado: `data/gold/manifiesto.json` pasa de 21 declaraciones (todas de Lidl) a
**26** —las cinco cadenas de catálogo incluidas— y `GET http://127.0.0.1:8080/api/estado`
devuelve bloque `cobertura` para **las seis cadenas**; antes, solo Lidl lo traía. La
`cobertura_medida` del manifiesto sigue intacta.

**Por qué así, y no añadiendo una cadena.** La tarea llegaba con «la cobertura de precios es de
UNA sola cadena (Lidl, 21 días)». Medido: **cinco** cadenas de catálogo con **43–57 días** de
histórico en gold (Alcampo 43, Aldi 57, Carrefour 51, DIA 53, Mercadona 57) y una pasada diaria
registrada en `data/runs.csv` **56–58 días** contando el día local (Alcampo 56, Aldi 58,
Carrefour 56, DIA 57, Mercadona 58; en UTC Alcampo sale 57), y ese mismo día **8.829 de los
39.115 grupos comparables con precio** tenían 2+ cadenas (22,6 %; sin exigir importe no nulo,
8.851 de 39.837). No faltaba una cadena: faltaba que las que hay
**declararan** lo suyo, porque el único sitio de declaración era `data/cobertura/` y ahí solo
escribía Lidl. Añadir un colector nuevo habría sido trabajo inventado —y `docs/COLECTORES.md`
§4.5 lo prohíbe—. Lo añadido es la declaración: dato medido, no una autodeclaración de la
cadena.

**Riesgo aceptado.** `data/cobertura/` crece ~5 ficheros/día (~1 KB cada uno) y el manifiesto
los lista todos (~1,8 MB al año). Se acepta sin retención mientras sea texto pequeño; si
molesta, queda como tarea en `BACKLOG.md`. Las filas declaradas son **bronce**; `productos` de
la API es **gold publicado** (Alcampo 23.416 → 23.405; Aldi 2.709 → 2.499, de las que 202 venían
sin precio en el bronce y 8 descarta el alcance): la diferencia es el filtro, y la doc de
evidencia la explica, no la disfraza.

**Una variación que estaba mal, encontrada por la revisión adversarial.** El
`vs_anterior_pct` que ya existía recorría el calendario al revés y comparaba con **la captura
más antigua de la ventana**, no con la anterior: publicaba «Alcampo +1,7 % sobre la captura
anterior» contra el 5/10 cuando lo real era **+2,8 % contra el 3/11**, y en Aldi hasta
cambiaba el signo (+6,8 % frente a −4,4 % real). Corregido en `cobertura_diaria.veredicto` con
su prueba (dos capturas anteriores, y salto de un día sin captura) y regeneradas las cinco
declaraciones y el manifiesto.

**Manifiesto del 4/11.** Se regeneró a mano con `core.manifiesto` después de declarar, **sin
mover la versión publicada** (`20261104-144138` en `data/gold/actual.json`), para que lo que se
lee hoy no siga diciendo «solo Lidl». La pasada diaria hace la declaración **antes** del
manifiesto y aunque el emparejador falle, y **ya se lanza sola**: David re-registró la tarea
`Cesta diaria` el 4/11 a las 19:18 (acción `F:\Proyectos\cesta\ejecutar.bat`, 3 disparadores) y
se verificó con un disparo manual (`LastTaskResult 0`, próxima 5/11 06:00). Detalle en
`docs/COBERTURA-DIARIA-2026-11-04.md` §11.

**Cómo se revierte.** Quitar el bloque de `declara()` de `run.py` y apartar
`data/cobertura/<cadena>-*.json`; el manifiesto y la API vuelven a lo anterior en la siguiente
pasada. Sin migración ni pérdida de datos.

## 6. Las métricas del panel: qué significa cada número de `metricas-cesta.json`

**Qué se ha hecho.** `projects/cesta/metricas.py` escribe `metricas-cesta.json` en la raíz del
proyecto, con la forma que pidió David, y `run.py` lo reescribe al cerrar cada pasada (como
`CIFRAS.md`): un número escrito a mano envejecería y el panel enseñaría una foto vieja sin
avisar. También se puede lanzar a mano: `python -m projects.cesta.metricas` (o `--ver`).

**Definiciones, para que el panel no lea de más:**

- `fecha_datos`: el día de los precios (la fecha máxima de `data/gold/precio_diario.parquet`).
- `cadenas[]`: por cadena, `hoy` = tiene alguna fila de precio con **importe no nulo** ese día;
  `dias` = días distintos con precio guardados en todo el histórico (hoy: Alcampo 43, Aldi 57,
  Carrefour 51, DIA 53, Lidl 21, Mercadona 57).
- `ultima_ejecucion`: la última pasada de `data/runs.csv`, **en hora de Madrid** (el `ts` está en
  UTC; a las 23:30Z ya es el día siguiente aquí). Hoy: `2026-11-04T13:58:00+01:00`.
- `comparables_con_precio`: grupos con `precio_comparable` **y una fila de precio con importe ese
  día**. Hoy: **39.115**.
- `en_varias_cadenas`: de esos, los que tienen precio en **2 o más cadenas** el mismo día. Hoy:
  **8.829** (22,6 %). **Es la cifra que dice si de verdad se puede comparar**, y va sobre el mismo
  día que la anterior a propósito: mezclar «cuántos comparables hay en el catálogo» con «cuántos
  tienen 2+ cadenas hoy» daría una razón que no significa nada.
- **Matiz medido después (4/11, tarde):** ese 8.829 exige importe no nulo, pero no la regla de
  producto. Con **unidad dominante y comparación fiable** —lo que la app puede prometer sin
  mentir— son **8.066 grupos (20,1 %)**; sin exigir importe, 8.851. La app y su documentación
  dirán siempre cuál de las tres están enseñando (`docs/DATOS-APP-2026-11-04.md` §4 y §14).
- `dias_historial`: días distintos con precios guardados. Hoy: **59**.
- `fecha_datos` es un campo **añadido** a la forma pedida: sin él, «hoy» no se puede interpretar
  dentro de una semana. El resto de claves es exactamente el contrato.

**Un matiz de dato, medido.** `precio_diario` del 4/11 tiene **760 filas con `precio_cent` nulo**
(52.701 en total). Por eso «con precio» da 39.115/8.829 y no 39.837/8.851: esas 760 filas son
presencia sin importe, y contarlas como precio sería vender más comparación de la que hay. Si el
panel quiere la cifra laxa, se puede añadir; hoy no se publica.

**Cómo se revierte.** Borrar `metricas-cesta.json` y el bloque de `run.py` que llama a
`metricas.escribe()`; no toca datos ni publicación.

## Decisión de coordinación (2026-11-04)

**¿Las pruebas de PostgreSQL necesitan un sandbox desechable?**

- **Sí, autorizado.** Las pruebas de base levantan su propio contenedor desechable (base efímera, volumen temporal, puerto libre).
- La base de casa **no se toca nunca** desde las pruebas, ni para leer.
- Si el contenedor no arranca, la prueba se marca «no ejecutada», nunca verde.

## Decision de coordinacion (2026-11-04, tarde) — arreglar la automatización y datos del panel

- **La automatización diaria apunta a `F:\aprendizaje\scrap`, que ya no existe.** El proyecto vive en
  `F:\Proyectos\cesta`. Hay que re-registrar la tarea programada con la ruta nueva (requiere
  administrador). Mientras no se haga, la ingesta diaria **puede no estar corriendo**: comprobarlo primero.
- **Datos que el panel necesita de Cesta** y hoy no tiene: cadena con datos de hoy, días de cobertura
  por cadena, última ejecución, productos comparables con precio, y cuántos productos tienen precio de
  más de una cadena (la métrica que dice si de verdad se puede comparar). Se publican en
  `F:\Proyectos\cesta\metricas-cesta.json`.

## Decisión de producto (2026-11-05) — comparar la cesta valora 5 cadenas, no 6

El motor de la cesta (`plataforma/api/cesta.py`, `CADENAS`) valora **cinco**: Alcampo, Aldi,
Carrefour, DIA y Mercadona. Lidl se **captura** (sus ofertas semanales), pero no se compara: no
publica un catálogo con precios de referencia como las otras, así que meterlo en un total de la
cesta sería comparar cosas distintas.

**La app no dice «6 cadenas».** La pantalla de comparar dice «lo he podido valorar en N cadenas»,
con la N sacada de los datos, y corona a una cadena solo si su total cuenta **todas** las líneas
de la lista (si le falta un producto, no gana y se dice cuál falta). Fuera de esa pantalla se
habla de cadenas sin prometer seis. En el panel y en los documentos se puede seguir distinguiendo
«6 capturadas» de «5 valoradas»: son dos cosas.

**Cambiar esto es una tarea de datos**, no de texto: si algún día Lidl publica catálogo comparable,
entra en el motor y la N sube sola.

