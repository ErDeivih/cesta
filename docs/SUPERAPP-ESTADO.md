# SUPERAPP · Estado del trabajo

## Revisión posterior — 8 de octubre de 2026

Leer [la revisión del código y correcciones](SUPERAPP-REVISION-2026-10-08.md)
antes de continuar desde `a32957e`. Se corrigieron subtotales independientes
por nutriente, ausencia frente a cero en el rango, números no finitos y el
mensaje que equiparaba entradas registradas con toda la ingesta del día.
Las correcciones permanecen en el árbol de trabajo, sin commit de esta revisión.

Prioridades detectadas: routers de Recetas/Diario sin sesión ni propietario;
referencia de identidad por cadena en lugar de referencia solicitada;
alternativas que siguen entrando en costes; candidato seleccionado antes de
evaluar la promoción por cantidad. Estos hallazgos impiden considerar S07–S09
terminados y deben resolverse antes del ensayo multiusuario o de activar identidad.
Las pantallas propias ya construidas se conservan. La verificación de esta
revisión se registra en SUPERAPP-REVISION-2026-10-08, sin reutilizar cifras previas.

Verificación posterior ejecutada: **1.318 pruebas aprobadas**, ruff limpio,
build frontend correcto y seis pruebas de cocina aprobadas. Persisten dos
avisos de dependencias y el aviso de tamaño del paquete frontend. No se
ejecutó el ensayo de navegador ni se probaron cuentas contra las bases reales.

Encargo vigente: `docs/SUPERAPP-00-EMPEZAR-AQUI.md` (7 de octubre de 2026), con
`SUPERAPP-01` (diseño y producto), `SUPERAPP-02` (datos, Lidl e identidad) y `SUPERAPP-03`
(investigación y límites). Este fichero es el estado vivo: se actualiza **antes de cada pausa**
y es lo primero que hay que leer al retomar.

Reglas de lectura de este fichero: **terminado** = cumple su criterio de aceptación con evidencia ·
**verificado** = se ejecutó y pasó, pero no cubre todo el paquete · **pendiente** = no empezado.
No se mezclan las tres.

---

## Bitácora de la sesión SUPERAPP (commits, con lo que hizo cada uno)

| commit | qué dejó |
|---|---|
| `e50f04c` | **S00**: baseline congelado. Los cambios heredados se verifican y se preservan; 1.195 pruebas |
| `5b66bf2` | Fichero de estado vivo: plan S00–S12, decisiones cerradas, correcciones a las referencias de Stitch |
| `dcde817` | **S01**: publicación por versiones (carpeta por versión, puntero atómico, `rutas()` fija la versión por petición, rollback) + catálogo actual adoptado como primera versión |
| `247a9cc` | **S02 núcleo**: cola de fichas en SQLite (estados, *lease* con vencimiento, hash, evidencia, reenganche sin duplicar) |
| `9f06396` | **S02 medido**: inventario de 74.861 fichas desde bronze en 75,7 s (antes: sin terminar) |
| `6bfdfd1` y `fb4dc6a` | **S02 instrumento**: informe de cobertura por fuente con deuda de cola y edades |
| `240bad4` | **S03 primera mitad**: descubridor de Lidl (sitemap guardado, clasificación por *slug*, sin red) |
| `42683e7` | La «cuna» suelta fuera de la política: tercera vez que la trampa de las tildes mordía; queda cubierta por pruebas |
| `edb4d2d` | **S03 medido**: el sitemap real, 6.622 direcciones → 691 incluidas, 1.568 de bazar evitadas, 4.363 a revisión |
| `e09f5d3` | **Puente S03→S02**: lo descubierto entra en la cola con su evidencia; el bazar no genera trabajo |

**Lo que la puerta ha parado**: seis commits que habrían metido una regresión o una prueba mal
escrita. La práctica es: las pruebas corren **antes** del commit y si no pasan, no se commitea.

## Resumen vigente (14 de octubre de 2026) · los cuatro defectos, cerrados y probados

**Los cuatro defectos que impedían cerrar identidad y coste están corregidos**, cada uno con pruebas de
comportamiento y **vistas rojas antes** de tocar el código:

| # | defecto | arreglo | commit |
|---|---|---|---|
| 1 | la autorización guardaba un sí/no, no **qué** alternativa se aceptó | migración `012` (producto y cadena, con una regla en la base que rechaza un sí sin producto), `autoriza_linea` que lo exige y lo guarda, endpoint que lo recibe, cruce único a las líneas, y `_es_la_confirmada` que **pide confirmación nueva si el motor propone otra** | `6f5c04d`, `6daf219`, `e2b97a8`, `1416867`, `b8baeb1`, `1b882aa` |
| 2 | el canónico se construía por `(grupo, fuente)` | una referencia **por grupo, igual en todas las cadenas**; **el producto pedido manda** cuando la línea lo registra (por producto o por grupo); y **el alta guarda el miembro que enseña la ficha** | `565e7cf`, `b2c5d04`, `5a13436`, `2e75ddd` |
| 3 | dos líneas del mismo producto se pisaban | las cantidades **se suman**: pedir 2 y 3 es pedir 5 | `b7fd14a` |
| 4 | la publicación no publicaba | la pasada **publica lo que escribe**, así que el puntero deja de quedarse viejo | `25ee6bc` |

**Lo que se midió al arreglar el 2, y conviene no perder:** la ficha enseña el miembro **más barato por
unidad** y el motor comparaba contra el de **identificador más bajo**; son productos distintos en cuanto los
precios no acompañan. Se arregló **guardando** el miembro mostrado, no unificando la regla: «el más barato»
cambia con los precios todos los días, y atar la identidad al precio habría sido peor que el defecto.

### El orden del dueño: tres de cuatro verificados, y los puentes hechos

| # | punto | estado |
|---|---|---|
| 1 | el ensayo reparado: la compra **por su identificador** y por **las líneas realmente marcadas** | **verificado** (`TODO BIEN`) |
| 2 | aislamiento y autorización con **dos cuentas** y almacenamiento real | **verificado** (`TODO BIEN`) |
| 3 | **copia y restauración** en un entorno separado, comprobando su contenido | **verificado** (`TODO BIEN`; `plataforma/prueba_copia.py`) |
| 4 | puentes con confirmación e idempotencia, y las gráficas | **puentes hechos**; **gráficas: plan asentado** |

Los puentes, todos con pruebas de comportamiento:

- **favoritos → lista**: ya **no duplica**, y dice cuántas había (`dde6742`).
- **plan → lista**: **vista previa** (`4a82d81`) y **acción** (`b7faa4d`), compartiendo el cálculo. Los
  ingredientes salen de **la versión que el plan guardó**, y la cantidad va **a la nota** —la lista cuenta
  envases y la receta habla en gramos—.
- **consumir → diario**: **previa con la cobertura dicha** (`7b1be32`) y **acción** (`54d8289`), idempotente
  por el identificador de la línea de compra, y **sin inventar calorías**: la previa dice si hay datos de
  nutrición, no cuántos, y sacar los números del texto es otra pieza.

