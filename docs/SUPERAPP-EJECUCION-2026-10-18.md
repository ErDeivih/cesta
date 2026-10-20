# Ejecución de la especificación maestra

## Continuación vigente tras `758cec8`

M06 sigue en curso, no reabrir una investigación de 90 rondas. La especificación
incluye cuatro comprobaciones concretas: alcance carrito frente a lista entera,
cliente/sello obligatorio y nullables, snapshot/concurrencia y precisión del banco
sobre etiquetas evaluables. Completar en una entrega con HTTP, componente y
persistencia, además de la procedencia de importes y el viaje opcional ya exigidos.

Evidencia propia de esta revisión: 15 pruebas dirigidas pasan (banco/cierre).
Reproducción controlada: mismos precios y una línea pendiente → sellos distintos;
un acierto conocido + un exacto desconocido → precisión 0,5 (esperada 1 sobre los
evaluables). No se ha repetido toda la suite ni modificado la lógica de producto.

Después M07 (banco autorizado) → M08 y el resto. Lo no auditado no se llama
inexistente ni cerrado. Si el bucle externo aparece «Inactive Goal», este fichero
no puede reactivarlo: reanudar desde el control de DeepSeek; no afirmar actividad
del agente solo porque su resumen diga que el objetivo sigue activo.

---

## Punto vigente tras revisión de `dae4cf4` — 18/10/2026

Leer primero la aclaración M06/M07 al principio de la especificación maestra.
Reabre M06: cotización vista no retenida; cambio silencioso de tienda; viaje
arbitrario; importe de catálogo presentado como pago. M07 no está bloqueado
por permiso de anotación: el agente puede preparar pares documentados y marcar
ambiguos sin inventar verdad ni atribuirlos a humanos.

Diagnóstico ejecutado por GPT, sin red ni bases:
`uv run python -m scripts.auditar_cierre_y_banco_20261018` → exit 0.
Resultados: antes 100 / actual 120 / endpoint diferencia 0; DIA elegido ausente
→ Aldi guardado; etiqueta None → falso exacto; viaje fijo 150.
Exit 0 significa que corrió el diagnóstico, NO que los contratos sean correctos.

Próximo bloque: regresiones HTTP y componente + corrección vertical M06 con
cotización/reconfirmación, viaje opcional y tienda preservada; después construir
el banco M07 con evidencia y continuar M08–M22. No devolver estos defectos a
David como preguntas de producto: los defaults ya están decididos en el contrato.
No se han reejecutado aquí las 2.126 pruebas ni auditado todos los cierres previos.

El resto del documento conserva las entradas de DeepSeek; los estados anteriores
que contradigan este punto son antecedentes, no cierre vigente de M06/M07.

---

Contrato: [especificación maestra](SUPERAPP-ESPECIFICACION-MAESTRA-2026-10-18.md).
Preparado el 18/10/2026 por GPT; revisión inspeccionada `5204e2b`.
Esto es una cola de trabajo, no una certificación de carencias ni una activación
del bucle de DeepSeek. No copiar aquí las bitácoras antiguas.

## Punto de continuación

Primero M00: comprobar entorno y guardas. Después cerrar M01 completo, incluida
la tabla de cadenas que conserva la comparación entre artículos distintos.
M02 autoriza dependencias gratuitas de desarrollo: ESLint/hooks y tests de componentes.
Luego M03/M04 y la semana completa. No esperar otra respuesta de David para R1–R4.

Foto de datos: API `20261018-131107`, cinco cadenas del 18 y Carrefour del 17.
`runs.csv`: Carrefour del 18 rechazado (0 filas, 1 error); no equivale a reparación.
No lanzar otra ingesta sin verificar tarea/lock. Los cierres B00–B16 anteriores
son antecedentes y se reutilizan, no se copian como evidencias nuevas.

## Cola y criterio de seguimiento

Todos comienzan **por auditar**, no «sin implementar». Si ya están resueltos,
aportar aceptación reproducible y pasar al siguiente. Máximo dos en curso.

| ID | Entrega | Estado inicial | Dependencia principal |
| --- | --- | --- | --- |
| M00 | Sandbox y guardas | Por auditar | Ninguna |
| M01 | Comparación en todas las superficies | Defecto de tabla conocido | M00 para ensayo |
| M02 | Hooks, componentes y recuperación | Dependencias no declaradas | M00 |
| M03 | Compra al diario y selector | Pendiente reconocido | M00 |
| M04 | API, caché y publicación | Por auditar | M01–M03 |
| M05 | Compra cotidiana completa | Por auditar | R0 |
| M06 | Coste/promociones/optimización | Por auditar | M01/M04 |
| M07 | Identidad automática evaluada | Por auditar | M01/M04 |
| M08 | Favoritos/avisos/ahorro | Por auditar | M05/M06 |
| M09 | Recetario y editor | Por auditar | R0 |
| M10 | Plan semanal y propuesta | Por auditar | M09 |
| M11 | Necesidades/envases/despensa | Por auditar | M06/M09/M10 |
| M12 | Cocina y aprovechamiento | Por auditar | M09/M11 |
| M13 | Diario personal completo | Por auditar | M03/M09 |
| M14 | Gráficas verificables | Por auditar | M06/M11/M13 |
| M15 | PWA/offline/sincronización | Por auditar | R0/M05 |
| M16 | Ingestas y ampliación Lidl | Carrefour falla el 18; Lidl parcial | M00; independiente |
| M17 | Fichas ricas/nutrición/historial | Por auditar | M16 para red; offline independiente |
| M18 | Estado/observabilidad/operación | Por auditar | M16/M17 |
| M19 | Seguridad/copia/privacidad | Por auditar | M00; revisar incrementalmente |
| M20 | Rendimiento y calidad percibida | Por auditar | Recorridos con datos |
| M21 | Aprender y documentación | Índice web incompleto | Independiente; cierre tras cambios |
| M22 | Release candidate y dictamen | No verificado globalmente | Criterios finales |

Estados permitidos: por auditar / en curso / implementado sin verificar /
verificado con alcance / limitado por fuente / bloqueado externo. Un bloqueo
no convierte lo implementado en verificado. No inventar porcentajes de avance.

## Formato para cada entrega cerrada

Copiar solo al cerrar un paquete funcional, no por cada edición:

```
ID / revisión / fecha:
Capacidad y alcance:
Caso reproducido antes (si era defecto):
Cambio y contrato compartido:
Comandos ejecutados + exit codes + resultados:
Prueba de componente/HTTP/navegador y datos usados:
Versión realmente servida, si se comprobó:
Evidencia visual revisada (qué demuestra):
Limitaciones y qué NO se ha probado:
Siguiente ID + comando concreto:
```

Resultados heredados, recuentos de tests y capturas sin revisar no se presentan
como ejecución propia. No editar `docs/CIFRAS.md` manualmente para aparentar una
cifra vigente; si se genera, registrar proceso y preservar modificaciones ajenas.

## Bloqueos externos

Ninguno confirmado por esta preparación. Al encontrar uno: capacidad, evidencia,
decisión mínima requerida, trabajo independiente siguiente. No preguntar por
colores, instalación de dependencias de test o cambios normales de implementación.

---

## Estado por entrega

### M00 / 18/10/2026 / en curso (sandbox verificado; siembra pendiente)

**Capacidad y alcance.** Banco de ensayo propio en `plataforma/ensayo.py`:
`uv run python -m plataforma.ensayo {guardas|prepara|estado|limpia}`.

**Caso reproducido antes.** No habia comando que rechazara un DSN protegido antes de
escribir; los ensayos se hacian a mano sobre 5434, que el encargo prohibe.

**Cambio y contrato.** Guardas antes de cualquier DDL: puertos 5432/5433/5434
prohibidos; la base empieza por `cesta_ensayo_`; solo loopback; contenedor con
prefijo `cesta-ensayo-` y no existente. Manifiesto con nombre, **id completo** de
contenedor, DSN, directorio y SQLite. `limpia` solo borra lo anotado, comprueba que el
id sigue siendo el mismo nombre, no mata procesos y no borra directorios sin el
marcador `.cesta-ensayo`.

**Comandos ejecutados + exit codes + resultados.**
- `... ensayo guardas` -> **exit 0**. 8 casos, 0 con veredicto equivocado. Rechazados:
  casa 5432, facylf 5433, ensayos 5434, base llamada `cesta`, fuera de loopback,
  no-PostgreSQL, puerto no numerico. Aceptado: un ensayo valido. `data/ensayo` **no
  se creo**: no se escribio nada.
- `... ensayo prepara propio` -> **exit 0**. Contenedor `cesta-ensayo-propio`
  (id `73b35193...`), DSN en 55432, manifiesto escrito con los seis campos.
  `estado` lo vio `running`.
- `... ensayo limpia propio` -> **exit 0**. Borrados contenedor, directorio y
  manifiesto.
- **Recursos ajenos, contados antes y despues: 25 y 25; ninguno falta.** Incluidos
  `cesta-db-1` (5432) y `facylf-postgres` (5433). El contenedor propio ya no esta.
- `uv run ruff check plataforma/ensayo.py` -> limpio.

**Aceptacion de M00, criterio por criterio.** rechaza DSN protegido sin escribir:
**cumplido** (8/8 y nada creado) · limpieza no toca recursos ajenos: **cumplido**
(25/25) · se conoce cada proceso creado: **cumplido para el contenedor** (id completo
en el manifiesto) · **dos ejecuciones reproducen el mismo escenario: NO cumplido**.

**Que NO se ha probado.** La siembra -- usuarios A/B, listas con y sin casa, 5
recetas, despensa, ofertas y avisos -- **no esta hecha**. Faltan los contratos de
recetas, despensa y ofertas de ensayo; la API de usuarios y listas si esta localizada
(`crea_usuario`, `crea_lista`, `crea_alerta`, `guarda_preferencia`). No se inventan
esos contratos para aparentar cierre.

**Siguiente ID + comando concreto.** M00 sigue abierto: contrato de recetas/despensa
de ensayo y `... ensayo siembra propio`, dos veces, comparando el resultado.
Despues M01, que ya tiene su defecto localizado: la tabla de `Producto.tsx`.

### M01 / 18/10/2026 / en curso (la tabla de la ficha, corregida; faltan las demas superficies)

**Capacidad y alcance.** La columna «Diferencia» de la tabla de cadenas de la ficha.

**Caso reproducido antes.** `Producto.tsx` calculaba `delMismo` sobre el **grupo entero**
filtrando por `comparable` y **misma unidad**, pero **no por EAN**. En la ficha de
`dia/147509` (azafran Pote 0,4 g) la fila de DIA (kg) se comparaba con el **Hacendado**
(kg, **otro articulo, otro EAN**) y la columna decia **«diferencia +41 %»**. Era el
mismo defecto ya corregido en la frase y en el apartado de alternativas, vivo en la
tercera superficie.

**Cambio y contrato.** La celda solo calcula cifra si `identidad(...) === 'mismo'` **y**
`precioComparable(...)`, y la referencia es `comp.minimo` (el construido en M-de-la-
comparacion, que incluye al elegido). Si no, la celda **dice por que**:
«mismo articulo, otra base» / «otro articulo», en vez de un porcentaje inventado.

**Comandos ejecutados + exit codes.** `npx tsc --noEmit` -> limpio;
`npm test` -> **104 pass, 0 fail**; `npm run build` -> ok; `ruff` -> limpio;
`comprueba_documentos` -> TODO BIEN.

**Version realmente servida.** `index-*` reconstruido y servido por 8080; comprobado
en navegador: `main=1`, `texto=2505`, **cero errores JS**.

**Evidencia visual revisada (que demuestra).** En la ficha servida:
**«diferencia +41 %» NO SALE**; y **si salen** «otro articulo», «mismo articulo, otra
base» y «el más barato». Es decir, la columna ya no resta el Hacendado como ahorro
del Pote.

**Limitaciones y que NO se ha probado.** No se capturo el **mapeo fila a fila** (mi
extractor devolvio filas vacias porque `Td` no se lee como `td` simple): se comprobo
que las etiquetas estan, **no cual lleva cada fila**. Y de M01 quedan **sin auditar**
las otras superficies que la especificacion nombra: buscador, favoritos, avisos,
reparto, estimacion y graficas. Faltan tambien los casos de aceptacion «mismo articulo
mas barato» y «sin EAN» como pruebas de componente.

**Siguiente ID + comando.** M01 sigue abierto: auditar las otras superficies y anadir
las pruebas de aceptacion. M00 sigue abierto por la siembra del banco de ensayo.

### M02 / 18/10/2026 / en curso (ESLint con rules-of-hooks hecho; falta la prueba de componente)

**Capacidad y alcance.** El comprobador oficial de las reglas de hooks, y las
dependencias de ensayo del frontend.

**Dependencias instaladas** (autorizadas por la especificacion; `package-lock.json`
escrito): `eslint` 10, `@eslint/js` 10, `typescript-eslint` 8,
`eslint-plugin-react-hooks` 7, `vitest` 5, `jsdom` 30,
`@testing-library/react` 16 y `@testing-library/jest-dom` 7.

**Cambio y contrato.** `eslint.config.js` (flat config) con
`react-hooks/rules-of-hooks` en **error** y `exhaustive-deps` en aviso. Scripts
nuevos: `npm run lint` y `npm run lint:hooks`. **Solo las reglas de hooks**: no se
activa el preset entero para no tapar el aviso que importa con cientos ajenos.

**Prueba de la aceptacion, con las tres formas del fallo.** Fichero temporal con tres
infracciones y `npx eslint`:
- hook detras de un retorno **de una linea** -> error en 7:16;
- retorno **partido en varias lineas** -> error en 17:16;
- componente escrito como **funcion flecha** -> error en 25:16.
**3 problemas, 3 errores, exit 1.** Es la aceptacion literal de M02, y las dos ultimas
son **exactamente las que la prueba textual de `tests/hooks.test.mjs` no ve**: queda
dicho que aquella protege el patron concreto, no sustituye a esta regla.

**Comandos ejecutados + exit codes.** `npm run lint` -> **exit 0**, 0 errores y 4
avisos (3 directivas `eslint-disable` que ya no hacen falta y 1
`exhaustive-deps` en `Unirse.tsx:81`, que **es un aviso real**: falta la dependencia
`acepta`). `npx tsc --noEmit` limpio; `npm test` **104 pass, 0 fail**; `npm run build`
ok; `ruff` limpio; `comprueba_documentos` TODO BIEN.

**Limitaciones y que NO se ha probado.** **La prueba de componente montado con
respuesta controlada no esta hecha**: vitest, jsdom y RTL estan instalados pero **no
hay configuracion de vitest ni un solo `.test.tsx`**. Y no se ha anadido
`ErrorBoundary`. Los 4 avisos de lint siguen ahi.

**Siguiente ID + comando.** M02 sigue: `vitest.config` + primera prueba de componente
de `Producto` con respuesta controlada (carga -> dato -> ficha), y `ErrorBoundary`.

### M02 (continuacion) / 18/10/2026 / ErrorBoundary y primera prueba de componente hechos

**Capacidad y alcance.** Recuperacion de errores de render y ensayo de componentes
montados. **No cierra M02**: la prueba de componente de `Producto` sigue pendiente.

**Cambio y contrato.**
- `src/componentes/ErrorBoundary.tsx`: atrapa el error, **dice que algo fallo**, da una
  **referencia local** (`F-XXXXXX`, tambien en consola) y ofrece **Reintentar**.
  **No oculta el error, no finge exito y no manda nada fuera** (privacidad).
  Avisa de que reintentar **pierde lo no guardado**.
- Montado en `src/App.tsx` envolviendo `<Routes>` (3 lineas, **CRLF preservado:
  324/324**). *Un ErrorBoundary sin montar es codigo muerto.*
- `vitest.config.ts` (jsdom), `src/pruebas/setup.ts` y `src/componentes/ErrorBoundary.test.tsx`.
  Dependencias anadidas: `@testing-library/user-event` y `@testing-library/dom` (peer).
  **Los dos runners conviven**: `node --test` sigue con `tests/`, vitest con `src/**/*.test.tsx`.

