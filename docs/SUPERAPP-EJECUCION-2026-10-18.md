# Ejecución de la especificación maestra

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