**Y el diario rechaza el tipo `compra` a propósito** —*comprar no es comer*—, que es la razón de que este
puente **proponga** en vez de copiar.

### Lo que queda

1. **Las gráficas**: que la serie lleve **medida** (precio por unidad), **cobertura** (cuántos puntos y sobre
   qué tramo, y callar si son pocos) y **universo** (el grupo o producto y las cadenas que entran), y que
   `Chispa.tsx` —una chispa **sin ejes**— los enseñe como **texto accesible**. El principio ya está escrito en
   `alertas.py`: *«sin histórico suficiente no se inventa un mínimo: se calla»*.
2. **El recorrido completo de las tres aplicaciones**, que es lo que queda del criterio de cierre. El ensayo
   con dos cuentas y copia restaurada está superado; **«usables de punta a punta» no se demuestra con pruebas
   de unidad**, y por eso **ninguna condición se ha declarado cerrada**.
3. La **publicación**: la pasada ya publica desde `25ee6bc`, pero el catálogo servido seguirá diciendo
   incoherente hasta que corra una pasada (o alguien publique una vez).

### El método que ha funcionado, y el que no

- **Observar antes de suponer.** Casi todas las rondas perdidas fueron por suponer un nombre, una forma o una
  aridad. Cuatro veces bastó con **preguntarle al módulo** (o al catálogo) en vez de recordarlo.
- **Compilar el texto nuevo ANTES de escribirlo**, y **abortar sin escribir** si algo no cuadra: ha evitado
  dejar el árbol roto cinco veces.
- **Un invariante entre pasos** cuando el cambio es grande: comprobar que las claves no cambian antes de
  seguir. *Compilar demuestra la sintaxis, no que el bucle siga haciendo lo mismo.*
- **Ejecutar con `subprocess` y lista de argumentos** para escribir dentro de contenedores: PowerShell partió
  cinco comandos con comillas y acentos graves.
- **Un rojo puede ser la prueba**: ha pasado seis veces, y una de ellas me llevó a **revertir un arreglo que
  estaba bien**. La regla vale también antes de revertir.
- **Lo escrito no está verificado.** La primera ejecución del guion de la copia encontró un `TypeError` mío;
  el ensayo de punta a punta encontró tres fallos que 1.400 pruebas no veían.

**Suite: en verde, `ruff` limpio.** Medida en `54d8289` y posteriores.

## Resumen vigente (13 de octubre de 2026) · corrección: la condición 2 NO está cerrada

**Este documento dijo que la condición 2 estaba cerrada y no lo está.** El dueño contrastó los informes con el
código y la plataforma en marcha y encontró **cuatro defectos**. La culpa del cierre prematuro es mía, y lo que
importa es que el estado lo diga: **ninguna condición se da por cerrada hasta que estos comportamientos estén
probados.**

| # | defecto | estado |
|---|---|---|
| 1 | la autorización guarda un sí/no por línea y **no qué alternativa** se aceptó: el motor puede cambiar de producto y seguir autorizado | **pendiente** (necesita migración `012` con producto y cadena confirmados) |
| 2 | `_candidatos` sigue construyendo el canónico por `(grupo, fuente)`: **no compara contra el producto solicitado** | **pendiente** (es la primera frase del encargo y sigue en pie) |
| 3 | dos líneas del mismo producto con cantidades distintas **se pisaban** al elegir candidato | **CORREGIDO** (`b7fd14a`), con prueba vista roja primero |
| 4 | `/api/estado` declara `coherente: false`: precios del 8 con publicación del 7 | **pendiente** (detectar ya funcionaba; falta resolver la publicación) |

**Y una nota sobre el defecto 3, porque enseña:** no era un descuido, estaba **escrito como decisión** —*«si la
misma apareciera en dos lineas con cantidades distintas, manda la ultima: es una decision, no un descuido»*—.
El razonamiento no se sostenía: dos líneas del mismo producto se compran juntas, así que la oferta que conviene
se decide con **las unidades totales**. La prueba que lo fija no compara números, compara **el candidato
elegido**: pedir 2 y 3 tiene que dar el mismo que pedir 5.

**Cifra de la suite: 1.428 pruebas, 0 fallos, ruff limpio** (medida en `b7fd14a`, no después).

## Resumen vigente (12 de octubre de 2026) · relevo: tres condiciones cerradas y lo que falta

### Cerrado, con sus dos puertas

Las condiciones **1 (aislamiento), 2 (identidad y coste) y 3 (pantallas y persistencia)** están cerradas. Su
detalle está en los resúmenes de los días 9, 10 y 11, más abajo. La **condición 2** se cerró con la
**autorización de la sustitución persistida por línea**: migración `011_autorizar_la_alternativa.sql`, dos
funciones en `almacen.py`, un endpoint para confirmar que pide permiso de **escritura**, y la autorización
leída de la base en los sitios que calculan precios.

**La puerta, a partir de ahora, son dos cosas:** `uv run ruff check .` y `uv run pytest -q`. Las dos limpias.
Los dos `NameError` en producción que aparecieron los vio **ruff**, no la suite.

### La condición 4 ha encontrado dos fallos reales, y uno está arreglado

El **ensayo de punta a punta** (`plataforma/prueba_e2e.py`) es lo que los encontró. Los dos existían **con la
suite en verde**, porque las pruebas de `tests/` sustituyen PostgreSQL y no ejecutan esos caminos:

| fallo | estado |
|---|---|
| `/api/estado` devolvía una cadena suelta: el decorador envolvía a un ayudante insertado entre el decorador y su función | **arreglado** (`351c679`), con prueba de forma vista roja antes |
| la **lista de la compra** y el **cierre de compra** reventaban con `too many values to unpack`: `mejor` tiene claves `(grupo_o_producto, fuente)` y `(grupo_o_producto, "alternativa")`, y los dos lectores descomponían la clave como un par | **arreglado** (`15fddb4`) y **confirmado** por el ensayo: `estimacion sin reventar: True` |

Ese segundo fallo enseña lo que más vale de estas rondas: mi primer intento de arreglo fue **incorrecto** (dejó
9 pruebas en rojo y la puerta lo paró) porque **la prueba y el arreglo partían de la misma suposición** sobre la
forma de la clave. Se arregló al **observar** la forma real, leyendo dónde se construye `clave` en
`_candidatos`. **Primero se observa, después se escribe la prueba, y solo entonces se arregla.**

### Pendiente, con nombre

1. **Una expectativa desactualizada en el ensayo.** `cerrar la compra` imprime «la compra no ha quedado
   guardada» **y a continuación la compra guardada**, con el mismo `compra_id` y sus dos líneas. La compra sí
   se guarda: lo que está viejo es la comprobación. Se pone al día **comparando con la evidencia que ella misma
   imprime**, no retocando la aserción para que pase.
