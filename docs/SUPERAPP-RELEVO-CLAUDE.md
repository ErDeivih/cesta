# Relevo para Claude · SUPERAPP de Cesta

**Estado del repositorio en el momento de escribir esto:** commit `d85d732`, árbol limpio,
**suite completa 1.301 pruebas, 0 fallos**, `ruff check .` limpio salvo **una** sugerencia en
`plataforma/api/cesta.py` (ver «Deudas dichas», al final).

**El objetivo NO está cumplido.** De los trece paquetes (S00–S12) hay **seis tocados** y **S10–S12 sin
empezar**. Este documento existe para que puedas revisar, corregir y continuar sin releer la sesión.
Está escrito para que **no tengas que fiarte de nada**: cada afirmación lleva su comando o su número.

---

## 1. Qué se pidió, y qué se ha hecho

El encargo vigente está en **`docs/SUPERAPP-00-EMPEZAR-AQUI.md`** y sus enlazados (`SUPERAPP-01` diseño
y producto, `SUPERAPP-02` datos/Lidl/identidad, `SUPERAPP-03` investigación). El estado vivo está en
**`docs/SUPERAPP-ESTADO.md`**: léelo **de arriba abajo**, porque empieza por el resumen vigente y la
bitácora histórica va después.

| paquete | estado | una línea |
|---|---|---|
| **S00** baseline | hecho | cambios heredados verificados y preservados |
| **S01** publicación versionada | hecho (etapa anterior) | versión con puntero atómico, rollback y concurrencia probados |
| **S02** cola de fichas | hecho (etapa anterior) | SQLite con estados, *lease*, hash, evidencia, próxima revisión; inventario de **79.915** |
| **S03** Lidl | **EN CURSO** | sitemap medido (6.622 → 691 incluidas / 1.568 de bazar / 4.363 a revisión), ficha real, lector con GTIN validado, **la cola pide fichas** (28 leídas). **Le faltan sus criterios de aceptación** |
| **S04** identidad exacta | **núcleo + candidatos + sombra** | motor de decisión, candidatos por GTIN y por bloque, sombra medida |
| **S05** vigencia | **hecho** | `fecha_tope` aplicada en `_candidatos` **y sus cuatro llamantes** |
| **S06** armazón | **hecho** | menú lateral, tres aplicaciones con rutas propias, cajón móvil accesible |
| **S07** alternativa explícita | **hecho** | cada elección dice si es el mismo producto o una alternativa, y por qué; el aviso se ve |
| **S08** Recetas | **almacenamiento + API + pantallas** | versionado autocontenido, recetario con selector de versión y plan semanal |
| **S09** Calorías | **almacenamiento + API + pantalla** | diario con fuente del dato, conocido ≠ completo, compra ≠ consumo |
| **S10–S12** | **sin empezar** | puentes, gráficas y **ensayo integral** (lo más gordo de lo que falta) |

---

## 2. Cómo se comprueba todo (empieza por aquí)

```powershell
uv run pytest -q                 # suite completa: 1.301 pasan, 0 fallan
uv run ruff check .              # limpio salvo una sugerencia dicha al final
cd plataforma/web/app
npx tsc --noEmit                 # tipos del frontend
npm run build                    # tsc + vite
```

Puertas del proyecto (todas en `plataforma/`):

| puerta | para qué | ojo |
|---|---|---|
| `uv run python -m plataforma.prueba_suite` | **23 comprobaciones en navegador** del armazón: navegación, lateral ausente a 390 px y presente a 1280, foco atrapado en el cajón, Escape, recarga, redirecciones antiguas, cero errores de página | necesita el servidor de desarrollo en **5173** |
| `uv run python -m plataforma.prueba_funciones` | 115 comprobaciones funcionales | |
| `uv run python -m plataforma.prueba_navegador` | la app servida, con PostgreSQL de pruebas | necesita Docker |
| `uv run python -m plataforma.prueba_e2e` | recorrido de extremo a extremo en un PostgreSQL desechable (5434) | necesita Docker |

**Docker está parado en la máquina donde se trabajó.** Eso **no impide** construir, probar lógica ni
persistencia. Para ver interfaz de verdad, el camino documentado en `docs/OPERACION.md` es el servidor
de desarrollo de Vite:

```powershell
cd plataforma/web/app
$env:CESTA_API='http://127.0.0.1:8099'; npm run dev   # queda en http://localhost:5173
```

---

## 3. Lo entregado, ronda a ronda, con su evidencia

Los commits de esta etapa, en orden (los tres primeros bloques son los que dan forma a lo demás):

| commits | qué se hizo | evidencia |
|---|---|---|
| `c578d36`, `9ff379b` | **S06**: lanzador, `/compra`, `/recetas`, `/calorias` con layout propio, menú lateral de 248 px, cajón de 288 px con foco atrapado y Escape, redirecciones que **conservan la query** | **23 comprobaciones en navegador** (`plataforma/prueba_suite.py`, versionado), capturas en `data/capturas-s06/` |
| `efcdf9e`, `ce8e4f2`, `65bb121` | **S04 núcleo**: `core/identidad.py` — GTIN validado **y** presentación comprobada, cuarentena, abstención, **sin cierre transitivo**; la validación de GTIN de las fichas de Lidl pasa a delegar aquí | 11 pruebas · y los dos contratos heredados que S06 rompió (títulos de ruta y colores del tema) arreglados **en el código**, no en las pruebas |
| `1059f85`, `5ef63d1` | **S04 candidatos y sombra**: candidatos exactos por GTIN y probables aparte; la sombra propone, compara e informa **sin tocar nada** | 3 pruebas de la lógica pura + el informe en `data/identidad-sombra/` |
| `1159547` | **S05**: `fecha_tope` deja de ser decorativa | 3 pruebas, una lee el código para que ningún llamante vuelva a pasar cadena vacía |
| `8072ef2`, `aff11d5` | **S07**: cada `Eleccion` sale con `identidad` y `motivo`, y el aviso **se pinta** en la lista | 6 pruebas del servidor + `AvisoIdentidad` en `RepartoEnTiendas` |
| `8ef147a` | **S08 almacenamiento**: `core/recetas.py` | 11 pruebas |
| `ef46905` | **S09 almacenamiento**: `core/diario.py` | 10 pruebas |
| `62cf4ed`, `7f75599` | **APIs** de recetas y diario + **prueba de montaje** | 5 + 6 + 3 pruebas |
| `478f204`, `8842cb7`, `40f6132` | **Pantallas propias**: recetario con **selector de versión**, diario con **conocido / sin dato separados**, plan semanal que **muestra la versión fijada** | `tsc` limpio, `npm run build` correcto |
| `35d3f02`, `5e744a3`, `d85d732` | estado: resumen vigente separado de la bitácora, con las cinco afirmaciones precisadas | — |

### Los números que se midieron, y qué describen exactamente

| medida | valor | **qué describe y qué NO** |
|---|---|---|
| catálogo (gold) | **51.915** productos | el catálogo, no el surtido de ninguna cadena |
| con **GTIN válido** | **25.294** (48,7 %) | dígito de control calculado, no copiado |
| grupos exactos por GTIN | **1.627** (1.589 multi-cadena) | solo GTIN válido |
| probables por bloque | **4.259** | **no son identidad**: van contados aparte a propósito |
| **cuarentena** (mismo GTIN, presentación incompatible) | **266** | **sin revisar**; aquí una de las dos fichas miente |
| grupos actuales multi-cadena | **6.545** | son **componentes conexas** de las 22.750 aristas de `enlaces.parquet`, no filas con id |
| **se partirían** al aplicar GTIN válido | **2.222 (34 %)** | **uno de cada tres** grupos que hoy se presentan como «el mismo producto» no lo es |
| sobreviven como exactos | **4.045 (62 %)** | un GTIN, varias cadenas |
| inventario de fichas | **79.915** | descubiertos; **28** tienen ficha leída |
| Lidl, sitemap | 6.622 → 691 incluidas / 1.568 de bazar / 4.363 a revisión | |
| nutrición en Lidl | **0 de 26** fichas leídas | **esa muestra, ese lector, casi todo envasado**. NO dice que la cadena no publique nutrición |