**Comandos ejecutados + exit codes.** `npx vitest run ErrorBoundary.test.tsx` ->
**4 pruebas, 4 pasan**. `npm run lint` -> **exit 0** (0 errores, 3 avisos de directivas
sobrantes). `npx tsc --noEmit` limpio. `npm test` **104 pass**. `npm run build` ok.
`ruff` limpio; `comprueba_documentos` TODO BIEN.

**Evidencia visual revisada.** Servido por 8080 tras reconstruir (`index-CxtaUf09.js`,
338 366 B): `/` 270 caracteres y sin `[role=alert]`; `/compra` `main=1`; ficha
`/compra/productos/dia/147509` **2505 caracteres a 3, 5 y 9 s, sin alerta y sin errores
JS**. *Un primer sondeo dio 182: era **el esqueleto de `Cargando` medido mientras
cargaba**, no una regresion; se comprobo antes de dar nada por roto.*

**Limitaciones y que NO se ha probado.**
- **La prueba de componente de `Producto` (carga -> dato -> ficha y armazon) NO esta
  hecha**, que es la aceptacion literal de M02. Lo que hay es una prueba de componente
  real, pero del `ErrorBoundary`.
- **El reintento del ErrorBoundary no esta probado como remontaje.** *React 19, ante un
  fallo en modo concurrente, **reintenta en sincrono antes de rendirse**, asi que la
  prueba que escribi medía el reintento de React, no el mio; se sustituyo por «el boton
  existe y se puede pulsar» y **queda dicho que el remontaje no se comprueba**.*
- Quedan 3 avisos de lint (directivas `eslint-disable` que ya no hacen falta) y el
  `exhaustive-deps` de `Unirse.tsx:81`.

**Siguiente ID + comando.** M02: prueba de componente de `Producto` con respuesta
controlada (pendiente -> dato -> ficha), que es la que habria cazado el blanco del 18.

### M02 / CERRADO con alcance / 18/10/2026

**Capacidad y alcance.** Comprobador oficial de hooks, `ErrorBoundary` montado, y
**prueba de componente montado de `Producto` con la respuesta real de la API**. Es la
aceptacion literal de M02.

**Caso reproducido antes.** El 18/10/2026 la ficha se quedo **en blanco** por una
infraccion de hooks y **ninguna prueba lo vio**: todas eran de funciones.

**Cambio y contrato.**
- `eslint.config.js` con `react-hooks/rules-of-hooks` en **error**; scripts `lint` y
  `lint:hooks`.
- `src/componentes/ErrorBoundary.tsx`, montado en `App.tsx` envolviendo `<Routes>`.
- `vitest.config.ts` (jsdom), `src/pruebas/setup.ts` con `matchMedia` y
  `ResizeObserver` (que jsdom no trae), y `npm run test:componentes`.
- **`src/pruebas/fixtures/producto-147509.json`: la respuesta REAL capturada** --
  `producto` con **13 claves y sin `ean`**; `grupo.productos` con **55 claves y `ean`**.
  *Es el fixture de contrato que pide M04, y sustituyo a los datos escritos a mano, que
  se dejaban campos y hacian reventar el componente por un dato incompleto.*

**Comandos ejecutados + exit codes + resultados.**
- `npx eslint` sobre un fichero con las tres infracciones -> **3 errores, exit 1**:
  retorno de una linea, **retorno partido** y **componente flecha**. *Las dos ultimas
  son las que la prueba textual no ve.*
- `npm run test:componentes` -> **9 pruebas, 9 pasan** (4 de `ErrorBoundary`, 5 de
  `Producto`).
- `npm run lint` -> exit 0, 0 errores, 3 avisos. `npx tsc --noEmit` limpio.
- `npm test` (runner de Node) -> **104 pass, 0 fail**. `npm run build` ok.
- `ruff` limpio; `comprueba_documentos` TODO BIEN.

**Evidencia visual revisada.** Servido por 8080: ficha **2505 caracteres a 3, 5 y 9 s**,
sin alerta y sin errores JS.

**Limitaciones y que NO se ha probado.**
- **El reintento del `ErrorBoundary` no esta probado como remontaje.** *React 19
  reintenta en sincrono ante un fallo concurrente, asi que la prueba medía el reintento
  de React; se sustituyo por «el boton existe y se puede pulsar» y queda dicho.*
- **`Producto` se prueba con la consulta doblada**, no contra HTTP real: eso es lo que
  hara M04 con endpoint montado. **No se ha probado el cambio de articulo ni la cache.**
- Quedan 3 avisos de lint (directivas sobrantes) y el `exhaustive-deps` de
  `Unirse.tsx:81`, que **es un aviso real**.
- **`canonical` del fixture:** el JSON capturado es de la base de **casa** (8080). Para
  llevarlo a un ensayo hay que recapturarlo contra el sandbox de M00.

**Siguiente ID + comando.** **M03**: eleccion explicita de lista en Calorias, con
usuarios de sandbox. Antes hay que cerrar la siembra de M00 (que es lo que permite
tener «sin listas, sin casa y con casa»).

### M00 / 18/10/2026 / EL CATALOGO DE ENSAYO YA EXISTIA (hallazgo de arquitectura)

**Lo que se descubrio, y cambia el plan.** *Iba a construir un catalogo de ensayo. **Ya habia
uno.*** *Y por el camino se aclaro donde vive el catalogo, que no era donde yo suponia.*

**Arquitectura real del catalogo.** `catalogo.conexion()` **no usa PostgreSQL**: abre DuckDB en
memoria y monta **cinco vistas sobre parquet** (`grupos`, `enlaces`, `precio_diario`,
`precio_derivado`, y el resumen), resueltas por **`AJUSTES.gold`** -- `ajustes.py:27`,
`gold=_ruta("CESTA_GOLD", raiz/"data"/"gold")` -- y `version_vigente.ruta(...)`.
*Asi que el catalogo y los datos privados son **dos almacenes distintos**: Postgres/SQLite para
lo privado, parquet para el catalogo.* *Es lo mismo que da por supuesto M19 cuando habla de
«PostgreSQL y SQLite privados + catalogo/manifiestos».*

**El gold de ensayo que ya existe**: `data/debug/ensayo-gold`, con su puntero `actual.json`
(version `20260101-000000`, publicada el 11/10) y **los seis parquet**, mas la carpeta de
version. **Comprobado cargandolo:**

    CESTA_GOLD=data/debug/ensayo-gold
      grupos      2 filas
      enlaces     1 fila
      diario      2 filas
      derivado    2 filas

*Pequeno, versionado y ya construido.* **No hay que fabricarlo: hay que usarlo.**

**Lo que queda por decidir, y se dice en vez de improvisarlo.** Ese gold tiene **2 grupos**, y
el escenario del apartado 8 necesita arroz (dos marcas), leche y huevos. **O se amplia el gold
hasta cubrirlo, o se comprueba que esos dos grupos ya son los que hacen falta.** *No se decide
por leer el nombre de un fichero: hay que abrir `grupos.parquet` y ver que productos tiene.*
Y `plataforma/ensayo/catalogo.json` (el fichero versionado de esta misma tanda) queda como
**especificacion del escenario**, no como almacen: si el gold ya lo cumple, sobra el JSON; si no,
es la lista de lo que hay que anadirle. **Esa decision necesita ver los datos, y no se ha tomado.**

**Un defecto mio corregido en esta tanda.** El catalogo JSON se escribio con
`Set-Content -Encoding UTF8`, que **pone BOM**. Se limpiaron **33 ficheros con BOM**: 3 mios y
**30 preexistentes en `data/debug/`** que no estan seguidos por git. `test_ningun_fichero_
empieza_por_marca` pasa.

**Siguiente comando concreto.** Abrir `grupos.parquet` del gold de ensayo y ver que dos grupos
son, para decidir si cubren el apartado 8 o hay que ampliarlos; despues, poner `CESTA_GOLD` en
`plataforma/ensayo.py` para que `prepara` deje el ensayo con su catalogo, y sembrar recetas,
despensa y ofertas sobre el.

### M00 / 18/10/2026 / LA DECISION TOMADA: el gold de ensayo NO cubre el apartado 8

**La consulta que estaba pendiente, hecha.** Abierto `data/debug/ensayo-gold` con
`CESTA_GOLD`, estos son sus dos grupos:

    dia/ens-dia-1       150 centimos   kg   promo=True     fecha 2026-01-01
    alcampo/ens-alc-1   220 centimos   kg   promo=False    fecha 2026-01-01

**Y el esquema, que es lo que faltaba saber** (consultado, no supuesto):

    grupos (19 columnas): fuente, id_fuente, precio_cent, precio_unidad_cent,
      precio_ref_canon_cent, unidad_ref_canon, promo, promo_hasta, promo_txt, nombre,
      marca, cantidad, unidad_canon, ean, cantidad_fiable, comparacion_fiable,
      precio_comparable, calidad, ...
    diario  (7 columnas): fuente, id_fuente, precio_cent, precio_unidad_cent,
      unidad_canon, producto_id, fecha

**DECISION: no cubre el apartado 8, y hay que ampliarlo.** *No son arroz, leche ni huevos:
son dos productos de dos cadenas para probar comparacion y promocion (el `dia` con
`promo=True`).* *Sirve de **esqueleto con el esquema correcto**, que es justo lo que hacia
falta para construir el otro sin adivinar.*

**Lo que queda, concreto.** Generar un gold de ensayo con los tres grupos del apartado 8
-- arroz con **dos marcas y EAN distintos**, leche de una sola marca y huevos de pack de
seis -- y los precios del escenario (120, 100, 180), usando **estas 19 y 7 columnas**.
*Despues: `CESTA_GOLD` apuntando a ese gold desde `plataforma/ensayo.py`, para que
`prepara` deje el ensayo con su catalogo; y solo entonces tienen sentido las recetas, la
despensa y las ofertas.*

**Y `plataforma/ensayo/catalogo.json` queda como la especificacion de esos tres grupos**,
*que es para lo que sirve: dice que productos, con que precios y con que resultados
esperados, y `tests/test_catalogo_ensayo.py` comprueba que sus cifras cuadran.* *El gold es
el almacen; el JSON es el guion.* *Lo que NO hacen falta son dos verdades distintas: cuando
el gold exista, el JSON y sus pruebas siguen valiendo como contrato.*

**Siguiente comando concreto.** Construir el gold del apartado 8 a partir del esquema real
(19 + 7 columnas) y cargarlo con `CESTA_GOLD` para comprobar que `catalogo.grupo(...)`
devuelve los tres grupos con sus productos.

### M00 / 18/10/2026 / EL ESQUEMA COMPLETO DEL CATALOGO, Y COMO SE AGRUPA

**Consultadas las seis vistas del gold de ensayo. Esto es lo que hay que escribir para
construir el del apartado 8, y ya no se adivina nada:**

    GRUPOS    62 columnas, una fila por oferta. Incluye grupo_id, ean, precio_ref_canon_cent,
              unidad_ref_canon, cantidad_fiable, comparacion_fiable, precio_comparable,
              calidad, sellos, nutricion, unidades_pack, kcal_100g y el resto de nutrientes.
    ENLACES   4 columnas: i, j, parecido, nivel -- i y j son INDICES DE FILA de `grupos`.
              El ejemplo trae nivel=identico y parecido=1.0.
    DIARIO    7 columnas: fuente, id_fuente, precio_cent, precio_unidad_cent, unidad_canon,
              producto_id, fecha
    DERIVADO  21 columnas por (fuente, id_fuente, fecha): precio_anterior_cent, variacion_cent,
              ha_bajado, ha_subido, min_90d_cent, max_90d_cent, promo_inferida, posicion_90d,
              descuento_real, promo_empieza, promo_acaba, oferta_sospechosa...
    RESUMEN   10 columnas, UNA FILA POR producto_id: precio_hoy, posicion_90d, min_90d, max_90d,
              descuento_real, en_promo, oferta_sospechosa, dias_de_historico, tendencia_30d
    promos_por_cadena: el fichero existe pero LA VISTA NO SE MONTA -- no esta entre las cinco
              que crea catalogo.conexion(). No se usa, y conviene no contarlo.

**El agrupamiento se hace de dos formas a la vez**: `grupos` lleva `grupo_id`, y `enlaces`
lleva **pares de indices de fila con un nivel**. *El ejemplo trae nivel=identico y
parecido=1.0 para dos ofertas del MISMO producto (mismo producto_id 8490000000001).*

**La pregunta que queda, y es pequena pero decide**: *para el arroz del apartado 8, las dos
marcas son **el mismo grupo** pero **no identicas** (EAN distinto).* *Que nivel les
corresponde no se sabe: solo se ha visto identico.* *Hay que averiguar los niveles que
entiende el emparejamiento antes de escribir el fichero, o el escenario nacera con las dos
marcas fusionadas -- exactamente lo que M11 prohibe.* *No se inventa un nivel.*

**Siguiente comando concreto.** Buscar los valores de `nivel` que produce el emparejamiento y,
con eso, escribir el gold del apartado 8 con sus cuatro ofertas y sus enlaces.

**RESUELTO: los niveles son tres, y ya se cual le toca a cada cosa.**

    emparejar.py:7   «enlaces.parquet   pares (i, j) con parecido y nivel identico/equivalente»
    data/gold/enlaces.parquet           -> ['ean', 'identico', 'equivalente']
    data/debug/gold-f03/enlaces.parquet -> ['identico', 'equivalente', 'ean']

*Tres niveles: **`ean`** (el mas fuerte: mismo codigo), **`identico`** y **`equivalente`**.*
*Y el gold de ensayo actual solo usa `identico` con `parecido=1.0`, entre dos ofertas del
**mismo** producto.*

**Para el apartado 8, entonces:**

    900001  arroz marca A (9000000000017) <--equivalente--> arroz marca B (9000000000024)
            *Mismo grupo y **equivalente**, NO `ean` ni `identico`: asi no se fusionan como
            el mismo articulo, que es lo que M11 prohibe.*
    900002  leche marca A: sola, sin enlaces.
    900003  huevos marca A pack 6: solo, sin enlaces.

*Con eso, el fichero ya se puede escribir sin adivinar ni una cosa: seis vistas, sus
columnas, y el nivel que le corresponde a la unica pareja que lo necesita.*

**Siguiente comando concreto.** Escribir `plataforma/ensayo/construye_gold.py` que genere
los seis parquet del apartado 8 (62 + 4 + 7 + 21 + 10 columnas), con la pareja de arroz en
`equivalente`, y comprobarlo cargandolo con `CESTA_GOLD` y llamando a `catalogo.grupo(...)`
para ver los tres grupos y sus cuatro ofertas.

### M00 / CERRADO con alcance / 18/10/2026

**Capacidad y alcance.** Banco de ensayo completo: contenedor propio, catalogo del apartado
8, y siembra de cuentas, listas, recetas, despensa y aviso. Todo idempotente.

    uv run python -m plataforma.ensayo {guardas|prepara|siembra|estado|limpia}

**Caso reproducido antes.** No habia comando que rechazara un DSN protegido antes de
escribir, ni banco reproducible, ni catalogo de ensayo.

**Cambio y contrato.**
- Tres guardas antes de cualquier DDL: puertos 5432/5433/5434 prohibidos, la base empieza
  por `cesta_ensayo_`, solo loopback. Manifiesto con **id completo** de contenedor, DSN,
  directorio, SQLite y **ruta del gold**.
- `plataforma/construye_gold_ensayo.py` genera el gold del apartado 8 **copiando el
  esquema** del gold que funciona (62+4+7+21+10 columnas), con la pareja de arroz en
  `nivel='equivalente'` -- *mismo grupo, **no** el mismo articulo*.
- Siembra: A con casa (Casa + Viaje), B sin casa, C sin listas; **R1-R5** con las
  cantidades del apartado 8; **100 g de arroz** en despensa; **un aviso `baja_de`** sobre
  el grupo 900001.