2. **Reconstruir la imagen de la API.** El ensayo ejecuta el código del árbol, así que lleva los arreglos; **la
   plataforma servida en el 8080 se construyó antes y sigue teniendo el fallo de la lista.** Va antes de dar la
   condición 4 por cerrada.
3. **Los tres huecos del ensayo**: copia de seguridad **restaurada** (no existe ningún `pg_dump`/restore),
   **dos cuentas** contra base real (el aislamiento se prueba con PostgreSQL sustituido) y **la autorización de
   verdad** (confirmar → recargar → sigue autorizada, que es el recorrido que hasta esta semana no existía).
4. **Puentes idempotentes con vista previa** y **gráficas con medida, cobertura y universo**, las otras dos
   piezas de la condición 4.

### El método que funciona, por si la próxima sesión empieza de cero

- **Observar antes de suponer.** Casi todas las rondas perdidas fueron por anclar o comparar sobre un recuerdo.
- **Ficheros enteros o edición por número de línea leído**, nunca parches sobre fragmentos recordados.
- **Ejecutar con `subprocess` y lista de argumentos** escribe SQL y código dentro de contenedores sin pelearse
  con el entrecomillado de PowerShell, que ha partido cinco comandos esta sesión.
- **Un rojo puede ser la prueba**: ha pasado seis veces. Se mira qué afirma antes de tocar el código.
- **Lo que las pruebas no ejecutan, el análisis estático sí lo ve**; y lo que está registrado y servido solo lo
  ve **usar la aplicación**.

**Suite: 1.424 pruebas, 0 fallos.** Ruff limpio. La plataforma servida, pendiente de reconstruir.

## Resumen vigente (11 de octubre de 2026) · un fallo que solo se veía usando la aplicación

**Lo que pasó, porque es lo más útil de esta etapa.** `/api/estado` devolvía **solo la cadena de la versión**
(`"20261007-161518"`) en vez del objeto de estado, **desde la ronda 17**. La causa: al insertar el ayudante
`_version_del_catalogo` lo puse **entre** `@app.get("/api/estado")` y `def estado():`, y un decorador envuelve
**a la función siguiente**. La ruta quedó atada al ayudante y **`estado()` nunca se registró**.

**Por qué la suite no lo vio, y esto es lo que hay que recordar.** Mis pruebas de esa ruta comprobaban que el
texto `"version_catalogo": _version_del_catalogo()` estaba **escrito en el fichero**… y lo estaba. El módulo
importa sin error. La función es correcta. **El fallo existía solo en el registro de la ruta**, que es un hecho
de ejecución. Resultado: **1.413 pruebas en verde y el endpoint roto en la plataforma servida.**

**Cómo se encontró:** usando la aplicación. La comprobación en navegador de la ronda 31 pasó por `/api/estado`,
y a partir de ahí la cadena de descarte fue: no es el proxy (los dos caminos coinciden), no es una imagen vieja
(huellas del fichero idénticas), es **a qué función está atada la ruta**.

**Cómo se cerró:** con la disciplina del proyecto. Primero la prueba, y **vista roja** contra el código roto
(3 fallos, uno de ellos comprobando directamente a qué función está atada la ruta); después el arreglo —el
decorador movido encima de `def estado():`—; y **vista verde**. Una prueba que no se ha visto roja no prueba
nada.

**Y comprobado en lo que de verdad se sirve**, tras reconstruir la imagen:

| camino | respuesta |
|---|---|
| host, 8080 (Caddy) | `dict` con las cinco claves, `fecha_datos: 2026-10-08`, **5 cadenas**, `version_catalogo: 20261007-161518` |
| dentro, 8000 (la API) | el mismo `dict` con las mismas claves |

Así que lo de las rondas 17 y 33 (versión del catálogo y vigencia del precio) está **vivo**, no solo en el
repositorio.

**Corrección de una nota mía desactualizada:** el estado decía que Docker estaba parado y que había que
levantar PostgreSQL cuando tocara esa pieza. **Llevaba 36 horas levantado** (`cesta-api-1`, `cesta-db-1` y
`cesta-web-1`, los tres sanos), y esa nota hizo perder una ronda. No hay nada que levantar.

**La lección, en una línea:** una prueba que **lee el código** no sustituye a una que **llama al endpoint**.
Hay fallos —este— que solo existen en lo que está registrado y servido, y para esos hacen falta la prueba de
forma, la comprobación en navegador y la plataforma real.

**Suite: 1.416 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, build correcto.

**Lo que queda del objetivo:**

1. **La persistencia** de la autorización de sustitución en la línea: último punto de la condición 2, sin
   obstáculo (PostgreSQL está levantado).
2. **Condición 4**: puentes explícitos e idempotentes con vista previa, gráficas con **medida, cobertura y
   universo**, y el **ensayo integral** con datos reales, **dos cuentas** y **copia restaurada**.

## Resumen vigente (10 de octubre de 2026) · condición 3 cerrada

**Condición 3 — pantallas y comportamiento persistente: CERRADA.** Pieza a pieza, con su evidencia:

| pieza | estado | dónde |
|---|---|---|
| el detalle por receta lee la receta **persistida de su ruta**, con **404 real** y versiones accesibles | hecho | `paginas/RecetaDetalle.tsx`, `tests/test_detalle_receta.py` |
| el módulo compartido **fuera** de las rutas de recetas y calorías | hecho | las tres secciones de recetas, el diario y las tendencias tienen pantalla propia |
| editar una receta, diciendo que **crea versión nueva** | hecho | `componentes/FormularioReceta.tsx`, `tests/test_editar_receta.py` |
| **errores al archivar**, con el motivo de la API | hecho | `paginas/Recetario.tsx`, `tests/test_archivar_errores.py` |
| **plan modificable**, incluido **quitar** una receta de un día | hecho | `quitar_del_plan` + `DELETE /plan`, `tests/test_quitar_del_plan.py` |
| **cálculo de raciones**, servidor y pantalla, con **las dos cifras** | hecho | `core/recetas.escala`, `tests/test_raciones.py`, `test_raciones_en_pantalla.py` |
| S09: **cobertura por nutriente**, y un nutriente sin dato se dice con la palabra | hecho | `paginas/Diario.tsx`, `tests/test_cobertura_en_pantalla.py` |
| S09: **tendencias con huecos en vez de ceros**, y sin media inventada | hecho | `paginas/Tendencias.tsx`, `tests/test_tendencias.py` |
| la versión del diario: **enlace verificado** y **procedencia** (`vinculada` / `manual` / `perdida`) | hecho | `plataforma/api/diario.py`, `tests/test_procedencia_diario.py` |

**Comprobación en navegador: hecha, 23 comprobaciones y 0 fallos** (`uv run python -m plataforma.prueba_suite`,
con el servidor de desarrollo en 5173). Y **no es una comprobación vieja**: `/recetas` y `/calorias` ya
renderizan las pantallas nuevas, así que verifica que **cargan en un navegador real con cero errores de
página**, además de navegación, teclado, foco atrapado, Escape, móvil a 390 y escritorio a 1280, recarga en
ruta profunda y las direcciones antiguas con su query. Capturas en `data/capturas-s06/`.