**Tres cosas que se leen mal y conviene no repetir:** «sin ficha» en la cola nueva **no** es «sin datos
históricos» (el catálogo ya traía ingredientes de DIA y Mercadona); un GTIN válido **no basta** para
identidad exacta (hay que comprobar además la presentación, y eso es lo que hace el motor); y una ficha
que el parser entiende **no** demuestra identidad.

---

## 4. Las decisiones de diseño que no conviene deshacer

1. **La regla central: elegir un producto concreto no autoriza a sustituirlo por otro más barato.**
   Está implementada: `Eleccion` lleva `identidad` (`exacto` / `probable` / `alternativa` / `cuarentena`
   / `abstiene`) y `motivo`, y la interfaz pinta el aviso. `probable` avisa de una manera y
   `alternativa` de otra, porque no son lo mismo.
2. **La abstención es un resultado válido.** Gramos contra mililitros abstenie (sin densidad
   documentada); sin evidencia suficiente, abstenie.
3. **Sin cierre transitivo:** un grupo solo se amplía si el candidato es compatible con **todos** sus
   miembros. Si no, `Cuarentena`.
4. **Las versiones son autocontenidas.** Una receta versionada guarda sus ingredientes **copiados**; el
   diario cita una versión y esa versión no se mueve nunca. Sin eso, editar una receta cambiaría lo que
   comiste el mes pasado.
5. **Ausencia no es cero.** En el diario, una entrada sin dato **no aporta 0 kcal**: aporta nada, aparece
   en `sin_dato`, y el día no está `completo`. En la cobertura y en las ofertas, la misma regla.
6. **Las compras no son consumo**: `core/diario.apunta` **rechaza** el tipo `compra` con un error. No es
   un comentario, es código, y tiene prueba.
7. **La sombra antes de activar.** Nada de la identidad nueva se publica hasta revisar las 266
   cuarentenas.
8. **El plan fija la versión** de la receta que se planificó.

---

## 5. Trampas del entorno que ya costaron rondas (léelas antes de tocar nada)

- **No uses `python -c` con comillas, acentos ni acentos graves desde PowerShell.** Me costó cinco
  intentos fallidos en una ronda y cuatro en otra. **Escribe el script a un fichero** y ejecútalo, o
  cambia de herramienta: cuando algo falla tres veces por lo mismo, se cambia la herramienta.
- **Los mensajes de commit, a un fichero y con `git commit -F`.** Con `-m` y varias líneas, PowerShell
  los parte y el commit falla con un `pathspec` incomprensible.
- **`data/` está ignorado por git.** Un script o una prueba que viva ahí **no se versiona**, y una
  comprobación que no se versiona no es una prueba: es un apunte.
- **Antes de sustituir líneas, léelas.** Casi todas mis rondas perdidas fueron por anclar sobre texto
  que suponía en vez de leerlo. **Mira antes de suponer**: la respuesta suele estar a una consulta de
  distancia.
- **Nunca commitees `core/datos/secciones.yml`.** Y no rompas la pasada de las 06:00 (`ejecutar.bat`):
  `run.py` **descubre** cadenas, así que un `fuente=lidl` en bronze haría que la pasada diaria lanzara
  Lidl; por eso el colector de Lidl lleva **guarda `--escribir`**.
- **Hay pruebas que leen el código** y cazan fallos que el compilador no ve: `test_interfaz.py`
  (colores), `test_titulos.py` (títulos por ruta), `test_ui_movil.py` (16 px mínimo en campos de texto).
  **Cuatro veces** en esta etapa cazaron un fallo silencioso:
  - `text-tinta`, un token que existe como **objeto**, así que la clase no se aplicaba;
  - **opacidad sobre una variable** (`bg-terracota/10`): Tailwind escribe `rgb(... / 0.x)` y ahí no cabe
    un `#rrggbb`, el navegador lo ignora en silencio;
  - una **referencia a una variable que ya no existía** (`var(--tinta)`);
  - campos de texto a **15 px**: por debajo de 16, el móvil hace zoom al enfocar.
- **Convenciones:** código y comentarios en español **sin acentos**; documentos en español **con**
  acentos. Documentación en el **mismo commit** que el código. `docs/SUPERAPP-ESTADO.md` actualizado
  **antes de cada pausa**.

---

## 6. Trabajo revertido, y por qué (para no repetirlo)