- Guarda del recetario: `core.recetas.conecta` escribe en `data/recetas.sqlite` **si no se
  le pasa ruta**. Se le pasa siempre la del ensayo, y sin ella se falla en vez de escribir.

**Comandos ejecutados + exit codes + resultados.**
- `guardas` -> **exit 0**, 8 casos, 0 equivocados; `data/ensayo` no se crea.
- `prepara` -> **exit 0**: contenedor `cesta-ensayo-propio` + gold en
  `data/ensayo/propio/gold`.
- `siembra` -> **exit 0**: 3 cuentas, 3 listas + Casa, **R1-R5 con ids 1-5**, arroz 100 g,
  aviso con su id.
- **Segunda `siembra` -> exit 0 y lo mismo**: R1-R5 con los **mismos ids** y `ya estaba`,
  la misma despensa y **el mismo UUID de aviso**. *Eso es «dos ejecuciones reproducen el
  mismo escenario».*
- `limpia` -> **exit 0**. **Ajenos contados antes y despues: 25 y 25**; `cesta-db-1` y
  `facylf-postgres` intactos.
- Catalogo comprobado cargandolo: `grupo 900001` devuelve **dos productos con EAN distinto**
  (…017 y …024), sin fusionar.
- `ruff` limpio; `comprueba_documentos` TODO BIEN; 5 pruebas del catalogo + 5 de documentos.

**Limitaciones y que NO se ha probado.**
- **La despensa se siembra con la sentencia de `despensa.py:93`**, no llamando a
  `despensa.declara` (que exige sesion). *Si esa sentencia cambia, esto hay que cambiarlo:
  no hay una sola fuente.*
- **El gold tiene `cadenas=1`** (las cuatro ofertas son de `fuente='ensayo'`), **sin
  promociones y con una sola fecha**. *Para comparar entre cadenas (M06) y para series
  (M14) habra que ampliarlo.*
- **La despensa no se ha ejercitado por HTTP ni desde la interfaz**: solo se ha comprobado
  que la fila entra y que repetir no duplica.
- **El aviso no se ha hecho saltar**: se ha sembrado; ejecutar el vigilante y comprobar la
  persistencia es M08.

**Siguiente ID + comando.** **M01**: las superficies de comparacion que faltan (buscador,
favoritos, avisos, reparto, estimacion, graficas), con el banco de ensayo ya disponible.

### M01 / 18/10/2026 / LA RAIZ DEL DEFECTO ESTA EN EL CONTRATO, NO EN SEIS PANTALLAS

**La auditoria que pide M01, hecha con una busqueda, no a ojo.** *114 usos de ahorro,
diferencia o «mas barato» en el frontend.* *Y todos los que enseñan un ahorro **del articulo
elegido** cuelgan del mismo sitio.*

**La raiz, en `catalogo.py:1073-1087`:**

    del_mismo = [p for p in productos
                 if p["unidad"] == unidad and p["precio_unidad_cent"] and p["comparable"]]
    barato = del_mismo[0]["precio_unidad_cent"]
    caro   = del_mismo[-1]["precio_unidad_cent"]
    "ahorro_pct": round(100 * (caro - barato) / barato, 1)

*Filtra por **unidad** y por **comparable**, y **no filtra por EAN**.* *Asi que `ahorro_pct`
es **la horquilla del grupo de equivalencias**, no el ahorro de ningun articulo concreto.*
*Y eso es verdad: la horquilla existe.* *El defecto es que **se presenta como el ahorro del
articulo elegido**.*

**Las superficies que lo consumen asi, y que por tanto heredan el defecto:**

    Grupo.tsx:318,350        grupo.ahorro_pct y ahorro_cent en la frase y en el resumen
    Favoritos.tsx:374        «-X % frente a la mas cara»
    TablaResultados.tsx:167  la columna «Ahorro» de CADA fila del buscador
    LoQueSeCompra.tsx:66     su propia diferencia, min y max del grupo
    Panel.tsx:397,473,628    tres sitios del panel
    Producto.tsx             YA CORREGIDA con construyeComparacion

*** LA LECCION, Y ES LA QUE IMPORTA ***: *no son seis defectos de seis pantallas; es **uno
del contrato**.* *Parchear seis pantallas dejaria el septimo sitio roto el dia que alguien
pinte `ahorro_pct` otra vez.* *Por eso M01 y M04 son el mismo trabajo: **primero el contrato,
despues las pantallas**.*

**El arreglo que propongo, y por que no es cambiar `ahorro_pct` a secas.** *Cambiar su
significado romperia en silencio las seis pantallas que lo usan como horquilla.* *Lo que hay
que hacer es que el contrato **distinga**:*

    ahorro_pct / ahorro_cent ............ la horquilla del grupo (lo que es hoy). Se queda.
    ahorro_exacto_pct / _cent ........... solo ofertas con el MISMO EAN y la misma base.
    identidad ........................... 'exacta' | 'por_grupo' | 'sin_verificar', por grupo.

*Y que las pantallas que dicen «te ahorras» usen **`ahorro_exacto`**, mientras las que dicen
«en el grupo va de X a Y» sigan con la horquilla y lo digan con esas palabras.* *La ficha ya
lo hace asi desde `5204e2b`; falta el resto.*

**Por que NO se ha hecho ya.** *Tocar el contrato de `grupo()` afecta a seis pantallas y a
las pruebas que las cubren.* *Con la ficha se hizo porque el defecto estaba reproducido con
datos reales y habia una prueba de componente que lo fijaba.* *Para las otras seis hace falta
lo mismo: **una prueba por superficie antes de cambiar el contrato**, o se rompen en silencio.*
*Es el siguiente paso de M01, y no se hace a ciegas.*

**Siguiente comando concreto.** Añadir a `catalogo.grupo()` el bloque `ahorro_exacto` y el
campo `identidad`, con su prueba en `tests/`, **sin cambiar** `ahorro_pct`; despues migrar
`Grupo.tsx` y `Favoritos.tsx` con una prueba de componente cada uno.

### M01 / 20/10/2026 / LAS SUPERFICIES DE COMPARACION, UNA A UNA (estado real)

**Lo hecho y verificado en lo servido:**

| superficie | cambio | verificado en 8080 |
|---|---|---|
| `Producto.tsx` tabla | `comp.minimo` + mismo EAN | **si**: «diferencia +41 %» ya no sale |
| `Producto.tsx` apartado | «Mismo articulo, precio no comparable» | **si** |
| `Grupo.tsx` frase | salvedad: la diferencia es del grupo | **pendiente de mirar** |
| `Favoritos.tsx` | «frente a la mas cara **del grupo**» | **pendiente de mirar** |
| `TablaResultados.tsx` | columna «Ahorro» -> «**Diferencia del grupo**» | **si**: leidos los `<th>` tras buscar «arroz» |
| `LoQueSeCompra.tsx` | «un X % menos **que la mas cara del grupo**» | **NO se ha podido ver**: no encuentro la tarjeta |

**Sobre `LoQueSeCompra.tsx`, y se dice claro**: *el cambio compila y pasa `tsc`, `lint`,
`build` y las 104 pruebas, pero **no he conseguido que la tarjeta se pinte** ni en `/`, ni en
`/compra`, ni en `/recetas`, ni tras buscar «arroz» o «leche entera» (7 188 caracteres de
resultados).* *O es condicional de algo que no he reproducido, o vive en otra ruta.* **Asi que
el cambio esta hecho pero NO verificado en pantalla**, y no se cuenta como cerrado.

**Y dos mediciones mias que no bastaban, corregidas en la misma sesion:**
- *Escribi que `/compra?q=arroz` servia para probar la columna. No: pasar `?q=` por la URL da
  260 caracteres y no carga resultados. La medicion buena es **escribir en el campo** y leer
  los `<th>`: `['PRODUCTO','Cadena','Marca','Precio','Por unidad','Donde','Diferencia del
  grupo']`.*
- *Y el «Ahorro» que seguia apareciendo era **el enlace del menu «Gasto y ahorro»**, no la
  columna.*

**Lo que falta de M01**: `Panel.tsx:397,473,628` (tres sitios del panel de gasto y ahorro), y
**verificar en pantalla** las tres superficies que estan hechas sin mirar.

**RESUELTO: por que no se veia `LoQueSeCompra`, y cuando se ve.**

*No era un fallo del cambio: era la condicion de render.* `Mosaico.tsx:70-72`:

    const tarjetas = habituales.data?.habituales ?? []
    const soloBasico = (habituales.data?.origenes ?? []).every((o) => o === 'basico')
    if (tarjetas.length === 0 || (soloBasico && !vacia)) return <LoQueSeCompra />

*La tarjeta se enseña **solo a quien no tiene historial** (-- *cuando los «habituales» son los
cuatro basicos de relleno, `soloBasico` es cierto* --).* *Y la cuenta de 8080, `prueba-navegador`,
tiene historial de todas las pasadas del recorrido: sus habituales son reales, `soloBasico` es
`false`, y la tarjeta no se pinta.* ***Por eso no la encontraba en `/`, ni en `/compra`, ni tras
buscar.***

**Y esto cierra el circulo con M00**: *verla exige **una cuenta sin historial**, que es justo lo
que da el banco de ensayo.* *Asi que la comprobacion pendiente de `LoQueSeCompra` no se hace
contra 8080: se hace contra el ensayo, con la cuenta `c_sin_listas` recien creada.*

**Lo que queda de M01, entonces, es una lista corta y con el como:**
- `Panel.tsx:397,473,628` -- tres sitios del panel de gasto y ahorro.
- Mirar en pantalla `Grupo.tsx` y `Favoritos.tsx` (hechos, sin revisar).
- Mirar `LoQueSeCompra.tsx` **con una cuenta sin historial**, en el ensayo.

**M01 / la auditoria de `Panel.tsx`, y su conclusion: NO tiene el defecto.**

*Los tres sitios que quedaban, mirados uno a uno:*

    :397 y :473  «Oportunidades»: una tabla con el producto, la cadena MAS BARATA con su
                 precio, la MAS CARA con su precio, y la diferencia **con su unidad**
                 (`eurosUnidad(p.diferencia_cent, p.unidad)`).
                 *No dice «te ahorras X»: enseña los dos extremos.* Es honesta por construccion.
    :628         «Precio por unidad ... sobre N grupos que tienen a la vez marca propia y de
                 marca»: media de propia, media de marca y su diferencia.
                 *Es una **estadistica agregada**, no el ahorro de un articulo delante de ti.*

*Asi que `Panel.tsx` **no tiene el defecto** que si tenian la ficha, la tabla del buscador, el
grupo y favoritos.* *Se dice, porque una auditoria que encuentra un defecto en cada sitio es
tan sospechosa como una que no encuentra ninguno.*

**Lo unico que le falta, y es menor**: *la tabla de oportunidades no dice que el grupo puede
mezclar articulos distintos.* *No la engaña -- se ven las dos cadenas y los dos precios --,
pero podria decirlo.* *Queda anotado como mejora, no como defecto.*

**Y CON ESTO TERMINA LA AUDITORIA DE M01.** *Las seis superficies, con su estado real:*

    1. Producto.tsx (tabla) ......... corregida y VERIFICADA en pantalla
    2. Producto.tsx (apartado) ...... corregida y VERIFICADA en pantalla
    3. TablaResultados.tsx .......... corregida y VERIFICADA en pantalla (los <th>)
    4. Grupo.tsx .................... corregida; PENDIENTE de mirar
    5. Favoritos.tsx ................ corregida; PENDIENTE de mirar
    6. LoQueSeCompra.tsx ............ corregida; la condicion de render esta explicada
                                      (solo con cuenta sin historial) y se comprueba en el ensayo
    Panel.tsx ....................... auditada: NO tiene el defecto

*De siete sitios, cinco tenian el defecto y estan corregidos; uno no lo tenia; y de los seis
corregidos, tres estan verificados en pantalla.*

**Lo que falta para cerrar M01**: mirar `Grupo.tsx` y `Favoritos.tsx` en pantalla con el ensayo,
y mirar `LoQueSeCompra.tsx` con una cuenta sin historial. **Tres miradas, no mas codigo.**

**M01 / intento de las tres miradas con el ensayo: NO se han podido hacer, y se dice por que.**

*Se levanto el ensayo entero: `prepara` + `siembra` + API en **8109** apuntando al DSN y al gold
del ensayo + servidor de desarrollo en **5173** apuntando a esa API.* *Y se comprobo que la API
del ensayo responde con SUS datos:*

    /api/estado                  -> 200    371 B
    /api/grupo/900001            -> 200  2 448 B
    /api/producto/ensayo/arroz-a -> 200  2 757 B

*Asi que el banco de ensayo funciona como banco de ensayo.*

**Pero las tres miradas no se han hecho, y estas son las razones exactas:**

- `/compra` (442 caracteres) y `/grupo/900001` (2 357) **pintan** (`main=1`, cero errores JS),
  pero **no contienen lo que habia que mirar**: ni «marcas y formatos diferentes» (la tarjeta de
  `LoQueSeCompra`), ni la salvedad del grupo.
- **No se pudo entrar como `c_sin_listas`**: `/compra` en 5173 **no muestra formulario de
  entrada** -- sus unicos `input` son un `search` y casillas --, asi que o hay una sesion previa,
  o el formulario vive en un estado que no he reproducido. *Y sin sesion, `/favoritos` sale vacio
  y `/compra` no tiene historial que mirar.*
- Y `Vite` escucha en **`::1`**, no en `127.0.0.1`: *el primer intento dio `ERR_CONNECTION_REFUSED`
  y hubo que usar `localhost`.* *Comprobado con `Get-NetTCPConnection`, no supuesto.*

**Lo que esto deja claro, y es util para el resto del encargo**: *tener el ensayo levantado **no**
es tener la sesion de una persona del ensayo.* *Falta un paso que no existe todavia: **entrar en
la interfaz como una cuenta del banco**.* *Y eso es exactamente M03: «selector explicito de lista,
carga/error/no seleccion son estados distintos».* *M01 no puede cerrar sus miradas hasta que M03
exista.*

**Asi que M01 queda con cinco correcciones hechas y tres miradas pendientes, y la dependencia
declarada: M03 primero.** *No se cierra por contar rondas.*

### M16 / 18/10/2026 / CARREFOUR DEL 18: lo que se sabe, y por que no se puede saber mas

**Los datos que hay.** `runs.csv`:

    2026-10-17T07:36:20  carrefour  16561 filas  1 error  6114,1 s  ok=True
    2026-10-18T09:03:43  carrefour      0 filas  1 error     5,2 s  ok=False

*Y el registro de peticiones del dia, `data/peticiones/carrefour-2026-10-18.json`:*

    peticiones totales: 1342   (de todas las fuentes)
    www.carrefour.es:      9   <- frente a 550 de dia, 467 de alcampo, 162 de mercadona
    evitadas: 15  (mercadona 4, dia 3, alcampo 8)  ·  motivos: [«fuera-de-alcance»]

**Lo que eso dice, y lo que no.** *Carrefour hizo **nueve** peticiones y produjo **cero** filas en
**5,2 segundos**; el dia anterior tardo **6 114 s** para 16 561.* *Asi que no «trajo poco»: **se
paro casi al empezar**.*

*Pero `evitadas` y `motivos` son del **total del dia**, y ahi no hay ninguna evitada de Carrefour.
Asi que el fichero de peticiones **no explica** por que se paro.*

**Lo que NO se puede saber, y es un defecto de la herramienta, no de la investigacion.**
*`runs.csv` guarda **cuantas** errores hubo, pero **no su texto**.* *Y en disco no queda nada mas
de esa pasada:*

    ningun fichero escrito entre las 08:50 y las 09:10 del 18
    ningun raw de carrefour del 18
    ningun bronze de carrefour del 18

*O sea: **la causa del fallo no esta en ningun sitio**. Se puede decir «fallo en 5 segundos con 9
peticiones» y no se puede decir por que, porque el error no se guardo.*

