# Historial y avisos por producto — 2026-11-09

Lo que pidió David: **por producto, guardar el precio mínimo visto y su fecha**, y marcar
cuando el precio **vuelve** a ese mínimo. Sin notificaciones emergentes: **solo una marca
visual en la lista** y **un fichero de resumen**.

## La decisión que más importa: «en el mínimo» no puede ser «precio repetido»

Con la definición literal («el precio de hoy es el mínimo visto»), **25.328 de los 52.106
productos con precio hoy** quedaban marcados: casi la mitad. La causa es que muchos productos
repiten el mismo precio todos los días, y entonces estar en el mínimo no dice nada.

La condición que se aplica exige que el precio **haya subido antes y haya vuelto**:

> `vuelve_al_minimo` = el precio de hoy es igual (tolerancia 0,5 céntimos) al mínimo de los
> días **anteriores**, **y** hubo al menos un día, después de ese mínimo y antes de hoy, con
> el precio **por encima** del mínimo (+0,5 céntimos).

Medido sobre el gold del 9/11: **1.480 productos vuelven de verdad** a su mínimo y **125
estrenan mínimo** (por debajo del anterior). Esos son los números que deja el artefacto.

## Dónde queda cada cosa

**1. El artefacto (lo escribe la cadena diaria, en el PC)**

- `data/minimos.parquet` — una fila por producto (79.240 filas, 16 columnas):
  `producto_id, fecha_datos, fuente, id_fuente, precio_hoy_cent, precio_hoy_unidad_cent,
  unidad_canon, minimo_previo_cent, minimo_previo_fecha, minimo_cent, minimo_fecha,
  dias_con_precio, dias_por_encima, ultima_por_encima, vuelve_al_minimo, nuevo_minimo`.
  - `minimo_cent`/`minimo_fecha`: el mínimo visto en **todo** el histórico hasta hoy, y la
    **primera** fecha en que se alcanzó (si se repitió, manda la más antigua: es la que
    aguanta que alguien la compruebe).
  - `minimo_previo_*`: lo mismo pero solo con los días **anteriores** a hoy; es contra lo que
    se juzga si «vuelve».
- `data/minimos-resumen.json` — **el fichero de resumen** que pidió David (824 KB):
  `fecha_datos, ventana_dias, productos, con_historial, vuelven_al_minimo[], nuevos_minimos[],
  generado`. Cada entrada lleva producto, cadena, precios, mínimo y fecha, `dias_por_encima`,
  `ultima_por_encima` y el `nombre`/`marca`/`grupo_id` del catálogo, para que se pueda leer sin
  cruzar ficheros.
- Módulo: `projects/cesta/minimos.py` (`python -m projects.cesta.minimos`, 3,3 s con el gold
  real). Escritura atómica (tmp + replace). Enganchado en `projects/cesta/run.py` después de
  publicar gold y de los avisos; si falla, se registra y **el día sigue**.

**2. La API (solo lee)**

- `GET /api/listas/{id}` añade a cada línea, **solo si hay dato fresco**, un campo opcional:
  `minimo: {producto_id, cadena, precio_cent, precio_unidad_cent, unidad, minimo_cent,
  minimo_fecha, vuelve_al_minimo, nuevo_minimo}`.
- Reglas de degradación: si el artefacto no existe, está truncado o su `fecha_datos` no es la
  de gold, **no se marca nada** y la lista se sirve igual. Mejor no marcar que mentir.
- El producto de la línea manda: `autorizado_producto` y luego `producto_id`. Si la línea no
  dice producto, se usa el **más barato de hoy de su grupo** con las mismas reglas que las
  alertas (sin ofertas de tarjeta ni solo-online, una unidad dominante por grupo). Una línea
  marcada como producto movido **no** cae al grupo.
- Lectura con DuckDB en memoria, cacheada por época de gold + `mtime` del artefacto (primera
  lectura ~300 ms, después ~0,5 ms).

**3. La lista (la marca visual, sin ventanas ni avisos)**

En la fila de metadatos de cada línea (`plataforma/web/app/src/paginas/Cesta.tsx`, `UnaLinea`):

- si vuelve al mínimo: pastilla **«En su mínimo · 2,40 €»** y debajo «visto por primera vez el
  6 sept»;
- si estrena mínimo: pastilla **«Mínimo nuevo · 1,39 €»** (tono distinto); si llegan las dos
  banderas manda la de mínimo nuevo, que es la noticia fuerte;
- si no hay `minimo`, la línea se pinta exactamente como antes.

Todo es texto visible (también para lector de pantalla); no hay `alert()`, ni `confirm()`, ni
notificaciones del navegador.

**Capturas:** antes `data/revision-minimos-antes/05-lista-movil.png` (sin marca), después
`data/revision-minimos-despues/05-lista-movil.png` (con las dos pastillas en las líneas del
batido Puleva y del refresco Coca-Cola zero). El texto completo de la pantalla, en
`data/revision-minimos-despues/textos/05-lista-movil.txt`.

## Comprobado

| Comprobación | Resultado |
|---|---|
| Cálculo independiente del Lead sobre el gold real | 52.106 con precio hoy; **1.480 vuelven**, **125 nuevos** — coincide con el artefacto |
| `pytest tests/test_minimos.py` | 20 pasan (mínimo y fecha, empate, vuelve/subió-y-volvió, repetir precio no marca, tolerancia, mínimo nuevo, sin precio hoy, un solo día, artefacto ausente/desfasado, resumen, caída al grupo, línea movida, enganches) |
| `pytest tests/test_run.py` | 22 pasan (el día sigue si mínimos falla) |
| Pruebas estáticas de la API (imagen, versión vigente, montaje) | 15 pasan |
| Web | vitest 249 · `npm test` 404 · tipos y lint limpios · build (`sw 2026110921`) |
| HTTP de verdad (API local 8099 + banco de ensayo) | dos líneas sembradas con `mercadona:10043` y `mercadona:13816`: la lista devuelve `minimo` con `vuelve=True` y `nuevo=True`; captura |
| Producción reconstruida | `docker compose build api` + `up -d`: `cesta-api-1` *healthy*; dentro del contenedor `minimos.lee()` lee `/datos/minimos.parquet` (52.106 productos); `GET /api/salud` 200; Caddy sirve el paquete nuevo (`index-Beyi7b52.js`) |
| Suite completa de Python | **1.471 verdes, 812 saltadas, 0 rojos, 10 min 4 s** |
| `pytest tests/test_documentos.py` | 5 pasan (se corrigió una doble codificación en `tests/test_minimos.py`) |

## Cómo se rehace

    .\.venv\Scripts\python.exe -m projects.cesta.minimos     # deja los dos ficheros
    pytest tests/test_minimos.py                             # 20 pruebas

La lista se marca sola en cuanto la cadena diaria deje el artefacto del día. Si el artefacto
no es de la fecha de gold, la lista se sirve sin marcas (y el resumen sigue en disco con la
fecha que le toque).

## Límites, dichos

- La marca depende de la cadena diaria: si un día no corre, no hay artefacto nuevo y no se
  marca nada (el de ayer sigue en disco, pero no se usa: su fecha no es la de gold).
- El resumen puede ser grande (824 KB con 1.480 entradas): es para leer/parsear, no para pintar.
- La caché de la API se invalida al publicar gold; en el contenedor la primera lectura del día
  cuesta ~300 ms y el resto ~0,5 ms.
