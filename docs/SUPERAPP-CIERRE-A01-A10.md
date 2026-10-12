# Cierre de A01–A10 — 12 y 13 de octubre de 2026

**Qué es esto.** *La revisión independiente del dueño dejó **diez paquetes ordenados** con sus criterios de
aceptación. Este documento los recorre **uno a uno** y dice qué quedó hecho, qué no, y cómo se comprueba.*

**Y la regla que se sigue, la misma de la matriz de capacidades**: *«cerrar con criterio ejecutado, no por
terminar Markdown o porque la suite permita `xfail`».* **Lo que no está, se dice.**

---

## Las puertas, hoy

```
uv run ruff check .                    ->  All checks passed!
CESTA_POSTGRES=...5434... uv run pytest -q  ->  1959 passed, 0 skipped, 0 failed
cd plataforma/web/app; npm test        ->  74 passed, 0 failed
npx --no-install tsc --noEmit          ->  0
npm run build                          ->  built
```

**Y cero `xfail` en todo el proyecto.** *Las cinco que arrastraba la fase 2 están las cinco arregladas y con
prueba en verde.*

---

## Los diez paquetes

### A01 — Recuperar publicación y evitar repetición · **hecho**

**La causa era un enlace duro.** *`publicar()` adoptaba el catálogo con `os.link` «para no duplicar un
fichero de 195 MB»* -- *y la frase estaba mal dos veces: el mayor son **19,2 MB**, y **un enlace duro no
aísla la versión de lo que le pase al fichero vivo**.* **Medido con `fsutil hardlink list`: tres nombres
para un solo fichero, y el enlace intacto** -- *lo que prueba que el pipeline reescribe **in situ**.*

**Arreglado**: *copia en vez de enlazar, **huella SHA-256** de cada fichero en el puntero, y
`/api/estado/publicacion` para comprobarlo.* **Y la respuesta distingue tres estados, no dos**: `bien`,
`cambiado` y **`sin_huella`** -- *y `coherente` sale **`None`**, no `True`, cuando no se puede saber.*

**Comprobación**: `tests/test_revision_a01_publicacion.py`, 10 pruebas, *y ninguna toca el catálogo real*.

### A02 — Identidad y recomendaciones · **hecho**

**Y el resultado de la auditoría es que no había que sustituir nada**: *`core/identidad.py` ya implementa el
contrato -- `EXACTO`/`PROBABLE`/`ALTERNATIVA`/`CUARENTENA`/`ABSTIENE`, GTIN validado, cuarentena, sin cierre
transitivo -- y **ya está conectado**: `cesta.py` llama a `identidad.decide` y de ahí sale `exacta`.*

**Lo que faltaba era el banco, y está con el caso real dentro**: *las cinco fichas del grupo `11627`
(Aldi Milsani, Carrefour Président, Alcampo/DIA/Mercadona Asturiana)*, **los diez pares de cadenas distintas,
y ninguno sale exacto** -- *que es la prueba de que el motor y la revisión dicen lo mismo.*

**Comprobación**: `tests/test_revision_a02_identidad.py`, 18 pruebas.

### A03 — Frescura por producto · **hecho en el cliente; el servidor no**

**Tres defectos, los tres en `Grupo.tsx`**: *la fecha se tomaba **de la cadena** y no del producto; **un
precio sin fecha decidía**; y **la antigüedad se medía contra el día del catálogo** -- *así un catálogo
congelado mantenía frescos sus precios para siempre.*

**Arreglado**: *la decisión, a `src/logica/frescura.ts` con **reloj inyectable** y 11 pruebas.* **Y el
criterio de A03 está en una de ellas**: *«cuatro días sin ingerir quitan las recomendaciones, sin borrar
datos».*

**Y lo que NO está**: *`cesta._candidatos` y `_promos_vigentes` en el servidor* -- *los lectores de silver
sin pin de publicación.* **No se han tocado.**

### A04 — Concurrencia de cantidades · **hecho**

**La última `xfail`, quitada.** *`cambia_linea` escribía `cantidad = %s` con el comentario «gana el último,
a propósito» -- y ese «último» era **el último que llega**, no el más nuevo.*