**Lo que esa comprobación NO es, dicho para no confundirlo:** no es un recorrido funcional completo. No crea
una receta ni anota un día. Eso es el **ensayo integral de S12** —datos reales, **dos cuentas** y **copia
restaurada**—, que sigue pendiente.

**Suite: 1.408 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, `npm run build` correcto.

**Lo que queda del objetivo:**

1. **D, segunda mitad**: que la fecha de cada precio **pertenezca** a la versión del catálogo (la versión ya se
   informa en `/api/estado` desde la ronda 17).
2. **La persistencia** de la autorización de sustitución en la línea: necesita **PostgreSQL** levantado, y se
   levanta cuando toque esa pieza.
3. **Condición 4**: puentes explícitos e idempotentes con vista previa, gráficas con **medida, cobertura y
   universo**, y el **ensayo integral** con dos cuentas y copia restaurada.

## Resumen vigente (9 de octubre de 2026) · condiciones de la revisión

**Condición 1 — aislamiento por usuario: CERRADA.**

| qué | evidencia |
|---|---|
| Recetas: propietario **obligatorio** en crear, leer, listar, versiones, cambiar, archivar, planificar y plan | `core/recetas.py`, con el propietario como parámetro **sin valor por defecto** |
| Versiones y plan **heredan** el permiso de la receta (se llega por `receta_id` y lo primero es comprobar que es tuya) | `core/recetas.py`, `plataforma/api/recetas.py` |
| Diario: propietario obligatorio en apuntar, día, borrar y rango | `core/diario.py` |
| **401** para el anónimo en todos los endpoints de las dos aplicaciones | `tests/test_aislamiento.py` |
| **B contra A**: no enumera, no lee, no cambia, no archiva, no ve versiones, no planifica; borrar adivinando el identificador da **404**, no 403 | `tests/test_aislamiento.py` |
| El propietario **no se puede dictar** en el cuerpo de la petición | `tests/test_aislamiento.py` |
| Migración `ALTER TABLE ADD COLUMN`, **repetida 3 veces**, conservando el histórico (700 kcal, 6 raciones) con propietario **NULL** y **sin asignárselo a nadie** | `tests/test_aislamiento.py` |
| La **caché** se vacía al cambiar de cuenta y el vigilante va antes que la aplicación | `api/cuenta.ts`, `main.tsx`, `tests/test_cache_por_cuenta.py` |
| El usuario dentro de la clave en las cuatro pantallas nuevas | `api/recetas.ts`, `api/diario.ts` |

**Suite: 1.326 pruebas, 0 fallos.** Ruff limpio, `tsc` limpio, `npm run build` correcto.

**Pendiente de verificación, dicho para no confundirlo:** la comprobación **en navegador**
(`uv run python -m plataforma.prueba_suite`) no se ha pasado desde el aislamiento; necesita el servidor
de desarrollo levantado.

**Condición 2 — identidad solicitada y selección del coste: CERRADA** salvo dos cosas que
dependen de otras (abajo, dichas).

| caso | estado | evidencia |
|---|---|---|
| **A** grupo antiguo con dos marcas incompatibles | **hecho** | mismo GTIN con marcas distintas → **cuarentena**; sin GTIN, dos productos; marca vacía no inventa conflicto. `core/identidad.py`, `cesta.py`, `tests/test_marca_en_identidad.py` |
| **B** alternativa más barata **no autorizada** | **hecho**: regla, total por cadena, reparto, respuesta **y pantalla** | `Eleccion.autorizada`, `Peticion.autorizado` por línea, `_total_autorizado` con `pendientes`, `sin_autorizar` **en el orden**, `_serializa` con `identidad`/`motivo`/`autorizada`/`alternativa`, y el aviso que dice **qué se puede pedir y por cuánto**. 5 + 4 + 4 + 3 + 4 pruebas |
| **C** dos unidades donde el envase caro gana por promoción | **hecho** | coste final de las unidades pedidas, 150 frente a 180, en una función pura. `cesta.py::_coste_para`, `tests/test_seleccion_por_coste.py` |
| **D** precio o promoción futura | **parcial** | `fecha_tope` corta particiones posteriores de promoción (S05). **Falta**: fecha del precio y versión del catálogo |
| **E** variantes bajo el mismo GTIN | **hecho** | el motor las distingue **y** la selección ya no descarta la exacta: `_prefiere` hace que una exacta gane a una alternativa más barata, y la alternativa se guarda aparte. `tests/test_variante_no_tapa_la_exacta.py` |

**Lo que queda de la condición 2, y por qué no está hecho:**

1. **D, resto** — fecha del precio y versión del catálogo, además de la partición de promoción. Se puede
   hacer sin base de datos.
2. **La persistencia de la autorización en la línea** — hoy `Peticion.autorizado` viaja en la petición;
   falta guardarlo en la línea de la lista para que sobreviva a una recarga. **Depende de PostgreSQL**
   (la lista vive en `almacen`), y con Docker parado **no se puede probar de verdad**: no se declara hecho
   antes de poder probarlo.

**Y queda pendiente, de antes:** la comprobación **en navegador** (`plataforma/prueba_suite`), que no se
ha pasado desde el aislamiento por usuario porque necesita el servidor de desarrollo levantado.

## Cierre de la etapa (7 de octubre de 2026) · ronda 60 de 60

El objetivo **no está cumplido y sigue activo**: de los trece paquetes hay cuatro tocados y nueve sin
empezar. Lo que sigue es el estado real, sin adornos, y una valoración en los tres ejes que el encargo
separa a propósito: **función**, **calidad y cobertura del dato** y **operación y seguridad**. Un build
verde no certifica los otros dos.

### Estado por paquete

| paquete | estado | una línea |
|---|---|---|
| **S00** baseline | **hecho** | cambios heredados verificados y preservados; 1.195 pruebas de partida |
| **S01** publicación versionada | **hecho** | versión con puntero atómico, `rutas()` fija la versión por petición, rollback y concurrencia probados; catálogo real adoptado como primera versión |
| **S02** cola de fichas | **hecho** | SQLite con estados, *lease* con vencimiento, hash, evidencia y próxima revisión; inventario de **79.915** desde bronze en 75,7 s; informe de cobertura |
| **S03** Lidl | **en curso** | sitemap medido (6.622 → 691 incluidas, 1.568 de bazar evitadas, 4.363 a revisión) · ficha real y lector de JSON-LD con **GTIN validado** · **la cola pide fichas** (28 con ficha y hash, 5.026 pendientes) · cobertura de nutrición sobre 26 (0/26) · medidor con pruebas |
| **S04** identidad | **sin empezar** | el laboratorio de la ampliación es diagnóstico, no el algoritmo; el matching actual sigue siendo el anterior |
| **S05** selector único | **sin empezar** | primer arreglo ya localizado: **`_candidatos` recibe `fecha_tope` y no la aplica**, y sus llamantes pasan cadena vacía |
| **S06** armazón | **sin empezar** | sin menú lateral todavía; las correcciones a las referencias de Stitch están listadas (sin 11 px, sin datos ficticios, sin recursos externos) |
| **S07–S12** | **sin empezar** | Compra, Recetas, Calorías, puentes, gráficas y ensayo integral |