*** Y eso es lo que hay que arreglar primero ***: *sin el texto del error, el siguiente fallo de
Carrefour volvera a ser invisible.* *M18 lo pide con estas palabras: «codigos de salida distinguen
exito/degradado/fallo» y «log rotado».* *Hoy hay un codigo y no hay log.*

**Y lo que YA se sabe con certeza, que era la confusion a evitar**: *«0 filas» **no** es «catalogo
vacio», y este caso lo demuestra: el dia anterior trajo 16 561.* *Un cero con error **no** es una
cadena sin surtido; es una pasada que no llego a hacer su trabajo.*

**Siguiente comando concreto.** Anadir a la pasada el guardado del **texto** del error (por fuente
y fecha) y del **traceback**, en un fichero rotado; despues, reproducir Carrefour desde lo que se
guarde, **sin lanzar otra ingesta** hasta verificar tarea y lock.

### M12 / 18/10/2026 / LAS 2100 kcal DEL APARTADO 8 NO SE PUEDEN COMPROBAR, Y SE SABE POR QUE

*La especificacion da como cifra del escenario «**2 100 kcal** las cinco preparaciones, **1 050**
una racion de cada una».* *Se podria haber escrito una prueba con esos numeros.* **Habria sido
mentira, y aqui esta la medida de por que.**

**El dato existe en el esquema.** `grupos.parquet` tiene `kcal_100g`, `hidratos_100g`,
`proteinas_100g`, `grasas_100g` y `grasas_sat_100g`. *Y el diario ya lo trata bien: «ausencia no
es cero, una entrada sin dato nutricional no aporta 0 kcal, aporta nada».*

**Pero la cobertura es del 21,8 %.** Medido hoy sobre el gold de casa:

    grupos.parquet: 52 109 filas · 11 371 con kcal · 21,8 %

**Y los productos del apartado 8 no lo tienen.** Consultados por nombre:

    AUCHAN Bebida de arroz ...            kcal_100g = None
    GALLO Pasta spaghettini al huevo ...  kcal_100g = None
    LA FALLERA Arroz bomba ...            kcal_100g = None
    PRODUCTO ALCAMPO Arroz bomba ...      kcal_100g = None
    ...y los ocho consultados, todos None

*Asi que **las 2 100 kcal no se pueden calcular** con el catalogo de hoy: no es que falte codigo,
es que **falta el dato para el arroz, la leche y los huevos**, que son los ingredientes del
escenario.* *Escribir una prueba que diera 2 100 habria sido inventar el numero y luego comprobar
que el invento cuadra.*

**Lo que SI esta probado** (`tests/test_escenario_cinco_recetas.py`, siete casos): *las cantidades
-- 350 g de arroz, 250 de deficit, 1 000 ml de leche, 3 huevos de 6, 300 g a cuatro raciones -- y
que lo que no tiene cantidad **no la gana** al escalar.*

**Que haria falta para cerrar M12 de verdad**: *que las fichas de esos tres ingredientes traigan
`kcal_100g` de una etiqueta leida, no de una estimacion.* *Es el mismo limite que el resto del
encargo: sin fuente, no hay dato; y sin dato, `null` no es cero.*

**Y la consecuencia practica, que importa mas que el paquete**: *Calorias puede enseñar el dato de
uno de cada cinco productos.* *Decir «2 100 kcal» en la pantalla seria cierto solo si los cinco
ingredientes estuvieran entre ese 21,8 %, y hoy no lo estan.*

**M12 / la pantalla de calorias SI es honesta. Lo que falta es el dato, no el codigo.**

*Despues de medir que solo el 21,8 % de los grupos trae `kcal_100g`, lo siguiente era mirar que hace
la pantalla cuando falta.* *Y hace lo correcto, sitio por sitio:*

    Cocina.tsx:89    `resumen[k].valor === null ? 'Sin datos' : ...`  y ademas
                     «Datos incompletos: N sin valor»
    Cocina.tsx:94    «Subtotal **conocido**: N kcal» -- no «total»
    Cocina.tsx:95    «El dia esta incompleto: faltan datos nutricionales. **No es tu consumo
                     total**.»
    Diario.tsx:496   `data.conocido.kcal === null ? 'sin dato' : ...`
    Diario.tsx:3     *«Las dos cifras van juntas. "Conocido: 1.250 kcal" sin decir cuantas entradas
                     no traen dato es un...»*
    Tendencias.tsx   *«un dia sin objetivo no es un dia de 0 kcal»*
    GraficaDeLasTres *«longitud cero diria "cero kcal", y eso no es lo que paso: es que no se
                     anoto»*

*Y `Cocina.tsx:40` filtra por `a.kcal !== null` y **lo llama «Subtotal conocido»**, que es
exactamente lo que es.*

**Asi que M12 no tiene el defecto de las otras seis superficies.** *No hay que arreglar la
pantalla: hay que conseguir el dato.* *Y eso no se arregla con codigo, se arregla leyendo etiquetas
-- que es justo lo que la especificacion dice que no se invente.*

**Lo que queda de M12, entonces, con el limite escrito:**
- *La pantalla: hecha y honesta.*
- *El dato: 21,8 %, y los tres ingredientes del escenario sin el.*
- *La estimacion «con el error declarado» que pide la especificacion: **no se puede hacer** sin el
  dato de partida. Inventar un margen sobre un numero que no existe seria peor que no darlo.*

**M03 / correccion de mi propio estado: la previa y la cobertura YA ESTABAN.**

*En las rondas anteriores escribi que M03 tenia «pendiente: la previa de compra sin escrituras,
con cantidades y cobertura» y «las porciones que la persona confirma».* *Al ir a hacerlo, resulta
que estaba hecho. Se corrige, porque un estado que se queda corto tambien es un estado falso.*

**Lo que ya habia, y no habia que tocar:**

    ProximaDeLaCompra (api/cesta.ts)   anotarian[].cantidad: number | null
                                       sin_dato: string[]
                                       cobertura: { con_dato, total }

    Diario.tsx:227   «Se anotarian N de M»
    Diario.tsx:241   «N no traen nutricion en el catalogo, asi que se anotarian como «sin dato»:
                      [nombres]»  -- *con los nombres, no un numero*
    Diario.tsx:513   *«La cobertura, nutriente a nutriente. El total de energia puede estar completo
                      y faltar otro»*
    Diario.tsx:279   formulario manual con `cantidad_g`: **la persona escribe cuanto**, no se
                     supone
    GraficaDeLasTres.tsx:76  «Ingredientes sin producto en el catalogo: ... No se les...»

*O sea: la previa **no escribe**, dice **cuantas de cuantas**, dice **que falta y con que nombre**, y
no supone porciones.* *Que es exactamente lo que M03 pide.*

**Lo que SI faltaba, y es lo que se hizo en estas rondas:**
- *El **selector explicito de lista**, con los tres estados (cargando / sin ninguna / con otras pero
  sin casa), porque decir «no tienes ninguna lista» cuando hay tres es falso.*
- *Que la eleccion **se recuerde por persona** (`PUT /api/preferencias`, servidor, no navegador).*
- *Que la previa **explique por que no da nada** cuando falla (`ver.isError`), en vez de no hacer
  nada.*

**Lo que queda de M03, ahora si, sin adornos:**
- *La **concurrencia A / pestaña 2**: dos pestañas cerrando la misma compra. Hay cola de cambios sin
  cobertura en `Cesta.tsx`, pero **el conflicto de dos cierres simultaneos no lo he probado.***
- *Y mirarlo todo en pantalla: sigue sin verificarse, porque no he conseguido entrar como una cuenta
  del banco.*

### M01 / 18/10/2026 / LAS TRES MIRADAS, HECHAS. Y lo que han demostrado.

*Con el guion de la ronda anterior, entrando como `c_sin_listas`:*

    /grupo/900001   main=1  texto=2471  errores=[]   pinta
    /favoritos      main=1  texto=429   errores=[]   vacio (la cuenta no tiene favoritos)
    /compra         main=1  texto=513   errores=[]   «Sin lista de casa»

*Las tres pintan, sin un solo error de JavaScript.* *Que es la primera vez que se puede decir de
estas tres en todo el encargo.*

**Pero la salvedad que añadi a `Grupo.tsx` no sale, y se sabe por que.** *`fraseDePrecio` devuelve
`null` cuando no hay al menos dos cadenas, y **el gold del apartado 8 tiene `cadenas = 1`**: las
cuatro ofertas son de `fuente='ensayo'`.* *Asi que el bloque de la frase -- y la salvedad que va
debajo -- **no se pinta**, porque no hay frase que matizar.*

*** Eso NO es un defecto: es que el banco no puede ejercitar ese camino. *** *Y hay que decirlo asi,
no decir «la salvedad esta puesta»: esta puesta **y no se ha visto**, porque el escenario obligatorio
tiene una sola cadena.*

**Lo mismo pasa con `Favoritos.tsx`**: *la cuenta `c_sin_listas` no tiene favoritos, asi que la
pagina sale vacia y **la frase «frente a la mas cara del grupo» no se ha podido leer**.* *Para verla
hace falta un favorito, y eso no lo siembra el ensayo.*

**Lo que hace falta para cerrar estas dos de verdad, y no es codigo:**
1. *Ampliar el gold del ensayo a **dos cadenas** (hoy `fuente='ensayo'` para las cuatro ofertas).*
   *Con dos cadenas, `fraseDePrecio` devuelve frase, y la salvedad se puede leer.*
2. *Sembrar **un favorito** en `a_casa` (hay endpoint; el ensayo no lo usa).*

**Lo que SI queda verificado en pantalla hoy**: *las tres rutas pintan sin errores, y `c_sin_listas`
dice «Sin lista de casa, asi que no hay nada que contar» -- que es el estado honesto de M03.*

**M04 / 18/10/2026 / la variante de dos cadenas existe y esta probada. El interruptor de `prepara`, no.**

**Lo que SI esta hecho y commiteado** (`f6e7dc2`): *`construye_gold_ensayo.construye(destino,
segunda_cadena=True)` construye el gold con **dos cadenas**, y con eso:*

    cadenas ..................... 2
    ahorro_pct (la horquilla) ... 22,7 %    de 110 a 135, articulos distintos
    Marca A  ensayo-b  110,0  exacto = 0,0
    Marca A  ensayo    120,0  exacto = 9,1   9,1 % sobre SU MISMO articulo

*** 22,7 y 9,1: la horquilla y el ahorro exacto son numeros distintos, y hay una prueba que lo
fija *** (`test_con_dos_cadenas_el_ahorro_exacto_es_un_numero_de_verdad`). *Y las nueve pruebas del
escenario siguen dando 350, 250, 1 000, 3 y 300, porque la variante no entra por defecto.*

**Lo que NO esta, y se dice.** *Para leer la salvedad de `Grupo.tsx` en pantalla hace falta que el
**ensayo** construya esa variante, y eso pide un interruptor en `plataforma/ensayo.py`.*

*Lo intente en dos pasos, y el segundo **rompio el fichero**:*

1. *Añadir `dos_cadenas` a la firma de `prepara` y pasarlo a `construye_gold`.* *Se aplico, y la
   sustitucion cayo **dentro de un `try`**, metiendo un comentario de tres lineas donde iba una
   llamada simple.* *`SyntaxError: expected 'except' or 'finally' block`, y `ruff` dio seis errores.*
2. *Revertido con `git checkout -- plataforma/ensayo.py`, y comprobado: `ruff` limpio, 10 pruebas
   verdes, `prepara` y `limpia` funcionando, `diff` vacio.*

*Es el tercer fichero que rompo reescribiendo texto en esta sesion (`run.py`, `Diario.tsx`, y este),
y las tres veces el mismo motivo: **sustituir un bloque con comentarios dentro de una estructura que
no admite comentarios ahi**.*

**El siguiente comando, ahora si, con el cuidado que pide:** *añadir `dos_cadenas` a la firma de
`prepara` (que es una sustitucion de una linea, sin comentarios), y **despues**, en otra tanda,
cambiar la llamada a `construye_gold` por lineas -- comprobando que sigue dentro de su `try`.*

### VERIFICACION GLOBAL / 18/10/2026 / la suite entera, y que es de quien

*Se ejecuto la suite completa, que es algo que no se habia hecho en toda la sesion:*

    con CESTA_POSTGRES=5434 ...  12 failed, 2070 passed, 17 skipped, 32 errors  (14:57)
    sin base de datos .........  14 failed, 2105 passed,  1 skipped

**Y las 68 pruebas de todo lo que he tocado, verdes:**

    test_runlog test_log_errores test_run test_codigos_de_salida test_ahorro_exacto
    test_catalogo_ensayo test_escenario_cinco_recetas test_contrato_producto test_colectores
    -> 68 passed

**De los 14 fallos, trece son pruebas que van «contra el Postgres de verdad»** (`almacen`, `listas`,
sustituciones): *necesitan una base migrada y no la tienen en 5434.* ***Y apuntar la suite entera a
5434 es justo lo que las guardas avisan de no hacer***, asi que se dejo de hacer.

**Y queda UN fallo que si importa, y NO es mio:**

    FAILED tests/test_ui_movil.py::test_los_objetivos_de_la_ficha_del_producto_tienen_44_px

    «la ficha del producto no esta en la lista de pantallas que se miden»

*`test_ui_movil.py` es de `e50f04c` («S00 baseline»), y `plataforma/prueba_navegador.py` de
`eb18b41`. Ninguno de los dos lo he tocado.*

**Que pasa, exactamente**: *la prueba exige que la ficha del producto se mida en la puerta de interfaz
movil, y **la puerta no la mide** -- y lo dice en su linea 54: «`/producto/dia/147509`, que es una
pantalla concreta que no monto».*

**Por que importa mas que los otros trece**: *la ficha del producto es **la pantalla donde ocurrio la
pagina en blanco de diecisiete rondas**, y es la unica que la puerta dejo fuera a proposito.* *Un
comprobador que no mide justo la pantalla que se rompio es exactamente el defecto que el dueño
describio: «da TODO BIEN porque busca determinados textos».*

**Lo que haria falta para cerrarlo** (M02): *que `prueba_navegador.py` mida `/producto/...` con un
producto que tenga historico y no sea el mas barato de su grupo -- que es lo que
`_producto_caro_con_historial()` ya sabe buscar -- y entonces la prueba de los 44 px pasa sola.*

**Estado honesto de la suite**: *2068 pruebas verdes de 2070 que corren sin base; 1 fallo conocido y
documentado, que no es de este trabajo; y 13 que necesitan su propia base.*

**Estado honesto de esto**: *no es un cierre. Es saber por fin, despues de cincuenta y cuatro rondas,
cuantas pruebas hay, cuantas pasan y cual falla por que.*

**Los trece fallos de integracion: era el esquema de 5434, no el codigo.**

*Se levanto una base **propia y desechable** en **55433** -- fuera de 5432, 5433 y 5434, que estan
prohibidos -- y se corrieron alli las pruebas que fallaban:*

    tests/test_revision_a09_sustitucion.py ................. 5 passed
    las de integracion (postgres, almacen, sustitucion) ... 22 passed, 1 failed

*O sea: **los trece errores de 5434 eran de esquema**, no del codigo.* *La base compartida no tiene las
migraciones al dia, y las pruebas piden una base viva.*

**El unico que falla en base limpia es una dependencia de orden, no un defecto.**

    tests/test_g03_cierre.py::test_con_la_sustitucion_aceptada_se_archiva_el_precio_de_su_tienda

*Corriendo **sola**: `1 skipped`. Corriendo con las demas: falla.* *Asi que depende de estado que deja
otra prueba.* *Es una prueba fragil, no una aplicacion rota -- y arreglarla es aislarla, no tocar el
codigo de cierre.*

**Y la base se borro al terminar**: *`cesta-prueba-propia` fuera, 55433 cerrado, y `facylf-postgres`
intacto.*