**Arreglado con migración `019`**: *`lista_linea.cantidad_en`, y `GREATEST` -- **al contrario que el
`LEAST` del tachado***, *porque tachar es «yo lo hice primero» y la cantidad es «éste es el valor de
ahora».*

**Y la prueba falló **por pasar**, que es el mecanismo que se diseñó.** *Se le quitó la marca.*

### A05 — Lidl · **hecho en las listas; la captura no**

**`CADENAS` (cinco) y `ORDEN` (seis) no decían lo mismo, y la diferencia no estaba escrita.** *Ahora sí:
**`CADENAS_QUE_SE_CAPTURAN`** y **`CADENAS`**, con su motivo* -- *Lidl publica **ofertas semanales
parciales**, y meterlo en las comparaciones haría que pareciera tener precio para cosas que no cataloga.*

**Y una comprobación al importar**: *lo comparable tiene que estar dentro de lo capturable.*

**Y lo que NO está**: *la captura de Lidl* -- *necesita red y una región declarada.* **No se ha hecho.**

### A06 — Fichas y nutrición · **hecho en la procedencia; el resto no**

**El caso del Président de Carrefour**: *`calidad_origen=ingredientes_off`, nota 100 y letra A, con su
columna nativa de ingredientes **vacía** -- y el sello decía «leída de ingredientes» **para las dos
procedencias**.* **Un dato de un tercero atribuido al supermercado.**

**Arreglado**: *la API manda `calidad_de`, la pantalla cambia de texto y de tono, y `_calidad_y_origen` es
una función pura con 7 pruebas.*

**Y lo que NO está**: *el inventario por campo y cadena, el **universo de alimentos**, la cola de
nuevos/cambiados/caducados, y priorizar Alcampo/Aldi y los datos nativos de Carrefour.* **Eso es un
trabajo, no una frase.**

### A07 — Paginación usable · **la regla y el estado; los botones no**

**La API ya recibía `desplazamiento` y el cliente no lo mandaba.** *Ahora está en la URL, se reinicia al
cambiar la pregunta, y hay **aviso de versión** si el catálogo cambia entre páginas.*

**Y una prueba lee el fuente del módulo y exige que no haya un `sort`** -- *porque **el orden es del
servidor, sobre todo el catálogo**, y ordenar la página haría que la primera no tuviera los mejores del
catálogo sino los mejores de los primeros N.*

**Y lo que NO está**: *los botones en pantalla*, y los **ensayos DOM** de respuesta retenida, error,
cancelación y llegada tardía -- *que es lo que la propia revisión avisa que las pruebas de una función pura
**no cubren**.*

### A08 — Recetas, compra y envases · **hecho, las cuatro piezas**

**El cálculo de envases estaba escrito Y NUNCA SE EJECUTABA**: *le pedía el tamaño a `envases.lee`, que
devuelve una **tupla** -- y además **nunca devolvió un tamaño**.*

**Las cuatro piezas, en cuatro rondas**: *la regla (`core/envases_enteros.py`, 20 pruebas) · la conexión a
la previa (`_envases_de`) · el camino desde el ingrediente · y la línea de la API que lo rellena.* **Y el
ejemplo del criterio pasa entrando por el recorrido**: *1,4 kg + envases de 1 kg → **2 envases y 600 g**.*

**Y lo que NO está**: *los permisos de preview, idempotencia y despensa que su criterio pide.*

### A09 — Recorridos reales · **cinco partes hechas de las que pide**

**Hecho**: *el **hogar** (A y B en una lista compartida, texto libre, cierre e histórico) · **la
sustitución** (aceptar, revocar, y que revocar no toque la línea de al lado) · **el 3×2** (el descuento
repartido sin perder un céntimo) · **las doce combinaciones** de ancho, tema y zoom · y **el
desbordamiento encontrado y arreglado** (`min-w-0`, no un número más pequeño).

**Y lo que NO está**: *el catálogo versionado controlado · las pantallas de Recetas y de Calorías · los
«controles, textos y errores reales, **no solo conteo de píxeles**» · y **las capturas** con
commit/imagen/versión.*