### Valoración honesta de preparación para un despliegue futuro

**Función: no.** No hay interfaz nueva construida. Las tres aplicaciones (Compra, Recetas, Calorías)
**no existen como tales**: siguen sin menú lateral, sin rutas separadas y sin las pantallas del
contrato. Lo que sí funciona es la **tripas de datos** que las sostendrá. Un despliegue hoy no tendría
nada que enseñar al usuario.

**Calidad y cobertura del dato: parcial, y con lo que falta medido.** El alcance, la cola, el
inventario y la publicación versionada están hechos y probados. Pero **la nutrición no está**: en Lidl
0 de 26 fichas la publican, y en el catálogo actual está a cero en Alcampo, Carrefour y Aldi. **La
identidad exacta (S04) no ha empezado**, así que las comparaciones entre cadenas siguen apoyadas en el
emparejador anterior: la regla del encargo —no sustituir un producto concreto sin elección explícita—
está en el contrato y **no implementada**. Y de las 79.915 fichas del inventario, **28 tienen ficha**.

**Operación y seguridad: sin verificar para un despliegue.** No hay despliegue público (correcto,
estaba fuera de alcance), **no hay credenciales en el repositorio**, y las peticiones se han hecho con
presupuesto, ritmo, robots respetado y sin bucles. Pero **no se ha probado ninguna copia de seguridad
restaurada**, **no se ha hecho el ensayo de dos cuentas** contra filtración, y la plataforma web **no
está levantada**. Eso es exactamente lo que S12 pide y no se ha hecho.

**Conclusión:** el proyecto está **más cerca que al empezar la etapa** —hay cimientos de datos
medidos, con pruebas y con límites escritos— y **no está listo para un despliegue**, ni público ni
doméstico serio. La distancia no es de semanas de trabajo: es de construir S06 a S12 y de cerrar S03 y
S04.

### Lo que falta, en orden, con el primer paso concreto

1. **S03, cerrar**: estratificar la muestra de fichas por familia (los 5.026 pendientes están en orden
   de identificador, que no es una muestra) y resolver los 4.363 a revisión **con la ficha**.
2. **S04, identidad exacta**: candidatos por GTIN —los de Lidl ya se validan— y por marca+familia+
   formato, veto de contradicciones, abstención como resultado válido, banco independiente y
   **publicación en sombra** antes de tocar nada de listas.
3. **S05**: aplicar `fecha_tope` en `_candidatos` y en todos sus llamantes, que hoy pasan cadena vacía.
4. **S06**: el armazón con menú lateral, respetando `SUPERAPP-01` y las correcciones a Stitch.
5. **S07 a S12**: las tres aplicaciones, los puentes, las gráficas y el ensayo integral.

### Cómo retomar

Primero **`uv run pytest -q` y `uv run ruff check .`** (la última suite completa verificada es
**1.243**). Después leer este fichero de arriba abajo: lleva la bitácora de commits de la etapa, lo que
está medido con su número, las decisiones cerradas que no se vuelven a preguntar y los límites dichos
al lado de cada cifra. La única dependencia externa es **Docker**, que hoy está parado, y solo hace
falta para verificar recorridos de interfaz.

## Paquete actual

**S03 · Lidl — PRIMERA MITAD HECHA.** Siguiente: **las fichas de los 5.054 candidatos** (S03, segunda mitad).

## Baseline (S00)

| dato | valor |
|---|---|
| commit | `e50f04c` (S00 baseline: los cambios heredados, verificados y preservados) |
| padre | `f74c432` (muro al día) |
| `uv run pytest -q` | **1.195 pruebas en verde**, 2 avisos de dependencias |
| `uv run ruff check .` | limpio |
| `uv run python -m projects.cesta.verificar_docs` | verde (166 comandos comprobados) |
| árbol | limpio |

**Cambios heredados que se preservaron tal cual** (no son míos y no se reescriben):

- `core/schemas.py`: `ProductoRaw.disponible` pasa a `bool | None` — distinguir «no sé» de «sí».
- `projects/cesta/collectors/dia.py`: conserva tablas nutricionales **parciales** sin inventar los
  nutrientes ausentes, y exige finito y no negativo.
- `core/datos/alcance.yml`, `core/datos/secciones.yml`, `docs/CIFRAS.md`: al día.
- `projects/cesta/collectors/lidl.py`: ampliado (sitemap y fichas) — **leer antes de tocarlo**.
- `plataforma/web/app/*`: `App.tsx`, `Cabecera.tsx`, `Producto.tsx`, `BotonAnadirACesta.tsx`,
  `package.json` con preparación de pantallas.

**No hay credenciales en el repositorio.** Las claves que circulan por el chat de origen deben
revocarse fuera del repositorio; aquí no se guardan ni se piden.

## Plan de paquetes (orden de dependencias)

| ID | estado | nota |
|---|---|---|
| S00 baseline | **terminado** | commit `e50f04c`, puertas ejecutadas |
| S01 publicación versionada | **terminado** | `core/publicacion.py`: versión con puntero atómico, `rutas()` fija la versión de una petición y fallback al catálogo suelto; 8 pruebas de aceptación |
| S02 cola de fichas | **núcleo hecho y medido** | `core/inventario.py` en SQLite: alta idempotente, lease con vencimiento, estados del contrato, próxima revisión, hash y evidencia; enganche desde bronze histórico. Falta: medir el inventario real y que los colectores consulten la cola |
| S03 Lidl por sitemap y fichas | **en curso**: sitemap medido (6.622 direcciones, 691 incluidas, 1.568 excluidas, 4.363 a revisión) | `projects/cesta/descubrir_lidl.py`: lee un sitemap guardado, separa fichas de categorías, clasifica por *slug* con la política (bazar inequívoco fuera, comida nunca fuera por su URL) e informa en direcciones y no en alimentos. Falta: recorrer el inventario real y las fichas |
| S04 identidad y banco independiente | pendiente | depende de S02 |
| S05 selector único y optimizador | pendiente | depende de S04 |
| S06 armazón y sistema visual | pendiente | **no depende de S01**; puede ir en paralelo |
| S07 Compra | pendiente | depende de S05 y S06 |
| S08 Recetas | pendiente | depende de S02 y S06 |
| S09 Calorías | pendiente | depende de S02, S06 y S08 |
| S10 puentes entre aplicaciones | pendiente | depende de S07–S09 |
| S11 gráficas y rendimiento | pendiente | depende de S07 y S09 |
| S12 ensayo integral y cierre | pendiente | depende de todo |

## Decisiones cerradas (no volver a preguntarlas)