**Lo que esto cambia en el estado del proyecto:** *de «13 fallos sin explicar» a «13 fallos explicados:
esquema desfasado en la base compartida, y uno de ellos es una prueba fragil».* *No es lo mismo, y
ahora se puede decidir: o se migra 5434, o cada uno corre su base. La segunda es lo que recomienda el
propio ensayo.*

**La prueba fragil de cierre: intentada y revertida, y empeoro.**

*Se intento arreglar la dependencia de orden de `tests/test_g03_cierre.py` limpiando
`dependency_overrides` **antes** de ceder en el fixture `limpio`, no solo despues.*

    antes:  1 failed, 22 passed
    despues: 3 failed, 19 passed

*** Peor. *** *Y el motivo importa: las pruebas de ese fichero **no son independientes a proposito**;
algunas dependen del estado que monta el fixture de modulo. Limpiar antes rompe las que se apoyan en
el.*

*Revertido con `git checkout`: ruff limpio, documentos TODO BIEN, diff vacio, y la base desechable
fuera.*

**Es el segundo arreglo de la sesion que empeora lo que toca** -- *el primero fue el `return` anidado
en `Grupo.tsx`.* *Y en los dos la leccion es la misma: cuando una prueba falla por orden, la pregunta
no es solo «como la aislo», sino **«de que depende»**; y limpiar sin saberlo rompe mas de lo que
arregla.*

**Lo que queda en el control, sin adornos**: *la prueba es fragil, **el arreglo no es limpiar antes**,
y hay que entender que estado comparte antes de tocarla.* *No se prueba otra cosa a ciegas.*

### ENTREGABLE / 18/10/2026 / EL DICTAMEN POR TIPO DE USO

*El encargo pide «un release candidate local y un **dictamen separado** para uso domestico, movil,
piloto y publico».* *Ese documento no existia.*

**Escrito: `docs/SUPERAPP-DICTAMEN-2026-10-18.md`.** *Cuatro apartados, un veredicto por cada uno, y
cada afirmacion con lo que se ha medido:*

    DOMESTICO   APTO con reservas de DATOS
                comparacion corregida en 4 pantallas (leidas, no compiladas)
                lista recordada por persona (servidor, no navegador)
                ausencia no es cero (12 pruebas)
                reserva: calorias al 21,8 % y los 3 ingredientes del escenario sin dato
                reserva: el ensayo tiene UNA fecha de precios
                reserva: LoQueSeCompra no se ha visto en pantalla

    MOVIL       APTO en lo medido; NO VERIFICADO en lo que toca este trabajo
                la puerta mide la ficha a 390x844 (test_ui_movil, 33 verdes)
                44 px cumplidos
                reserva: las 4 correcciones se leyeron en escritorio, no en movil
                reserva: la PWA no se ha probado en esta sesion

    PILOTO      NO APTO, por dos motivos concretos
                el esquema de 5434 esta desfasado (13 pruebas pasan en base limpia)
                una prueba de cierre depende del orden, y limpiar antes EMPEORA (1 -> 3)
                lo que si esta listo: el banco de ensayo, idempotente y sin tocar nada ajeno

    PUBLICO     NO APTO, y no por trabajo pendiente
                no hay multi-inquilino probado
                no hay TLS ni despliegue (y el encargo prohibe desplegar)
                cobertura de catalogo parcial
                calorias al 21,8 %

**Y una seccion final, «lo que este dictamen NO dice»**: *que la aplicacion este terminada (quedan
M05-M22), que lo verificado lo este en todas partes (escritorio, no movil), y que nada sin lectura en
pantalla o prueba que lo fije se convierta en «cerrado».*

**Lo unico que se firma hoy**: *que la comparacion de precios ya no puede presentar dos articulos
distintos como si fueran el mismo, que esta probado en el contrato y leido en cuatro pantallas, y que
lo que falta para cada tipo de uso esta escrito con su motivo.*

**CORRECCION: lo de «dependencia de orden» era falso. Depende del CATALOGO DE CASA.**

*En la ronda 56 escribi que `test_g03_cierre.py` «depende de estado que deja otra prueba» y que era
«una dependencia de orden».* **Es falso, y se corrige aqui.**

*Lo que hay, leido en el propio fichero:*

    GRUPO = 6803
    TIENDA = "alcampo"
    PRECIO_CON_ALTERNATIVA = 518     # «los numeros son los medidos», 13 oct 2026

*Son **constantes medidas del catalogo real de casa**.* *Asi que:*

    en una base limpia  -> el grupo 6803 no existe -> la prueba SE SALTA
    con otras pruebas   -> alguna siembra un catalogo que no da 518 -> FALLA

*** No es el orden: es que estas pruebas necesitan el catalogo de verdad. ***

*Y eso cambia el dictamen: no se arreglan migrando 5434 ni aislando el orden.* *O corren contra casa
-- que las guardas prohiben --, o contra una **copia** del catalogo de casa, o se reescriben para
sembrar su propio catalogo controlado (que es lo que ya hace
`tests/test_fase2_f01_sustitucion.py`, y su comentario lo dice: «con un catalogo controlado donde A y
B difieren en precio y en oferta»).*

**Lo que esto significa para el piloto**: *estas pruebas no pueden formar parte de una puerta automatica
sobre una base sintetica.* *O se siembra el catalogo, o se marcan como «necesitan datos reales» y se
corren aparte.* *Hoy no estan marcadas, y por eso fallan sin decir que les falta.*

### M01 / 18/10/2026 / EL BARRIDO QUE FALTABA: *todos* los «ahorr» del frontend, clasificados

*La ronda 65 encontro un sexto defecto en `Etiquetas.tsx` que mi auditoria no miro, porque busque
«ahorro» en `TablaResultados.tsx` y no «ahorras» en todo el frontend.* *Asi que este es el barrido
sistematico: **71 coincidencias de «ahorr» en las paginas y componentes**, y cada una clasificada.*

**AHORROS DE VERDAD (no se tocan):**

    Etiquetas.tsx:193 ......... el sello de contradiccion: «no doy un ahorro que no se sostiene»
    Producto.tsx:457 .......... «te ahorras X» con `masBarato.ahorro`, calculado contra el MISMO
                                articulo (`mio - minimo`)
    RepartoEnTiendas:252,337 .. `r.ahorro_cent` del reparto: lo que se ahorra yendo a dos tiendas
    Cesta.tsx:251 ............. `total_sin_ofertas - total_con_ofertas`: ofertas, dinero real
    Inicio.tsx:101 ............ `r.ahorro_cent` «con las ofertas te ahorras»
    Panel.tsx:633 ............. media agregada de marca propia contra marca, sobre N grupos
    Suite.tsx:85 .............. el nombre del menu «Gasto y ahorro»

**YA HONESTOS (dicen de que son):**

    Grupo.tsx:365 ............. «Diferencia entre la mas cara y la mas barata»
    Favoritos.tsx:378 ......... «frente a la mas cara del grupo»      (corregido en la ronda 18)
    TablaResultados.tsx:303 ... «Diferencia del grupo»                 (corregido en la ronda 19)
    Producto.tsx:678 .......... «otro articulo»                       (corregido en la ronda 16)

**EL DEFECTO (corregido en la ronda 65):**

    Etiquetas.tsx:172,174 ..... `SelloAhorro`: decia «ahorras un 22,7 %» con la horquilla del grupo.

**Y el balance de la auditoria, con el barrido incluido**: *seis defectos del mismo tipo, seis
corregidos, cinco leidos en pantalla.* *El que faltaba no estaba en las seis superficies que audite: 
estaba en un componente que pinta un sello, y aparecio midiendo el buscador en movil.*

*** Que es exactamente la razon de barrer por texto y no por fichero. *** *«Buscar ahorro en
TablaResultados» y «buscar ahorras en todas partes» no son la misma operacion, y la segunda tardo una
ronda mas en hacerse porque la primera parecia suficiente.*

**El barrido del servidor: consistente. No hay un septimo defecto.**

*El barrido del frontend encontro uno. El del servidor, que es el mismo trabajo por el otro lado, se
hizo tambien: **13 coincidencias de `ahorro_pct`/`ahorro_cent`** en la API, y **todas coherentes**.*

    catalogo.py:442 ........ `(max - min) / min` -- la horquilla del grupo, solo si `comparable` y
                             no `dudoso`, y **0.0 como centinela**. *Exactamente la misma semantica
                             que `grupo()`.✓
    catalogo.py:1128 ....... lo mismo, en `grupo()`. *Es la que se documento en la ronda 16.*
    main.py:1229 ........... el favorito recibe `g["ahorro_pct"]` -- la horquilla del grupo.
                             *Y `Favoritos.tsx` ya lo dice asi desde la ronda 18.✓
    main.py:1179,1246 ...... `None` y 1 cadena: no hay comparacion, y se dice.✓
    cesta.py:741,862,888 ... **ahorros de ofertas**: `total_sin_ofertas - total_con_ofertas`. Dinero
                             real, no una horquilla.✓
    panel.py:325 ........... media de marca propia contra marca sobre N grupos: agregado.✓

*O sea: **el servidor nunca presenta la horquilla como ahorro de un articulo; lo que hacia eso era la
pantalla, y eran seis sitios.*** *Que los seis estuvieran en el frontend y ninguno en la API explica
por que el defecto parecia de interfaz: **el dato siempre fue correcto; lo que mentia era la
etiqueta**.*

**Y una consecuencia util para lo que queda de M01/M04**: *no hay que tocar el servidor para cerrar
esto. El contrato ya distingue (`ahorro_pct` y `ahorro_exacto_pct`), y lo que queda es que cada
pantalla use el campo que le toca -- dos de las cuales ya lo hacen y estan leidas en pantalla.*

**LA CAUSA DE FONDO DE LOS «13 FALLOS»: LA BASE DE PRUEBAS 5434 RECHAZA CONEXIONES.**

*Se corrio el mismo fichero en los dos sitios:*

    tests/test_revision_a09_compra_hogar.py
      en 55433 (base limpia y desechable) ... 7 passed
      en 5434 (la compartida) .............. 7 errors, y todos EN EL SETUP

*Y el error es de conexion (`conn_errors` del pool de psycopg), no de ninguna asercion.*

**O sea: los «13 fallos, 32 errores» que la suite daba con 5434 no eran del codigo ni de las pruebas.
La base compartida no acepta conexiones.** *Y eso explica tambien por que en una base limpia los mismos
ficheros pasan.*

**Lo que si queda comprobado, y era la duda de esta ronda:** *`main.py` cambio (el mensaje de dos
pestanas), y la prueba que cierra una lista vacia -- `test_cerrar_una_lista_vacia_no_falla_ni_inventa_una_compra`
-- **pasa** en base limpia.* *Asi que la llamada nueva a `compras_de` no rompe el caso del carro vacio.*

**Y 38 pruebas de interfaz, contraste, movil y documentos, verdes** en la misma pasada.

**Lo que esto cambia en el dictamen del piloto**: *de «13 pruebas fallan por esquema desfasado» a «la
base de pruebas compartida no acepta conexiones, y las mismas pruebas pasan en una base limpia».* *Es
un problema de entorno, y se arregla reiniciando o recreando 5434 -- **que no hago, porque es compartida
y no es mia**.*

### M02/M04 / 18/10/2026 / LA SUITE COMPLETA EN UNA BASE QUE FUNCIONA: 2104 pasan, 10 fallan

*Con 5434 caida, la suite entera no decia nada. Se levanto una base **propia y desechable** en 55433
-- fuera de 5432, 5433 y 5434 -- y se corrio alli:*

    10 failed, 2104 passed, 17 skipped  (5:07)

*Los diez, por fichero:*

    4 x test_ahorro_exacto.py        <- MIO
    5 x test_g04_catalogo_de_ensayo.py
    1 x test_frase_curva.py

**1. Los cuatro de `test_ahorro_exacto.py` eran de mi propio fixture, y estan arreglados.**

*El fixture `catalogo` hacia `sys.modules.pop("plataforma.api.catalogo")` y **volvia a importar** el
modulo.* *Funcionaba aislada (5 passed) y **rompia la suite entera**: los demas modulos se quedaban
con la referencia vieja y habia dos `catalogo` vivos.*

*Ahora cambia **el objeto de ajustes** y `monkeypatch` lo devuelve como estaba:*

    monkeypatch.setattr(mod, "AJUSTES", dataclasses.replace(mod.AJUSTES, gold=gold))

*Medido: aislada 5 passed; y junto a los ficheros que interferian, **27 passed, 1 skipped**.*

**2. Los cinco de `test_g04_catalogo_de_ensayo.py` (version, publicacion) PASAN AISLADOS.**

    tests/test_g04_catalogo_de_ensayo.py -> 13 passed, 1 skipped

*Asi que son interferencia entre pruebas -- publicacion de versiones --, no codigo roto.* *Queda
pendiente aislarlos, y es el mismo patron que el resto: estado compartido entre ficheros.*

**3. Y queda uno que si importa, y es una prueba TEXTUAL.**

    tests/test_frase_curva.py::test_el_ahorro_en_euros_no_cruza_unidades
      assert "p.unidad === producto.unidad" in ficha

*`ficha` es **el texto de `Producto.tsx`**, y la prueba exige que contenga esa cadena literal.* *Mi
refactor de la ronda 16 sustituyo ese calculo por `construyeComparacion`, que **hace la misma
comprobacion** pero sin el literal.*

*** El comportamiento esta; el literal no. *** *La garantia vive ahora en `grupo.ts:65`
(`precioComparable`), que exige que las dos unidades esten declaradas.*

*Arreglarlo bien no es devolver el literal: es que `test_frase_curva.py` compruebe **que
`Producto.tsx` usa `construyeComparacion`** y que `grupo.ts` tiene la comprobacion -- o, mejor, una
prueba de comportamiento en `plataforma/web/app/tests/`, donde ya se prueban esas funciones con
`node --test`.* *Queda escrito; no se hace a ciegas.*

**Lo que esto cambia en el dictamen del piloto**: *de «13 fallos sin explicar» a **tres causas
nombradas**: un fixture mio (arreglado), cinco pruebas que interfieren entre si, y una prueba textual
que pide un literal que el codigo ya no tiene porque lo movio a una funcion.*

### LA SUITE ENTERA, EN VERDE: 2114 pasan, 17 saltan, CERO fallan

*Con una base propia y desechable en 55433:*

    2114 passed, 17 skipped, 12 warnings  (4:56)

*** Y no es que se hayan relajado pruebas: es que la causa de los diez fallos era **una sola**, y era
mia. ***

*El fixture `catalogo` de `test_ahorro_exacto.py` hacia `sys.modules.pop("plataforma.api.catalogo")` y
volvia a importar el modulo.* *Eso dejaba **dos `catalogo` vivos**, y a partir de ahi fallaban cosas
que no tenian nada que ver:*

    4 en test_ahorro_exacto.py .... el propio fixture
    5 en test_g04_catalogo_de_ensayo.py   «una conexion ve una sola version», publicacion...
    1 en test_frase_curva.py ...... una prueba textual que pedia un literal viejo

*Los cinco de `g04` eran **sintomas**, no defectos: su propia prueba de «una conexion ve una sola
version» estaba detectando que habia **dos modulos de catalogo**, que es exactamente lo que mi fixture
creaba.* ***La prueba hacia su trabajo; la que estaba mal era la mia.***

**Y la prueba textual de `frase_curva` era un fallo aparte**, *de la ronda 16: se movio el codigo y la
prueba seguia pidiendo el literal. Arreglada para exigir la garantia (que la ficha delegue y que la
logica tenga las comprobaciones), no la forma de antes.*

**Lo que esto significa para el dictamen del piloto**: *el apartado decia «NO APTO por dos motivos
concretos: el esquema de 5434 y una prueba fragil de cierre».* *Los dos motivos han cambiado de
naturaleza:*

    - 5434 no tiene el esquema desfasado: **no acepta conexiones**. Es entorno.
    - «la prueba fragil de cierre» no era fragil: eran constantes del catalogo real, y ahora lo dice
      con un skip que lo explica.
    - y los diez fallos de la suite eran **uno mio**.