- **El primer intento de S07** se revirtió entero: los campos nuevos de `Eleccion` iban **antes** de
  `linea_id`, así que la llamada posicional metía el id de la línea en el veredicto (el error decía
  `'l1' == 'exacto'`), y **faltaba el GTIN de la fila elegida** (sin él el motor compara un código
  contra nada y la respuesta correcta es `probable`, nunca `exacto`). **Contramedidas aplicadas**: los
  campos nuevos van después, y **los finales se pasan por nombre**.
- **Dos pruebas se retiraron con una nota en su sitio**: una que leía el catálogo real y tardaba **336
  segundos** (una prueba que cuesta cinco minutos se acaba saltando), y otra de la comparación con un
  grafo de mentira que no conseguí montar en dos intentos. En los dos casos la comprobación vive ahora
  donde se ejercita de verdad.
- Una prueba de colores estuvo **en rojo** y se commiteó **diciendo su nombre y su aserción exacta** en
  el mensaje, en vez de esconderla o perder el trabajo.

---

## 7. Deudas dichas

1. **Una sugerencia de lint** en `plataforma/api/cesta.py` que `ruff` no aplica por sí sola
   (`uv run ruff check --unsafe-fixes --diff plataforma/api/cesta.py` la enseña).
2. **`core/identidad.py` y `core/diario.py` los importa poca cosa todavía**: el motor decide en la API
   de la cesta, pero **la identidad nueva no está activada** en ningún recorrido de usuario.
3. **Los módulos de S08 y S09 no tienen pantalla de detalle por ruta** ni las secciones de *mis
   alimentos* y *tendencias*: siguen en la pantalla de cocina compartida con un `modo`.
4. **Ninguna copia de seguridad se ha restaurado nunca**, ni se ha probado el flujo con dos usuarios.

---

## 8. Lo siguiente, en orden, con el primer paso concreto

1. **Revisar las 266 cuarentenas**, una a una, mirando las dos fichas del mismo GTIN: es donde una de
   las dos miente. Es trabajo de datos puro, no depende de nadie, y **es lo que desbloquea decidir
   sobre la identidad nueva**. El informe está en `data/identidad-sombra/identidad-<fecha>.json`.
2. **Terminar de partir la pantalla de cocina** (detalle por receta, *mis alimentos*, *tendencias*): es
   lo último de la arquitectura antigua, y es avance visible.
3. **Cerrar S03**: estratificar la muestra de fichas **por familia** (los 5.026 pendientes están en
   orden de identificador, que no es una muestra; cuando la familia no pueda determinarse, **registrar
   ese estrato desconocido**), resolver los 4.363 a revisión **con la ficha y no con el slug**, e
   informe por fuente y familia.
4. **S10–S12**: puentes explícitos e idempotentes, gráficas con medida y universo declarados, y el
   **ensayo integral** con datos reales, **dos usuarios**, recuperación de errores y **copia de
   seguridad restaurada**. Es lo más gordo que queda.

---

## 9. Qué revisar de mi trabajo, concretamente

Si vienes a **corregir**, estos son los sitios donde más probable es que haya algo mejorable, en orden
de impacto:

1. **`core/identidad.py`**: los umbrales (2 % de tolerancia en cantidad, `pack` ausente leído como 1),
   la lista de unidades y la regla de «sin GTIN, lo mejor es `probable`». Son decisiones defendibles,
   pero son decisiones.
2. **`_candidatos` en `plataforma/api/cesta.py`**: el canónico del grupo es el de **menor
   identificador** (para que el veredicto sea reproducible) y el diccionario lleva **seis** campos. Si
   añades uno, **pásalo por nombre**.
3. **El orden de declaración de rutas**: `/plan` antes que `/{receta_id}` y `/rango` antes que
   `/{fecha}`. Si se invierte, FastAPI lee la palabra como un identificador y el fallo aparece solo
   cuando alguien pide esa ruta. Hay prueba de las dos.
4. **`docs/SUPERAPP-ESTADO.md`**: comprueba que el resumen vigente **no repita como pendiente nada ya
   hecho** —el encargo lo pide expresamente— y que cada cifra lleve al lado su límite.
5. **`tests/`**: hay pruebas que leen el código a propósito (colores, títulos, montaje, 16 px). No las
   borres: son las que cazan lo que no da error.