- Menú lateral de aplicaciones en escritorio; cajón accesible en móvil.
- React/Vite/TypeScript y backend actual; sin migrar de framework.
- Datos e infraestructura locales; sin despliegue público ni servicios de pago.
- **Calorías es privada por persona**, aunque Compra sea del hogar.
- Un ingrediente genérico no es un producto comercial exacto. **Comprar no es consumir.**
- Prioridad a la precisión: **la abstención es un resultado válido**.
- Aprovechar el crudo histórico antes de pedir; renovar fichas conocidas por cola.
- No buscar paridad artificial de filas con Aldi.
- v0 ya dio la dirección visual; **no consumir más cuota**. Stitch es referencia, no código.

## Correcciones obligatorias al portar las referencias de `.stitch/`

1. Colores y tamaños de `SUPERAPP-01` §1; **rechazar los 11 px** de Stitch (mínimo 13 px en
   metadatos, 14 px en tablas, 16 px en cuerpo). Borde suave `#D8D2C7` **solo** decorativo: no
   delimita un control (contraste 1,43:1).
2. Compra: el panel derecho sale cortado en la referencia; lenguaje cotidiano («Mi lista»,
   «Tiendas», «Total estimado»), sin «gasto provisionado» ni «referencia mercantil».
3. Compra: **eliminar afirmaciones ficticias** de auditoría de tickets, comprobación física y
   producto exacto verificado. Precio ausente ≠ sin stock. Promociones con condiciones y cálculo.
4. Recetas: «Preparar lista» **abre una propuesta que se confirma**, no añade sola. Cambiar
   raciones escala unidades y recalcula cobertura nutricional.
5. Calorías: conservar «subtotal conocido» y el día sin datos como **hueco**. Los datos de la
   captura son de ejemplo.
6. El HTML descargado usa recursos externos: **no pegarlo**; portar componentes y servir local.
7. Las tres referencias son de escritorio: verificar 390 y 768 px, zoom 200 % y teclado.

## Problemas pendientes conocidos

- **T03 (identidad) sigue sin empezar** y es lo que gobierna que las comparaciones sean correctas.
  1.014 candidatos por GTIN y 10.999 pares con contradicciones medidos en el laboratorio.
- **T11**: la ficha ya llega en Carrefour, DIA y Aldi y se tira al parsear; en Alcampo no llega.
  Falta la extracción con procedencia y fecha por campo.
- **Lidl**: el colector existe y está probado sin red; la primera captura real está pendiente y
  `--escribir` está detrás de una bandera porque la pasada diaria **descubre** las cadenas.
- **La plataforma web no está levantada** (Docker parado); los recorridos de interfaz se verificarán
  cuando se levante o con el servidor de desarrollo.
- Sin medir todavía: `plataforma/web/app` `npm run build` y `npm run test:cocina` en este baseline.

## S01 · Publicación versionada — HECHO (7 de octubre de 2026)

`core/publicacion.py`. Cómo cumple su criterio:

| exigencia de S01 | cómo se cumple |
|---|---|
| caída entre escrituras no mezcla versiones | cada publicación escribe en `data/gold/v<fecha-hora>/` y el **puntero** (`actual.json`) se cambia con `os.replace` **solo** cuando están todos los ficheros; si falla, la carpeta a medias se retira y el puntero no se mueve |
| rollback probado | las versiones no se borran; `fijar(version)` vuelve a una anterior y rechaza una incompleta |
| concurrencia probada | `rutas()` resuelve la versión **una vez** y devuelve todos los caminos de esa misma publicación: una petición no puede mezclar `grupos` de una con `enlaces` de otra |
| no romper lo que hay | sin puntero se lee el catálogo suelto de siempre (fallback conservador) |

Publicar **no borra** y una versión existente **no se sobrescribe**. 8 pruebas de aceptación en
`tests/test_publicacion.py`.

**Pendiente dentro de S01**: el pipeline todavía escribe los ficheros sueltos; hay que hacerlo
publicar por versiones y que la API lea con `rutas()`. Se hace al entrar en S02/S05, para no tocar
la tarea de las 06:00 a la vez que se cambia la lectura.

## S02 · Cola de fichas — núcleo hecho y medido (7 de octubre de 2026)

`core/inventario.py` + `tests/test_inventario.py` (9 pruebas). Lo que aporta y lo que se midió:

| cosa | valor |
|---|---|
| **inventario levantado del bronze histórico** | **74.861 fichas**, sin una sola petición de red |
| alcampo | 43.603 |
| carrefour | 17.283 |
| dia | 6.292 |
| mercadona | 4.477 |
| aldi | 3.206 |
| tiempo del enganche | **75,7 s** (antes: más de 710 s de CPU y sin terminar) |

**Ese 74.861 no es el surtido de ningún supermercado**: es lo **descubierto** en el histórico, la unión
de todas las capturas. Hoy el catálogo tiene 51.659 productos, así que el inventario es un 45 % más
grande: son productos que aparecieron en alguna captura y no están en la de hoy. Es justo para lo que
existe el inventario —no perder de vista lo que un día se vio— y es el denominador honesto para hablar
de cobertura, en lugar de contar filas de un día.

**Dos fallos propios que se corrigieron aquí, y cómo se encontraron:**

1. La evidencia reventaba si el bronze estaba fuera del repositorio (lo cazó la prueba del enganche
   con un bronze temporal: justo donde se prueba).
2. El enganche hacía un *upsert* por **(día, producto)**: millones de escrituras para guardar dos
   fechas, porque bronze guarda la misma ficha treinta días seguidos. Se agregó en memoria
   (primera y última fecha por producto) y se escribe una vez por fuente: de no terminar a 75,7 s.
   **Cambio de contrato declarado**: `enganche()` devolvía altas procesadas y ahora devuelve
   **productos distintos**, que es el dato que interesa; su prueba lo explica.

**Instrumento añadido**: `projects/cesta/informe_inventario.py`, el panel de cobertura por fuente
(descubiertos, sin ficha, con ficha, con contenido útil registrado y vencidas, más las edades por
tramos). Es lo que pide SUPERAPP-02 §8, es de solo lectura y no toca la pasada diaria.

## S03 · Lidl, primera medida real (7 de octubre de 2026)

`projects/cesta/descubrir_lidl.py` bajó el sitemap público **una vez** (robots.txt primero, una sola
petición, y el XML guardado para repetir el análisis sin red) y lo clasificó por el *slug* de cada
dirección. Resultado:

| medida | valor |
|---|---|
| direcciones en el sitemap | **6.622** |
| fichas de producto (no son categorías) | 6.622 |
| **incluidas por la política** | **691** |
| **excluidas (bazar inequívoco)** | **1.568** |
| **a revisión (la URL no decide)** | **4.363** |