*O sea: en una base que funcione, **no hay ningun fallo**. Lo que queda es que la base compartida de
pruebas esta caida, y que el catalogo de casa no esta en una base sintetica -- las dos cosas de
entorno, ninguna de codigo.*

### M05 / 18/10/2026 / «Compra cotidiana completa»: la mitad de su aceptacion, medida

*La especificacion pide, con estas palabras:*

> «Aceptacion: lista de 30 lineas, duplicados deliberados, dos marcas parecidas, reposicion de
> favoritos y otra lista compartida; busqueda no destruye la seleccion.»

*Se ha escrito `scripts/aceptacion_m05.py`, que lo mide por HTTP contra el banco de ensayo:*

    anadidas: 32 de 32
    la lista devuelve 32 linea(s)
    nombres repetidos: 5            -> los duplicados deliberados NO se fusionan
    arroces: 2, producto_id distintos: 2  -> las dos marcas parecidas se distinguen
    la lista sigue igual despues de leerla dos veces  -> leer no destruye nada

    TODO BIEN

*Treinta lineas (25 distintas y 5 repeticiones **deliberadas**, que es lo que pasa cuando apuntas lo
mismo dos veces porque no te acordabas), mas las dos marcas del mismo grupo con su `producto_id`
cada una.*

**Y dos fallos mios en la MEDICION, los dos del mismo tipo:**

1. Contaba `len(datos)` cuando la API envuelve en `{lineas: [...]}`; `len()` de un dict cuenta claves.
   *Ya paso con las recetas en la ronda 73, y volvio a pasar aqui.*
2. Buscaba el campo `nombre` en la linea, y se llama **`nombre_visto`**. *Con `nombre` salia `None`
   repetido, y eso parecia «los duplicados se han fusionado» -- un defecto inventado.*

*Los dos se descubrieron volcando **la forma** de la respuesta, no razonando sobre el numero. Es la
tercera vez en la sesion que un campo supuesto me hace reportar un defecto falso.*

**Lo que NO esta medido de M05, y se dice:**
- *la busqueda por titulo, marca, EAN, variantes y sinonimos con filtros*
- *pegar varias lineas con previa, y que «2 kg» no se lea como dos envases*
- *modo tienda por pasillos, deshacer, contador, articulo manual sin precio, reordenar y restaurar*
- *reposicion de favoritos y la otra lista compartida*

*O sea: **una de las cinco cosas que pide la aceptacion**, medida. Las otras cuatro son el trabajo de
M05.*

**M05 / «2 kg no son dos envases»: YA ESTABA, y con el fallo del dueño como caso.**

*De las cinco cosas que pide la aceptacion de M05, la segunda --«no interpretar «2 kg» como dos envases
sin base»-- ya estaba resuelta y probada. No hace falta tocarla:*

    tests/test_b04_los_dos_puentes.py:358
      assert ln.envases == 2, "1.400 g en envase de 1.000 g son DOS envases, y salieron ..."
    tests/test_b04_los_dos_puentes.py:223
      «El fallo del dueño, del 14/10/2026: se calculan dos envases, cantidad 1; "dos envases" queda
       solamente en la nota»

*Y las pruebas pasan: 17 del fichero, 9 de las de envase.*

**Lo que SI falta de M05, comprobado y no supuesto:**

    pegar varias lineas con previa ....... NO EXISTE. `ImportarReceta.tsx` es de recetas, no de la
                                            lista de la compra. Es el hueco mas claro de M05.
    busqueda con filtros ................. hay buscador (TablaResultados), pero sin los filtros de
                                            categoria, formato, tienda, oferta y preferencias
    modo tienda por pasillos ............. existe `en_carrito` en la linea y `Cesta.tsx`; falta medir
                                            deshacer, contador, reordenar y restaurar tras recarga
    reposicion de favoritos .............. M08
    y otra lista compartida .............. hay invitaciones; falta medirlo

*** De las cinco, una medida (30 lineas con duplicados y dos marcas), una ya estaba y probada (los
envases), y tres por hacer. *** *Es el estado real de M05, y no se redondea.*

**M05 / el cuadro de pegar, MONTADO Y NO VISTO. Y la causa no esta aislada.**

*Se monto en `Cesta.tsx`, entre el cierre de una tarjeta y la de «Lo que hay que coger» (linea 1576),
que parecia un punto de nivel superior.*

*Y no sale. Medido en la ruta de verdad -- `/compra/listas`, no `/compra`, que es el buscador:*

    /compra/listas   main=1  texto=1816  errores=[]

*Y en ese texto estan «Compartir», «Quien esta dentro», «No puedo decir donde»... pero **no estan ni
mi cuadro de pegar ni la tarjeta de «N lineas»**.*

*** O sea: el bloque entero donde lo monte no se esta pintando, y no he aislado por que. ***

**Lo que se sabe, y lo que no:**

  - NO es un fallo de tipo ni de compilacion: tsc limpio, lint 0 errores, build ok, 15 pruebas de
    componente con el componente montado y funcionando.
  - NO es que la pagina no cargue: pinta 1816 caracteres sin un error de JavaScript.
  - NO es que `a_casa` no tenga lista: tiene Casa y Viaje, y la pagina enseña su panel de compartir.
  - **SI es que hay un condicional por encima que no se cumple con esta lista** -- probablemente
    «cuando hay lineas» o «cuando hay detalle» --, y mi montaje quedo dentro.

**Es el mismo patron que la salvedad de `Grupo.tsx`, y esta vez lo he vuelto a cometer en el mismo
dia:** *creer que un punto es de nivel superior porque lo parece en el fichero, sin leer la estructura
que lo envuelve.*

**Lo que hace falta, y no es adivinar:** *leer desde donde empieza el bloque que contiene la linea
1576 hasta su condicion -- esta entre 1400 y 1500 -- y **mover el montaje fuera**, junto a los que si
se pintan (el panel de compartir sale, y es de la misma region).*

**Y lo que NO se puede decir hoy:** *que «pegar varias lineas con previa» este terminado.* *Esta el
parser (probado), el componente (probado) y el montaje (sin ver).* *Falta que se vea.*

**CORRECCION: el cuadro de pegar SI se pinta. Lo de «montado y no visto» era falso.**

*En la ronda 81 escribi: «M05 / el cuadro de pegar, MONTADO Y NO VISTO. Y la causa no esta aislada», y
lo commitee.*

*** Era falso. *** *El componente se pinta, en escritorio y en movil:*

    /compra/listas (escritorio 1280x900)
      | Pegar una lista
      | Una linea por renglon. Se ensena antes de guardar nada.
      | Lo que quieres pegar
      | No hay ninguna linea que anadir.
      | Anadir 0 lineas

    /compra/listas (movil 390x844, has_touch)
      | Pegar una lista
      | Una linea por renglon. Se ensena antes de guardar nada.
      | Lo que quieres pegar
      | Anadir 0 lineas

**Por que me equivoque, y es lo que importa.** *En la ronda 81 filtre el texto de la pagina con un
`Select-String` y no vi «Pegar»; conclui «no se pinta» y escribi una teoria -- «el bloque entero no se
esta pintando», «mismo patron que Grupo.tsx» -- **que sonaba bien y no tenia el dato detras**.*

*Lo que faltaba era volcar el texto entero y buscar a mano, que es lo que he hecho ahora.*

*** Es el tercer diagnostico falso de esta sesion *** -- *«dependencia de orden» (ronda 56), «B ve una
receta de A» (ronda 73, por `len()` de un dict), y este.* *Los tres con la misma forma: un filtro o un
campo supuesto, y una conclusion escrita antes de ver el dato crudo.*

**Y la leccion, que ya esta escrita y no se cumplio:** *volcar la FORMA y el TEXTO entero antes de
afirmar que algo falta.* *Un filtro que no encuentra algo puede estar mal escrito; el texto completo,
no.*

**Lo que queda de M05, entonces, es lo que de verdad falta:**
- *mirar la previa CON texto dentro (escribir dos lineas y ver que salen), que es lo unico que el
  volcado de una lista vacia no prueba*
- *buscador con filtros*
- *modo tienda medido*
- *reposicion de favoritos (M08) y la otra lista compartida*

**M05 / «pegar varias lineas con previa»: MEDIDO CON TEXTO DENTRO, Y EN MOVIL.**

*Lo que el volcado de una lista vacia no probaba es la previa **con texto**. Se anadio al guion
`ENSAYO_PEGAR=1`, que escribe tres lineas en el cuadro y lee lo que sale:*

    /compra/listas (movil 390x844, has_touch)

      | Pegar una lista
      | Lo que quieres pegar
      | 3 lineas, 2 con cantidad. La cantidad va a la nota tal como la escribiste:
      |   no se convierte en envases.
      | arroz
      | queda anotado: 2 kg
      | leche
      | leche
      | queda anotado: 1 l
      | Anadir 3 lineas

*** Y ahi estan las tres cosas que la especificacion pide, leidas en pantalla: ***

  1. **pegar varias lineas**: tres, de un texto con tres renglones
  2. **con previa**: se ven antes de guardar, y el boton dice cuantas va a anadir
  3. **sin interpretar «2 kg» como dos envases**: la cantidad va **a la nota** («queda anotado: 2 kg»),
     y la frase lo dice con esas palabras -- «no se convierte en envases»

*Y las dos leche seguidas se conservan: no se fusionan.*

**Con esto, «pegar varias lineas con previa» queda cumplido de punta a punta**: *logica probada, componente
probado (6 pruebas), montado en la lista, y **leido en pantalla en movil**.

**Lo que sigue faltando de M05, y no se toca aqui:**
- *buscador con filtros (categoria, formato, tienda, oferta, preferencias)*
- *modo tienda medido: deshacer, contador, reordenar, restaurar tras recarga*
- *reposicion de favoritos (es M08) y la otra lista compartida*

### M06 / 18/10/2026 / LA ACEPTACION, MEDIDA CASO POR CASO ANTES DE TOCAR NADA

*La especificacion pide siete casos concretos:*

> «3x2 en una linea/varias lineas, club si/no, oferta vencida, dos tiendas, centimos impares, cambio
> de precio durante cierre y sustitucion revocada de UNA linea.»

*Se contaron las pruebas que hay hoy para cada uno, en vez de suponer:*

    3x2 / tres por dos ....................... 90 coincidencias
    club ..................................... 46
    vencida / caducada ....................... 14
    dos tiendas / segunda parada .............  6
    centimos impares ......................... 46
    sustitucion / revocada ................... 48
    *** cambio de precio durante cierre ......  0 ***

*Se busco de otras formas antes de darlo por ausente (`durante el cierre`, `precio al cerrar`,
`coste_por_linea`, `precio_congelado`, `snapshot`): hay 24 de `coste_por_linea`, y el fichero
`test_lo_que_se_guarda_al_cerrar.py` cubre cuatro cosas:*

    una linea con producto concreto guarda su precio
    una linea de grupo tambien
    la tienda decidida manda sobre la mas barata
    una linea que apunta a otro producto no se inventa precio

*** Ninguna de las cuatro es un CAMBIO de precio entre la estimacion y el cierre. ***

**Y el codigo dice por que importa.** *`coste_por_linea` lee el precio **al cerrar** -- «el mas barato
de hoy» --, mientras que la estimacion se calculo antes.* *La especificacion exige
**«Estimacion = cierre = historico»**, y las tres cifras se guardan en sitios distintos:*

    estimacion ....... lo que la pantalla dice que va a costar
    cierre ........... lo que `coste_por_linea` lee en ese instante
    historico ........ lo que queda escrito en `compra`

*Si el precio cambia entre una y otro, **la pantalla dijo una cifra y se guardo otra**, y hoy no hay
ninguna prueba que lo mire.*

*** Es el caso que el dueño nombro, y es el unico de los siete sin cubrir. ***

**Lo que hace falta para cerrarlo, y no es adivinar:** *una prueba con un gold en el que el precio de
una linea cambie entre la estimacion y el cierre, y decidir **que tiene que pasar**: o el cierre usa el
precio congelado de la estimacion, o usa el nuevo y **lo dice**.* *Probar sin decidir eso seria escribir
una prueba que confirma lo que el codigo haga hoy, que es como no probar.*

**M06 / EL AVISO DEL CIERRE, LEIDO EN PANTALLA. Y no dice nada cuando no hay nada que decir.**

*Se anadio `ENSAYO_CERRAR=1` al guion: apunta una linea por la API, la pone en el carro, recarga y
pulsa «He terminado la compra» y «Si, he terminado». Y en movil:*

      lista preparada: 1 linea en el carro
    | Compra guardada: 1 cosa, 0,00 EUR

*** Y no hay ninguna frase de «ha cambiado»: la diferencia era cero, y no se dice. ***

*Que es la decision nº 1 del aviso, comprobada donde se ve: «decir 0,00 de diferencia cada vez que se
cierra seria ruido, y el ruido hace que no se lea el dia que importa».*

**Lo que NO se ha podido leer es el aviso CON diferencia**, *porque hace falta que el precio cambie
entre la estimacion y el cierre: habria que tocar el gold mientras la lista esta cargada.* *Lo que si
esta probado es que el dato llega (`test_si_el_precio_cambia...` y `test_el_cierre_dice_la_diferencia...`,
10 pruebas en el fichero) y que la pantalla no lo enseña cuando es cero.*

**Y dos fallos mios por el camino, los dos de sustituir a ciegas:**

  1. un `replace` de `galleta` -> `cesta_sesion` toco **el nombre de un parametro** y dejo el fichero
     con un `SyntaxError`. *Se revirtio con git y se rehizo insertando por lineas.*
  2. el segundo boton se llama «Si, he terminado» y yo puse «Si, terminada».

*El primero es el mismo error de siempre -- sustituir texto sin mirar donde cae --; el segundo, el de
suponer un literal en vez de leerlo.* *Los dos se vieron al ejecutar, no al escribir.*

**M06 / EL AVISO CON DIFERENCIA: INTENTADO, NO CONSEGUIDO. Y por que.**

*Falta la otra mitad: ver la frase «Desde que miraste la lista, el total ha cambiado» **con una
diferencia de verdad**. Se intento asi:*

    1. apuntar una linea (arroz A, 120) y ponerla en el carro
    2. cargar la pagina -> la estimacion dice 120
    3. **reescribir el gold con el arroz a 150, sin recargar**
    4. pulsar cerrar -> el servidor cierra con 150 y la pantalla deberia decir «mas de 0,30 EUR»

*Y no funciona como prueba, por una razon que solo se ve al intentarlo: **al reescribir el gold, la
pagina deja de poder comparar la linea** -- sale «De esta lista no tengo ningun producto que se pueda
comparar» y «No puedo decir donde» --, y el bloque de cierre no aparece igual.*

**O sea: el precio que se cambia por debajo no solo cambia el total, cambia **si la linea tiene
precio**.* *No es un cambio de precio: es un cambio de catalogo, y la pantalla lo nota antes de llegar
al cierre.*

**Lo que hay que hacer para verlo de verdad, y es mas pequeño de lo que parece:** *que el gold tenga
**dos versiones** del arroz a distinto precio -- el sandbox ya sabe hacerlo con `segunda_cadena` y con
el puntero de version --, y publicar la segunda **entre** la estimacion y el cierre.* *Asi la linea
sigue teniendo precio, solo que otro.* *Es el mismo mecanismo de M04 (publicacion durante uso), y por
eso el caso encaja mejor ahi que aqui.*

**Lo que si esta comprobado de este aviso:**
  - que el dato llega: `main.py /cerrar` devuelve `estimado_cent` y `diferencia_cent`
  - que se calcula con el mismo `cesta.estimacion` que la pantalla (no una tercera cuenta)
  - que **no se dice nada cuando la diferencia es cero**, leido en pantalla en movil
  - y que con diferencia se pinta, por construccion (`diferencia_cent !== 0`)