### A10 — Despliegue y aprendizaje · **cuatro cosas de las siete**

| lo que pide | **estado** |
|---|---|
| **exposición de puertos** | **hecho**: *la web estaba en `0.0.0.0` -- el único de cinco -- y ahora está en `127.0.0.1`.* **Estaba en dos sitios** |
| **bundles y separar rutas** | **hecho**: *la entrada baja de **677,8 a 326,5 KB**, con 28 trozos por ruta* |
| **backups y restauración** | **verificado**: *volcado de 30 515 bytes, restaurado, contenido 2/2 · 10/10 · 2/2, y **la confirmación conserva `dia:74397|dia`*** |
| **imagen de API** | **hecho**: *el `404` de `/api/estado/publicacion` es ahora un `200`* |
| **`docs/aprende`** | **hecho**: *el capítulo 17, con seis fallos reales y su reproducción* |
| **sesiones y logs sin secretos** | **no**: *se leyó la cookie -- sin `secure`, y **no se cambia porque rompería la sesión en HTTP local*** --, y **no se ha mirado ni un log*** |
| **copia programada** | **no**: *esto comprueba que **se puede** hacer, no que **se haga** -- no hay tarea, ni retención, ni sitio donde se guarden los volcados* |

---

## Y el daño que causé, que va al final y no se disimula

**`cesta-prueba-db` tenía 716 usuarios, 2 529 listas y 2 533 líneas. Ahora tiene 2, 2 y 10.**

**Cómo**: *al correr `plataforma/prueba_copia.py` le puse `CESTA_POSTGRES` apuntando al `5434`, y el guion
-- en su versión de entonces -- **no ponía ese entorno para el ensayo**: lo heredaba.* **Así que
`prueba_e2e` corrió contra la base de pruebas de verdad, y ese ensayo rehace el esquema.**

**Y hay una corrección que debo a mi propio informe.** *Dije que **«el daño no se nota en las puertas,
porque cada prueba crea sus propios usuarios»**.* **Era falso, y se vio al correr la suite entera:**

```
1942 passed, 17 skipped      <- y las 17 dicen por que
SKIPPED: no hay cuenta de prueba y el alta tiene limite por hora agotado
SKIPPED: no hay cuenta de prueba en el almacen
```

*Diecisiete ensayos necesitaban una cuenta que estaba entre los 716 usuarios, y el límite de altas
impedía crear otra.* **Se recuperaron recreando `prueba-navegador` y `recibo-de-prueba` con
`almacen.crea_usuario`** -- *que no pasa por la ruta HTTP y por tanto no toca el límite* --, **y la suite
volvió a `1959 passed, 0 skipped`.**

> **La lección, que es la de todo este trabajo**: *«no se nota» es una afirmación, y hay que comprobarla
> como cualquier otra.* *Yo la hice sin mirar la suite entera, y era falsa por diecisiete ensayos.*

**Y lo que se arregló del guion**, para que no vuelva a pasar: *nombres y puertos propios
(`cesta-copia-ensayo:5436`, `cesta-copia-db:5437`) y **el `CESTA_POSTGRES` puesto por él**, en vez de
heredado.*

**Lo que no está en peligro**: *los datos de casa (`cesta-db-1` no publica puerto), `facylf-postgres`
(el `5433`, **intacto**), el catálogo (`data/gold` **intacto**), y los tres ficheros ajenos.*

---

## Lo que este cierre deja dicho como lo que falta

**Ordenado por lo que más pesa, y no por lo que más fácil sería:**

1. **Una copia programada.** *Está comprobado que se puede; **no hay nada que la haga**.*
2. **`docs/aprende`** está actualizado con los fallos, **y no con las carencias de cobertura** -- *que era
   la otra mitad de lo que la revisión pedía.*
3. **El recorrido de A09 con textos y errores reales**, y las capturas con commit/imagen/versión.
4. **La caducidad de sesiones y los logs sin secretos** -- *no medidos.*
5. **Y las conexiones que cada paquete dejó dichas**: *`tamano_envase` en los sitios que faltaban,
   `_candidatos` y `_promos_vigentes` en el servidor, y la captura de Lidl.*
