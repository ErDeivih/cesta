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

## Decisión de coordinación (2026-11-04)

**¿Las pruebas de PostgreSQL necesitan un sandbox desechable?**

- **Sí, autorizado.** Las pruebas de base levantan su propio contenedor desechable (base efímera, volumen temporal, puerto libre).
- La base de casa **no se toca nunca** desde las pruebas, ni para leer.
- Si el contenedor no arranca, la prueba se marca «no ejecutada», nunca verde.