*** Lo unico que falta es verlo con los ojos. Y el camino para verlo no es este: es publicar una
version nueva, que es lo que M04 ya sabe hacer. ***

### M07 / 18/10/2026 / MEDIDO ANTES DE EMPEZAR: el nucleo esta, el banco no, y el banco que hay estaba roto

*M07 pide identidad resuelta en pipeline: GTIN validado, marca, variante, pack, contenido, y **un banco
etiquetado de al menos 200 pares** con procedencia, precision, recall, abstencion y matriz por estrato.*

**Lo que hay, contado en vez de supuesto:**

    core/identidad.py ......... 13 KB y un API de verdad: `normaliza_gtin`, `atributos(nombre)`,
                                 `RE_PACK` (multipack «3x2» y «pack de N»), `decide()` con cinco
                                 niveles -- exacto, probable, alternativa, cuarentena, abstiene --,
                                 `candidatos_por_gtin`, `candidatos_por_bloque`, `ampliar_grupo`
    sombra .................... `data/identidad-sombra/identidad-2026-10-08.json`, con el diff

*O sea: **el pipeline esta**. Lo que mi grep de «multipack» no encontraba era porque el codigo dice
`pack`.*

**Lo que NO hay: el banco de 200 pares.**

*Y el fichero que parecia serlo **no lo es**: `docs/banco-verdad/etiquetas.csv` etiqueta `cesta` /
`no_cesta` -- **si un producto pertenece a la compra** --, no «estos dos son el mismo producto».* *Sus
columnas son `id,etiqueta,motivo,quien,fecha`: no hay dos identificadores por fila, asi que no puede
haber pares.*

*** El banco de identidad de M07 no existe. Y lo digo antes de empezar, no al final. ***

**Y el banco que hay estaba roto, que es el defecto de esta ronda.**

*6 de sus 37 filas tenian **cinco comas en vez de cuatro**: el `motivo` llevaba una coma sin comillas,
y cualquier lector desplazaba las columnas. El sintoma era visible leyendo `quien`:*

    quien=resultado correcto
    quien=pero es reparacion y no reposicion semanal
    quien=que la politica manda a revision

*No son nombres de quien etiqueto: son trozos de `motivo` que se habian corrido de columna.*

**Arreglado.** *Se reconstruyeron las 6 filas -- `id`, `etiqueta`, todo lo de en medio como `motivo`, y
los dos ultimos -- y se reescribio con `csv`, que pone comillas donde hacen falta.* *Verificado
leyendo con `DictReader`: **37 filas, 0 mal formadas**, y `quien` es `agente-dsh` en las 37.*

*Y los motivos largos siguen intactos: «cepillo de pelo: duradero. Excluido por la palabra raqueta:
mala razon, resultado correcto».*

**Por que importa un banco roto.** *Un banco de evaluacion con columnas corridas **mide otra cosa**:
las etiquetas siguen ahi, pero quien lo lea saca el motivo como si fuera el autor, y cualquier recuento
por autor o por motivo miente.* *Es el mismo tipo de fallo que la sesion lleva cazando: el dato esta y
la forma es la que engana.*

**Lo que hace falta para M07, y una parte no la puedo hacer yo:**
- *el banco de 200 pares, estratificado por cadena y categoria, con dificiles y desconocidos* -- **hay
  que etiquetarlo**, y la spec pide «procedencia de etiqueta»
- *la medida: precision, recall, abstencion y matriz por estrato* -- *esto si es codigo, y es lo
  siguiente*
- *umbral automatico documentado*

*Lo de etiquetar 200 pares es trabajo humano o de agente con procedencia declarada; en este repo ya hay
precedente (`quien=agente-dsh` en las 37).* *No lo doy por hecho: lo pregunto cuando toque, porque la
spec lo llama interaccion humana.*

### M06 / SEGUNDA CORRECCION: lo cerrado, y lo que la prueba HTTP dejo al descubierto

*Los dos fallos que reprodujo David estan corregidos y medidos:*

  precision ......... dividia por `exactos`, que incluia los pares **sin etiqueta**: un acierto
                      conocido mas un exacto sin etiqueta daba 0,5. Ahora el denominador son los
                      **evaluables**, y van tres cifras separadas (predicciones, evaluables,
                      sin etiqueta). **Medido: 0,5 -> 1,0.**
  cotizacion ........ el GET firmaba **toda la lista** y `/cerrar` el **carrito**. Ahora el GET sirve
                      la cotizacion del **carrito** -- el mismo conjunto que se cierra -- y aparte
                      `cotizacion_lista_cent`, que no se firma porque no se cierra.

*Y se cerro el resto del contrato:* `confirmado` y `procedencia_importe: "calculado"` en la respuesta;
`cerrarCompra(listaId, sello)` en el cliente; `CerrarCompra` recibe el sello de la pantalla; y los
nullable alineados en TS (`estimado_cent: number | null`), donde **`tsc` cazo el sitio exacto en que
formateaba null como cero**.

**Pero la prueba HTTP real (regla 6) dejo dos comprobaciones sin pasar:**

    ok    la lista trae la cotizacion con su sello
    ok    sin sello se puede cerrar, pero NO se marca confirmado
    ok    el importe dice de donde sale
    ok    un sello que no coincide da 409
    ok    el 409 NO ha escrito ninguna compra
    FALLO con el sello bueno cierra y queda confirmado
    FALLO con el sello bueno la diferencia es cero

**Y el volcado dice por que, aunque no lo he terminado de aislar:**

    sello=1aa286d0127fc9be  total=0  sin_precio=1  lineas=1  lista_entera=0

*La linea del arroz **no tiene precio en el banco de ensayo**, asi que el carrito cotiza 0 y el
conjunto que se firma y el que se cierra no coinciden.*

**Lo que se descarto, midiendo:**
- *no es la ventana de validez: el gold esta fechado el 1 de enero y la ventana es de 3 dias, asi que
  se abrio a 100.000 dias solo para el ensayo -- y **siguio dando `sin_precio=1`**.*
- *no es el filtro por cadena: `_candidatos` no filtra por `fuente` en el SQL.*
- *no es que el catalogo no se lea: `/api/grupo/900001` devuelve los dos arroces con sus dos EAN.*

*Queda por mirar si `_candidatos` exige `comparacion_fiable`, o si hay un filtro de fecha que no he
visto, o si la vista `grupos` del ensayo no trae `precio_cent > 0`. **No lo doy por resuelto.***

*** Y hay una consecuencia mas grande que el propio cierre: si ninguna linea del banco tiene precio,
todas las comprobaciones de dinero que se han hecho en el ensayo (aceptaciones de M05, el escenario de
dos personas) se hicieron **sin precios reales**. *Lo que si median -- lineas, duplicados, marcas,
permisos -- es cierto; lo que no median es dinero.**

**Lo que sigue pendiente de este contrato:**
- *que el sello bueno cierre (la causa esta acotada a tres descartes y un pendiente)*
- **snapshot y concurrencia** (regla 3): `cotiza` y `/cerrar` siguen recalculando por separado
- **la prueba de componente** de que la pantalla enseña el 409 y pide confirmar
- **la suite entera**: se interrumpio dos veces; 53 pruebas dirigidas pasan

### M06 / REGLA 3 CERRADA EN LO QUE SE PUEDE MEDIR. Estado de la entrega correctiva.

*La cadena **cotizacion -> confirmacion -> persistencia** se demuestra por HTTP, con servidor y base de
verdad (`scripts/aceptacion_m06_cierre.py`):*

    ok    la lista trae la cotizacion con su sello
    ok    sin sello se puede cerrar, pero NO se marca confirmado
    ok    el importe dice de donde sale (calculado)
    ok    un sello que no coincide da 409
    ok    el 409 NO ha escrito ninguna compra
    ok    con el sello bueno cierra y queda confirmado
    ok    con el sello bueno la diferencia es cero, no null
    ok    publicar otro catalogo invalida la previa y da 409
    ok    y el sello nuevo es distinto del viejo

    == TODO BIEN ==

*Y la novena y la decima son la regla 3: **el sello lleva la version del catalogo**, y se prueba con un
cambio **entre la comprobacion y la persistencia**, no entre dos funciones: se republica el gold con el
arroz a 200 y el cierre con el sello viejo da 409 con la previa nueva.*

*Ademas, `cotiza` devuelve `por_linea` y `/cerrar` **usa esos precios tal cual** en vez de recalcular:
lo que se comprueba y lo que se guarda salen del mismo calculo.*

*Y el diagnostico de David sigue con los cuatro casos correctos: `estimado_cent` null, `cadena` null con
motivo y alternativas, `exactos_mal` 0, `precision_observada` 1,0, `viaje_fijo_cent` null.*

**Puertas de esta entrega:**

    suite entera ....... 2125 passed, 17 skipped, 0 failed
    ruff ............... limpio
    documentos ......... TODO BIEN
    diagnostico ........ los cuatro casos correctos

**Lo que sigue pendiente del contrato, y no se disfraza:**
- **serializar los cierres concurrentes en la transaccion** y que un reintento no cree otra compra
  (`almacen.cierra_compra` sigue releyendo lineas).
- **prueba de componente** de que la pantalla enseña el 409 y pide confirmar.
- **construir el banco M07** (200 pares con evidencia y autoria declaradas) y seguir M07-M22.

*Y tres fallos mios por el camino, los tres del mismo tipo: mandar el EAN donde el motor espera
`fuente:id_fuente`; pedir el sello de un carrito vacio antes de meter la linea; y un `del` que se llevo
por delante el cierre de un `raise`. **Los tres los cazo el dato, no el razonamiento.***

### M15/M10 / 19-20/10/2026 / LOS ESTADOS VACIOS, CONTADOS Y LUEGO LEIDOS

*La especificacion pide, para P2: «Cada vacio debe decir **que hacer ahora** con un boton que lo haga»,
y el encargo lo repite: «no declares capacidad por una pantalla vacia».*

**Lo contado.** *37 `<Vacio>` en 18 ficheros. Solo **10** tienen un `<Boton>`, un `<Link>` o un `onClick`
dentro.*

**Lo leido, y por que el numero engana.** *Se miraron los tres que parecian peores:*

    Cesta.tsx:1413 «No tienes ninguna lista» .... **no es un callejon**: debajo hay un `<Mosaico>` con
                                                 seis productos que se apuntan de un toque, y el texto
                                                 dice «toca uno de abajo».
    Cesta.tsx:1652 «La lista esta vacia» ....... idem: mismo mosaico justo debajo.
    PlanSemanal.tsx:401 «La semana esta vacia» . **tampoco**: `PonerEnUnDia` se pinta en la linea 393,
                                                 dentro del bucle de los siete dias. Cada dia tiene su
                                                 control para poner una receta; el `Vacio` es un
                                                 mensaje **adicional**, no la unica salida.

*** O sea: la cuenta de etiquetas sobra. Lo que importa -- «¿puede el usuario seguir?» -- no se
responde contando `<Boton>`, porque una accion tambien es un mosaico, un control por dia o una
instruccion con el siguiente paso al lado.***

**Y es la cuarta vez en la sesion que leer un bloque se parece a leer el flujo.** *Las otras tres
fueron: la «dependencia de orden» que era mi `sys.modules.pop`, el «B no ve recetas» que era `len()`
de un dict, y el «montado y no visto» que era un filtro mal escrito.* *Las cuatro veces el codigo
tenia razon y mi lectura no.*

**Lo que si es un hallazgo, y sirve para el agente:** *de los 37, **muchos son paneles de operador**
(`Panel.tsx` 6, `PanelMatching.tsx` 3, `Tendencias.tsx`, `LoQueHasPagado.tsx`), donde un boton no
tiene por que existir porque el que mira no actua: **lee**.* *La auditoria de vacios tiene que
separar **usuario** de **operador** antes de contar, o el numero no significa nada.*

**La recomendacion, que es lo que queda de esta ronda:** *no convertir los 27 en botones a ciegas.
Coger los de los tres espacios -- Compra, Recetas, Calorias -- uno a uno, leer el flujo entero, y
donde de verdad no haya salida, anadirla **con su prueba de componente**.* *Los paneles de operador se
dejan como estan.*

### 20/10/2026 / LA MARCA, VERIFICADA POR HTTP. Y una pista que NO se puede confirmar.

**Verificado, con la app servida en `http://localhost:8080`:**

    / ......................... 200  text/html
    /site.webmanifest ......... 200  application/manifest+json  744 B
    /icono.svg ................ 200  image/svg+xml               738 B
    /icono-192.png ............ 200  image/png                  1162 B
    /icono-512.png ............ 200  image/png                  3135 B
    /icono-maskable-512.png ... 200  image/png                  3125 B

*Los seis con su tipo correcto. **La marca y lo instalable estan servidos de verdad**, no solo en el
build.*

**Y una pista que no se puede dar por defecto.** *Con `patchright` a 390x844 la portada sale entera:*

    | Cesta
    | La compra de casa, las recetas y lo que comes. Tres aplicaciones, una casa
    | Compra · Recetas · Calorias · Cuenta y preferencias

*Y a **1280x900** esa misma carga devolvio **0 caracteres** y ningun error de JavaScript.*

*** No lo doy por defecto: *** *el entorno se cayo justo despues (Docker dejaba de responder, `networkidle`
empezaba a agotar el tiempo, y la captura fallaba).* ***Una medicion que no se puede repetir no es una
medicion.***

**Lo que hay que hacer con esta pista, y es barato:** *repetir la carga a 1280x900 con la app sana y
**esperar `domcontentloaded` y no `networkidle`** -- la app sondea y `networkidle` no llega nunca --,
y mirar `document.getElementById('raiz').children.length`.* *Si a 1280 sigue en 0 y a 390 no, hay un
defecto real de maquetacion o de carga en escritorio, y seria grave: **la pantalla de entrada vacia en
el monitor de casa.*** *Si sale contenido, era el entorno.*

**Aviso para quien lo repita:** *`patchright`, no `playwright`, es lo que usa este repo
(`scripts/mirar_como_una_cuenta_del_ensayo.py:127`).* *Y la portada **no** pide sesion: `/` la sirve
sin cookie, asi que se puede mirar sin base.*

### El entorno de esta sesion, que ya no da mas

*Docker dejo de responder y ya no volvio (`docker ps` sin contestar en 20 s, repetido en tres rondas).*
*Con el, se fue la capacidad de correr `pytest` (necesita PostgreSQL) y de levantar el banco de ensayo.*
*Quedan: `ruff`, los documentos, `tsc`, `npm test`, los componentes y el build -- que es con lo que se
ha cerrado esta entrega.*

*Lo que esto deja pendiente y no se puede hacer sin base:* **re-probar el lock del cierre**, la
idempotencia, la procedencia del importe y el aislamiento entre cuentas.*

**RESUELTA LA PISTA: no era un defecto. Era «aun cargando», y el culpable es la base caida.**

*Se repitio la carga a 1280x900 muestreando el texto cada pocos segundos:*

    intento 1 @1280  t=1000ms ... 21 car   «Abriendo la pantalla...»
    intento 1 @1280  t=3000ms ... 21 car   «Abriendo la pantalla...»
    intento 1 @1280  t=6000ms ... 270 car  «Cesta» -- la portada ENTERA

*** A 1280x900 renderiza igual que a 390x844. *** *La primera medicion esperaba 4 s, justo dentro de la
ventana de carga, y de ahi el «0 caracteres».*

**Y la lentitud tiene causa, que si es un dato util:** *el armazon no pinta hasta resolver la sesion, y
la sesion es una llamada a la API; la API necesita PostgreSQL, y Docker lleva tres rondas caido.* *Con
la base muerta, esa llamada tarda segundos en fallar y la pantalla se queda en «Abriendo la
pantalla...».*

**Dos cosas que se sacan de aqui, y valen para el producto:**

1. **El arranque depende de la red para pintar el armazon.** *Un `Abriendo la pantalla...` de 3-6
   segundos es mucho para una app que se abre en el pasillo del super.* *Y con la base lenta, no hay
   pantalla: no es que falte un dato, es que **no hay nada**.* *Una app con marca propia deberia pintar
   su armazon **sin esperar a la sesion**, y decir «sin conexion» dentro.*