**Lo que esto demuestra, que es justo lo que el encargo avisaba de no suponer:** 6.622 direcciones
**no** son 6.622 alimentos. Solo 691 entran sin más; 1.568 son bazar claro —carros de jardín,
colchones hinchables, tijeras de podar— y **se evitan sin pedir ni una ficha**, que es el objetivo de
esta mitad del paquete. Y **4.363 no se pueden decidir desde la dirección**: el sitemap de Lidl usa
slugs largos y a menudo en alemán, y forzar una decisión ahí sería inventar.

**Lo que no dice:** nada sobre el surtido. Es **catálogo público descubierto**, con cobertura
desconocida, y una dirección tampoco prueba que la página viva (el encargo documenta un 404 en el
mismo sitemap). La cobertura real la dirá la otra mitad de S03: las fichas.

**Puente hecho (7 de octubre de 2026)**: lo descubierto se da de alta en la cola de fichas (`--registrar`), con su evidencia; los incluidos y los que quedan a revisión entran como candidatos, y el bazar inequívoco se cuenta pero **no genera trabajo**. Así el recorrido completo queda: sitemap → inventario → informe de cobertura.\n\n**Pendiente de S03**: (1) las fichas de ese inventario, con cola y presupuesto, para resolver los
4.363 y traer ingredientes y nutrición; (2) el informe por fuente y familia; (3) las ofertas
semanales como segunda corriente, sin confundir «producto conocido» con «precio de hoy».

**Pendiente dentro de S02** (es lo que lo hará útil de verdad): que los colectores **consulten la
cola** —pedir ficha a quien le falta, renovarla a quien le vence y no volver a pedir la que está
correcta y en plazo— y el informe diario de cobertura por fuente y familia. Hasta entonces esto es
memoria escrita, no renovación.

### Lo que trae la ficha de Lidl, medido (7 de octubre de 2026)

Leído el fixture guardado (`data/lidl-ficha-ejemplo.html`), sin red. Trae **tres** bloques de datos
estructurados, y solo uno es del producto:

    [0] @type=Product        name, brand, description, gtin13, sku, image, offers, url
    [1] @type=Organization   LIDL
    [2] @type=Organization   Lidl (con el programa de socio)

**Tres consecuencias, y las tres cambian el plan:**

1. **Hay `gtin13`.** La ficha de producto **sí trae código de barras**, que la página de ofertas no
   traía. Eso alimenta directamente la identidad de S04: un GTIN válido y con procedencia es la vía
   fuerte para decir «este es el mismo producto en otra cadena».
2. **`sku` (11000174) no es un EAN.** Es el identificador interno. El contrato lo prohíbe
   expresamente y ahora está visto en el dato, no supuesto: confundirlos envenenaría las
   comparaciones.
3. **No trae ingredientes ni nutrición.** El JSON-LD da identidad, descripción y ofertas; la ficha
   nutricional tendrá que salir del **cuerpo HTML** o de otra fuente. Para T11 esto significa que las
   fichas de Lidl darán identidad y precio, y habrá que medir aparte cuánta nutrición publica.

Y dos cuidados que ya están escritos para el lector: la `description` viene con **HTML** (hay que
sanitizarla, no pintarla) y `offers` es una **lista** (varias condiciones: normal y club, con fechas).

**Pendiente inmediato**: escribir el lector sobre el fixture (producto → campos de bronze) con
`gtin13` validado, `sku` **nunca** como EAN, `description` saneada y las condiciones de `offers`
separadas. Y después medir cuánta nutrición hay en el HTML de la ficha, sin darla por hecha.

## S03 · El lector de fichas, funcionando sobre una ficha real (7 de octubre de 2026)

`projects/cesta/ficha_lidl.py` lee el JSON-LD de la ficha y lo convierte en campos del proyecto. Sobre
la ficha real guardada (`data/lidl-ficha-ejemplo.html`):

    nombre: Galletas rellenas · marca: SONDEY · descripción: Rellenas de crema de chocolate.
    id_fuente: 11000174 (sku, identificador interno)
    ean: 4056489574392   <- GTIN válido, dígito de control comprobado
    precio_cent: None    <- y no se ha inventado
    condiciones: 1 oferta con availability=InStoreOnly y SIN importe

**Dos hallazgos que cambian el plan:**

1. **La ficha de producto de Lidl da códigos de barras de verdad.** El `gtin13` pasa la validación del
   dígito de control, así que **S04 tiene por fin una vía fuerte de identidad** con una cadena: GTIN
   válido y con procedencia. Y queda visto en el dato que `sku` no es un EAN.
2. **Esa ficha no publica precio.** Su oferta dice `availability: InStoreOnly` y no trae importe. El
   lector devolvió vacío en vez de inventar un precio, que es exactamente la distinción del encargo:
   **reunir fichas y disponer de precios actuales son trabajos diferentes**. La aplicación podrá
   conocer un producto de Lidl sin fingir que sabe cuánto cuesta hoy.

**Decisiones del lector, cada una con su prueba:** `gtin13` validado (el que no cuadra no se usa pero
tampoco se tira en silencio: se guarda aparte), `sku` jamás como EAN, `description` convertida a texto
en vez de pintada, y **dos condiciones de oferta no se funden en un precio**. Nueve pruebas en el
fichero, seis nuevas. Suite completa: **1.233 en verde**.

**Pendiente inmediato de S03**: la cola mandando (pedir fichas a los 691 incluidos con presupuesto por
host y día, guardar hash del contenido útil y versión de parser, próxima revisión a 30 días) · medir
cuánta nutrición publica Lidl en el **cuerpo HTML**, sin darla por hecha · resolver los 4.363 a
revisión **con la ficha, no con el slug** · informe por fuente y familia.

## S03 · ¿Publica Lidl nutrición? Medido, y con reservas (7 de octubre de 2026)

Sobre el fixture guardado, buscando **estructuras** y no palabras sueltas (que es la advertencia del
propio encargo):

| búsqueda | resultado |
|---|---|
| campos de una tabla nutricional española (energía, grasas, saturadas, hidratos, azúcares, proteínas, fibra, sal, kcal, kJ…) | **1 de 12**, y el que aparece es `kj` ×2 |
| bases que hacen interpretable una tabla (`por 100 g`, `100 ml`, porción con peso) | ninguna base real; `porción`/`ración` son texto de interfaz |
| señales de ingredientes (la palabra, harina, azúcar, aceite, cacao) | **0 de 6** — en un producto que **es una galleta** |

**Conclusión provisional: la ficha de producto de Lidl no publica la ficha nutricional.** Da
identidad (GTIN válido), nombre, marca, descripción, imagen y ofertas; la nutrición no está.

**Y el límite de esta medición, que importa tanto como el resultado:** es **un** producto. Un producto
no es la fuente. Para poder decir «Lidl publica poca nutrición» hacen falta **varias fichas
estratificadas** (frescos, envasados, droguería) y contarlo como cobertura, no como conclusión de
catálogo. Mientras tanto se dice **una ficha medida**, no una tendencia.

**Consecuencia para T11**: si se confirma, Lidl aportará **identidad y precio** a la plataforma y su
nutrición será una **limitación de fuente** que se declara —no se rellena desde otra fuente sin
decirlo, y no se presenta como dato propio—.