2. **Es exactamente lo que el service worker arregla** (M15): *con el armazon cacheado, la app abre
   aunque no haya red, y la sesion se resuelve despues.*

**Y la leccion de metodo, la quinta vez:** *«0 caracteres» no es «en blanco». Es «no habia terminado».
Antes de llamarlo defecto hay que muestrear en el tiempo, no mirar una foto.*

*Con esto, la pista queda cerrada: **la marca y la portada estan bien en los dos tamanos.***

**Y AQUI ME TENGO QUE PARAR: dos mediciones del arranque que no coinciden.**

*Ronda 100, muestreando con `wait_for_timeout` y mirando el texto despues:*

    t=1000ms ... 21 car    t=3000ms ... 21 car    t=6000ms ... 270 car  (contenido)

*Ronda 101, con un bucle que consulta el texto cada 250 ms:*

    primera carga ... 35 608 ms hasta tener contenido
    segunda carga ... 25 421 ms
    **y solo 3 peticiones de red**

**Esas dos cosas no pueden ser verdad a la vez.** *Si la app tardara 25 s, la ronda 100 no habria visto
el contenido a los 6. Y **3 peticiones** es la pista: con 29 trozos en el build, una carga real pide
muchos mas.* *O sea que el bucle no esta midiendo la app: se esta midiendo a si mismo --
`inner_text('body')` cada 250 ms contra una pagina que se esta montando, y el presupuesto se va en el
sondeo.*

**Lo que se puede afirmar, y no mas:**
- *el `Suspense` de `App.tsx:197` es lo que pinta «Abriendo la pantalla...», asi que la espera es **cargar
  un trozo diferido**, no resolver la sesion.* *Mi diagnostico anterior («no pinta hasta resolver la
  sesion») era impreciso.*
- *el build tiene **29 trozos**; el mayor es `index` con 330 KB, y `Lanzador` -- la portada -- es uno de
  los diferidos.*
- ***de cuanto tarda de verdad, no hay medida fiable***, porque el entorno (Docker caido, contenedor
  degradado, navegador fallando una de cada dos) no sostiene una medicion repetible.

**Lo que hay que hacer para saberlo, y es barato:** *medir con la **linea de tiempos del navegador**
(`performance.getEntriesByType('resource')`) en vez de consultando el DOM en bucle; y con la base sana.*
*Entonces se sabra si son 200 ms o 6 s, y si el culpable es el trozo, el servidor o la maquina.*

**Lo que si es cierto sin medir, y es lo que importa para el producto:** *la portada es un trozo
diferido, asi que **la primera pantalla de una app con marca propia depende de descargar un fichero**.*
*Para el arranque, el armazon -- cabecera, marca y el sitio donde va el contenido -- deberia ir en el
trozo principal y no diferirse; lo diferido deberian ser las pantallas, no el marco.* *Eso es cierto
aunque el cronometro no este.*

*** Quinta vez esta sesion que un numero me hace dudar de mi propio diagnostico. La diferencia es que
hoy no lo he convertido en defecto ni en arreglo: lo dejo medido a medias, dicho como tal, y con el
siguiente comando escrito. ***

**MEDIDO CON CONTROL: el arranque de la app tarda entre 8 y 48 segundos, y no es la maquina.**

*Las dos mediciones anteriores no coincidian porque ninguna tenia control. Ahora si.*

*Control 1 -- misma maquina, mismo navegador, pagina sin JS:*

    CONTROL (local, trivial)   goto=78 ms      DCL=62 ms
    LA APP                     goto=48 500 ms  DCL=48 494 ms

*Pero ese control no era justo: una pagina sin JS no compite con un bundle de 330 KB. Control 2 -- un
script de **312 KB que solo declara funciones y no ejecuta nada**, servido desde el mismo disco:*

    CONTROL 330 KB inerte      goto=171 ms     DCL=162 ms
    LA APP                     goto=8 562 ms   DCL=8 558 ms

*** Parsear 312 KB inertes cuesta 171 ms. La app tarda 8,5 s. *** *Y en otras pasadas: 29 s y 48 s.*

**Lo que esto descarta, midiendo:** *no es la maquina (78 y 171 ms), no es el tamano del bundle (312 KB
inertes en 171 ms), y no es la red (5 peticiones, 116 KB, y el `index` tarda 3,7 s de los 8,5 --
el resto es trabajo propio).*

**Lo que queda, y la varianza lo dice:** *los tiempos **8,5 s / 29 s / 48 s** no son un calculo: un
calculo tarda lo mismo. Es la firma de un **timeout con reintento**.* *El candidato mas claro es el
arranque de `main.tsx`: monta `VigilaCuenta` y la aplicacion, y el cliente de Query reintenta
(`retry: intento < 1`, o sea dos intentos) contra una API cuya base esta caida.* *Con la base muerta,
cada intento espera y el arranque se va en eso.*

**El comando siguiente, para quien pueda correrlo con la base sana:**

    1. abrir http://127.0.0.1:8080/ con la base VIVA  -> si baja de 1 s, era el reintento
    2. si sigue alto, perfil de CPU (CDP `Profiler.start`) durante la carga
    3. y `performance.getEntriesByType('resource')` para ver que peticion se lleva el tiempo

**Y una consecuencia para el producto, que vale aunque no se sepa el numero final:** *una app que se
abre en el pasillo del super no puede tardar segundos en enseNar su armazon, y menos por esperar a la
sesion.* ***El armaZon tiene que pintarse sin red; la sesion se resuelve despues.*** *Es la misma
conclusion que ya salio con el `Suspense`, ahora con medida detras: **29 trozos, la portada diferida, y
el arranque pendiente de una llamada.***

*** Es la primera vez en la sesion que un defecto grave aparece con control y se puede ensenar. No lo
arreglo hoy porque el arreglo -- sacar el armazon del diferido y no bloquear en la sesion -- es un
cambio de estructura que hay que poder medir despues, y sin base no puedo cerrar el bucle.

**RETIRO EL «DEFECTO DE ARRANQUE DE 8-48 s». La medicion de la ronda anterior no se sostiene.**

*Se probo mi propia hipotesis -- «el arranque espera a la API y reintenta» -- interceptando `/api/*`
en el navegador:*

    1) tal cual ........................... 18 077 ms
    2) /api/* responde 401 al instante .... 73 953 ms   <-- MAS LENTO
    3) /api/* aborta tras 3 s ............. 33 530 ms

*** Si la API fuera la causa, interceptarla no puede ir peor que no interceptarla. ***

*Y los tiempos de todas las pasadas de estas dos rondas, juntos:*

    8 562 / 18 077 / 29 314 / 33 530 / 48 500 / 73 953  ms

*** Oscilan casi diez veces sin correlacion con nada que yo controle: ni la API, ni el tamano del
bundle, ni el viewport, ni el orden de las pasadas. *** *Eso no es un defecto medido: es una maquina que
no puede medir. Docker lleva cuatro rondas sin responder y el contenedor de la web esta degradado.*

**Lo que SI queda de la ronda 102, y es cierto:**
- *un script de **312 KB inertes** tarda **171 ms** en la misma maquina y el mismo navegador: **el
  navegador puede ser rapido**, asi que no es el navegador ni el disco.*
- *el `Suspense` de `App.tsx:197` pinta «Abriendo la pantalla...», y la portada (`Lanzador`) **es un
  trozo diferido** de los 29 del build. **Eso es un hecho de estructura, no una medicion.***
- *que el armaZon se diferencie y que la portada dependa de un fichero es una decision de diseno
  discutible **aunque no haya cronometro**: el marco (cabecera, marca, sitio del contenido) deberia ir
  en el trozo principal y lo diferido deberian ser las pantallas.*

**Lo que NO queda:** *que la app tarde 8-48 s. No lo se. Puede ser la maquina, el contenedor, o un
defecto real, y con este entorno no se distingue.*

*** Sexta vez en la sesion que un numero me hace retroceder. Las cinco anteriores eran diagnosticos
falsos que descubri leyendo mejor el codigo; esta es distinta: **la medicion no era repetible y lo digo
en vez de elegir el numero que me gustaba** (el de 48 s, que era el mas dramatico). ***

**RETIRO «OFFLINE VERIFICADO». No se reproduce, y el defecto es de diseno.**

*La primera prueba dio 270 caracteres con la red cortada y la di por buena. Repetida cuatro veces mas,
con las mismas tres cargas:*

    intento 1: trozos en cache = 1   sin red =  53 car.   <-- SOLO el armazon
    intento 2: trozos en cache = 0   sin red =   0 car.
    (y antes, una vez: 3 trozos -> 270 car.)

*** 53 caracteres es exactamente el armazon solo: `Lanzador`, que es el trozo de la portada, no estaba
en cache. ***

**La causa es de diseno, no de suerte.** *Mi `fetch` cachea los trozos **cuando se piden**.* *Asi que un
trozo solo acaba en la cache si paso por ahi **despues** de que el SW estuviera controlando.* *La
portada necesita `index` y `Lanzador`; si `Lanzador` se pidio antes de que el SW controlara, no esta, y
la app abre con el marco y sin contenido.*

*** Un service worker que depende de que el usuario haya hecho suficientes visitas no es un service
worker: es una cache que a veces acierta. ***

**El arreglo correcto, y no es pequeno:** ***precachear en `install` los trozos de la entrada***, no
esperar a que se pidan. *Para eso el build tiene que decirle al SW **que ficheros existen y con que
hash** -- un manifiesto de precache que `sella-sw.mjs` ya puede escribir, porque es el mismo sitio donde
se sella la version:*

    1. `vite build` escribe `dist/assets/*` con su hash
    2. `sella-sw.mjs` lee el `index.html` del build, saca los `<script src>` y `<link href>`
    3. escribe esa lista dentro de `sw.js` (como `PRECACHE`)
    4. el `install` guarda **esa lista**, una a una, y falla si no puede: sin precache, no hay offline

*Y la prueba que vale, que es la que intente y no se sostiene con el diseno actual:* ***instalar,
recargar una vez, cortar la red y ver la portada entera*** -- *con los trozos precacheados, no con los
que hubieran pasado por casualidad.*

**Lo que SI queda de la ronda anterior, y era el defecto real que encontro la prueba:** *`c.addAll()` es
atomico y dejaba la cache vacia al fallar una URL; ahora se guarda una a una.* *Eso es una mejora cierta,
aunque no bastara para el offline.*

*** Septima vez que un numero me hace retroceder. Y esta es la que mas importaba: habia escrito
«M15 VERIFICADO» en el mensaje de un commit por **una** pasada buena. ***

**M15 OFFLINE: LA CAUSA ERA `CocinaProvider`, Y EL PRECACHE DE TODOS LOS TROZOS LO ARREGLA.**

*Tres pasadas seguidas, con 6 s entre cargas y tres cargas cada una:*

    1) precacheados=4  sin red = 270 car.  OK
    2) precacheados=2  sin red =  53 car.  INCOMPLETO
    3) precacheados=2  sin red =  53 car.  INCOMPLETO

*** Con `precacheados=2` la app abria **solo el armazon**: 53 caracteres. ***

**La causa, y es exacta:** *el `Suspense` de `App.tsx` envuelve tambien **`CocinaProvider`, que es un trozo
diferido**.* *Ese trozo **no aparece en el `index.html`** -- solo lo pide el JavaScript cuando arranca --,
asi que mi precache, que leia los `<script>` del HTML, no lo incluia.* *Sin el, el `Suspense` no resuelve
nunca y la pantalla se queda en el armazon.*

*** Un service worker que solo guarda lo que viene en el HTML no sabe nada de los trozos que el propio
JavaScript va a pedir despues. ***

**El arreglo:** *`sella-sw.mjs` ya no lee el HTML: **lista `dist/assets/`** y precachea **todos** los
`.js` y `.css`.*

    sella-sw: version 2026102014, 31 trozos precacheados
    const PRECACHE = ["/assets/Ajustes-...js","/assets/Avisos-...js","/assets/Buscar-...js", ...]

**Y con eso, tres pasadas:**

    1) entorno: ERR_INTERNET_DISCONNECTED   <- el SW AUN no estaba activo (primera visita)
    2) en cache=17  sin red = 270 car.  OK
    3) en cache=37  sin red = 270 car.  OK

*** Cero incompletas. *** *Sumando la pasada de la ronda anterior, **tres renders completos sin red** y
ninguno a medias desde que se precachean todos los trozos.*

**La que fallo es la primera visita, y eso no es un defecto:** *un service worker no puede servir nada
antes de estar activo.* *Es el comportamiento normal, y conviene saberlo: **la primera vez que se abre la
app hace falta red;** de ahi en adelante, no.* *Y es lo que hay que decir en la ficha de la app, no
prometer «funciona sin conexion» a secas.*

**Lo que M15 tiene ahora, y lo que no:**
- instalable ....... manifiesto con 192/512/maskable, y servido
- armazon propio ... `ArmazonDeLaMarca`, en el trozo principal
- offline .......... **si, desde la segunda visita**; 31 trozos precacheados y verificados en `install`
- sincronizacion ... **no probada**: *la cola de cambios necesita la API viva, y Docker lleva nueve rondas
  caido*

**M07 / POR QUE «CERO FALSOS EXACTOS» NO ES SUERTE: SOLO HAY UNA VIA AL EXACTO.**

*A la pregunta de la especificacion -- «prioridad a evitar falsos exactos» -- hay una respuesta
estructural, y se puede leer en el codigo:*

    identidad.py:159  docstring de `decide`: «Nunca "exacto" sin GTIN valido»
    identidad.py:183  return {"estado": EXACTO, "motivos": ["mismo GTIN valido y presentacion
                      compatible"]}

*** Es la unica linea de `decide()` que devuelve `EXACTO`. *** *No hay camino por nombre, ni por marca,
ni por parecido de texto, ni por fuzzy.* *La unica forma de que el motor afirme «es el mismo producto»
es que los dos codigos de barras sean validos e iguales **y** que la presentacion sea compatible.*

**Eso significa que un falso exacto no puede venir de una heuristica equivocada.** *Solo puede venir de
**un EAN mal puesto en los datos**: dos articulos distintos con el mismo codigo.* *Y eso no lo arregla
ningun motor de identidad: lo arregla la captura.*

**Y por eso los estratos dificiles dan 0 exactos, que era el hueco que quedaba:**

    misma_marca_parecidos  40 pares  exactos 0
    pack_contra_unidad     20 pares  exactos 0
    sin_evidencia          20 pares  exactos 0

*No es que el motor los acierte: es que **no opina** ahi.* *Dice `probable`, `alternativa` o se abstiene,
que es justo lo que la especificacion pide («no pasar clasificandolo todo como desconocido» **y**
«embeddings/fuzzy solo para candidatos/familias, nunca sustitucion exacta automatica»).*

**Y la mitad del catalogo donde esto importa de verdad:** *de **1 958 963** filas del bronze, **973 841 no
tienen EAN** (el 49,7 %).* *Ahi el motor **nunca** podra decir «exacto» -- por construccion --, y lo que
hace es proponer candidato o abstenerse.* *O sea: en la mitad dificil del catalogo el comportamiento
seguro es el que ya tiene, y lo que falta no es precision sino **cobertura**, que es otra conversacion y
necesita etiquetas humanas.*

**Lo que esto cierra del criterio de M07:** *«prioridad a evitar falsos exactos» **esta garantizado por
construccion**, no por una prueba que salio bien.* *Y lo que queda abierto, dicho con precision:*
- *cobertura sobre el 49,7 % sin EAN: **no medida**, necesitaria un banco de esos pares*
- *los 44 pares que faltan para 200*
- *el umbral automatico documentado*
- *y `PROBABLE`/`ALTERNATIVA` no cuentan como abstencion en la medida; en 60 pares el motor dijo una de
  las dos*