## S03 · Cobertura de nutrición sobre seis fichas (7 de octubre de 2026)

Ya no es un producto. El colector guarda ahora **una copia por producto** (`data/fichas-lidl/<id>.html`),
así que las fichas se acumulan y el análisis es **offline y repetible**. Sobre las seis primeras,
sacadas de la cola con presupuesto:

| medida | resultado |
|---|---|
| fichas guardadas | **6** |
| **con datos estructurados de producto** | **6/6** — el lector las lee todas |
| con tabla nutricional (3+ campos) | **0/6** |
| con base interpretable (`por 100 g`) | **0/6** |
| con ingredientes (2+ señales) | **0/6** |

**Qué permite decir esto:** la ficha de producto de Lidl es **fiable para identidad** (GTIN, nombre,
marca, descripción, imagen, ofertas) y **no trae la ficha nutricional** en las seis medidas.

**Qué no permite decir:** que sea así en todo el surtido. Son **seis fichas de 5.046 candidatos**, y
la muestra no está estratificada por familia (frescos, envasados, droguería). Se dice cobertura de
esta muestra, no una propiedad de la cadena.

**Progreso de la cola con estas rondas**: `correcto` pasó de 0 a **8**, y quedan **5.046**
pendientes. Cada ficha cerrada deja su hash del contenido útil, su versión de parser y su próxima
revisión a 30 días.


## S03 · ¿Resuelve la ficha lo que el *slug* no pudo? (7 de octubre de 2026)

Lidl dejó **4.363 direcciones a revisión** porque su *slug* no dice nada. El contrato dice que esos se
resuelven **con la ficha y no con el slug**, y eso hay que demostrarlo. Comparación sobre las
6 fichas ya leídas y guardadas, sin pedir nada a la red:

| resultado | fichas |
|---|---|
| el *slug* y la ficha coinciden | 5 |
| **la ficha cambia la decisión** | **1** |
| sin *slug* con el que comparar | 0 |

Casos donde el *slug* callaba o se equivocaba:

- `100272773`: incluido → **revisar** (None) · 4rain Depósito de agua "VASO 2in1 Decor", Volumen 220 Litros

**Lo que esto permite decir:** con 1 fichas, la ficha aporta decisión donde el
*slug* no la tenía. **Lo que no permite:** extrapolar a las 4.363 ni a la cadena. La
muestra es diminuta y no está estratificada; el valor está en que **el mecanismo
funciona**, no en el porcentaje.

## S03 · El lote acotado, y la cobertura sobre 26 fichas (7 de octubre de 2026)

La muestra de seis era anecdótica. Se han leído **20 fichas más** con la cola, en un solo lote acotado:

| medida | valor |
|---|---|
| fichas del lote | **20** |
| correctas / sin publicar / error de red | **20 / 0 / 0** |
| tiempo | **35,5 s** (ritmo del proyecto, robots respetado) |
| estado de la cola tras el lote | **correcto=28 · pendiente=5.026** |
| fichas guardadas en total | **26** |

**Cobertura de nutrición sobre 26 fichas** (el cuádruple que antes, y por eso vale más):

| medida | resultado |
|---|---|
| **con datos estructurados de producto** | **26/26** — el lector las lee todas |
| con tabla nutricional (3+ campos) | **0/26** |
| con base interpretable (`por 100 g`) | **0/26** |
| con ingredientes (2+ señales) | **0/26** |

**Lo que ahora se puede decir con más fundamento:** la ficha de producto de Lidl es **fiable para
identidad** en todas las leídas (y da GTIN válido) y, en **26 de 26**, **no trae la ficha
nutricional**. Veinte fichas seguidas sin un solo error de red ni una sin datos estructurados también
dice algo del instrumento: el lector y la cola aguantan un lote.

**Lo que sigue sin poder decirse:** que valga para todo el surtido. Siguen siendo **26 de 5.026
candidatos** y la muestra **no está estratificada por familia** (frescos, envasados, droguería): lo
leído son los primeros identificadores de la cola, que es una muestra cómoda y no una muestra
representativa. Para la afirmación sobre la cadena hace falta estratificar.

## Siguiente paso concreto

**S03 · segunda mitad: las fichas de Lidl.** Los 5.054 candidatos están ya en la cola (691 incluidos
y 4.363 a revisión) con su evidencia, y 1.568 direcciones de bazar quedaron fuera sin generar trabajo.
Lo que falta, en este orden:

1. **Un lector de ficha de Lidl** a partir de una ficha guardada (fixtures primero, sin red), con lo
   que publique: marca, título, descripción, ingredientes, alérgenos, nutrición con su base, peso,
   envase y procedencia. Lo que no publique queda `no_publicado`, no `null` sin motivo.
2. **La cola manda**: pedir ficha solo a los `pendiente`, con presupuesto por host y por día, guardar
   el hash del contenido útil y la versión del parser, y dejar `proxima_revision` a 30 días (7 si hay
   conflicto). Reanudable y sin duplicar, como ya está probado en S02.
3. **Resolver los 4.363 a revisión** con lo que diga la ficha, no con el *slug*: es la única forma
   honesta de saber si esos productos son de la cesta.
4. **Informe por fuente y familia** (descubiertos, incluidos, excluidos, ambiguos, visitados, vivos,
   con GTIN, con nutrición, con precio vigente y errores), sin declarar cobertura completa.

**Antes de eso, una comprobación de una línea**: pasar `uv run pytest -q` y `uv run ruff check .`, y
confirmar que siguen verdes. La última suite completa verificada es **1.223**.

### Lo que queda del encargo, sin adornos

- **Terminado y verificado**: S00, S01, S02 (núcleo, inventario y cobertura) y la primera mitad de S03.
- **Sin empezar**: S04 (identidad exacta, con el laboratorio como diagnóstico y no como sustituto),
  S05 (selector único: **`_candidatos` recibe `fecha_tope` y no la aplica**, y sus llamantes pasan
  cadena vacía — es el primer arreglo concreto del paquete), S06 (armazón con menú lateral, sin los
  11 px de Stitch ni datos ficticios), S07 a S12.
- **Decisión pendiente del dueño**: ninguna que bloquee. Cuando toque verificar recorridos completos
  de interfaz hará falta **Docker arrancado** (hoy está parado y la plataforma no responde).

## Detalle histórico: S02 · Cola de fichas. Crear el registro por `(fuente, id_fuente, variante, ámbito)` con
`discovered_at`, `last_seen_at`, `detail_fetched_at`, `next_check_at`, hash del contenido útil,
versión de parser, intentos y resultado; estados (`pendiente`, `en_curso` con lease, `correcto`,
`parcial`, `no_publicado`, `bloqueado`, `error_temporal`, `no_encontrado`, `excluido`); reanudación
sin duplicar; y el inventario de cobertura que hoy no existe. Empezar por el **crudo histórico**,
que ya está descargado, antes de pedir nada.
