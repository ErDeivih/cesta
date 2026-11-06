# Ficha del agente — Cesta

**Id en el panel**: `cesta`
**Ruta**: `F:\Proyectos\cesta`
**Rama de trabajo**: `master`
**Repositorio**: https://github.com/ErDeivih/cesta (privado, respaldado el 2026-11-04)
**Compose**: `plataforma/docker-compose.yml`, proyecto `cesta`

## Misión

Una **superapp para el consumidor**: compra comparada entre supermercados, recetas y calorías, en una sola aplicación web responsive y PWA móvil.

No es un comparador de precios suelto. Es: *qué compro, dónde me sale mejor, qué cocino con ello y cuántas calorías tiene*.

## Autoridad documental: leerla antes de nada

El proyecto **ya tiene especificación maestra y encargo vigente**. Esta ficha no la sustituye.

| Documento | Qué manda |
|---|---|
| `docs/SUPERAPP-ESPECIFICACION-MAESTRA-2026-10-18.md` | la especificación vinculante, paquetes **M00–M22** |
| `docs/SUPERAPP-GOAL-ACTUAL.md` | el encargo operativo vigente |
| `docs/SUPERAPP-EJECUCION-2026-10-18.md` | el estado corto de ejecución |
| `docs/CIFRAS.md` | las cifras de hoy; lo reescribe `projects/cesta/cifras.py` en cada pasada |
| `docs/COLECTORES.md` · `docs/CADENAS.md` | colectores y cadenas |
| `docs/BACKLOG.md` | el backlog del proyecto |

**Regla**: los documentos guardan sus cifras con la fecha en que se midieron. **No se actualizan a mano, se registran**; las de hoy viven solo en `CIFRAS.md`.

## Estado real el 2026-11-04, 14:30 (medido, no supuesto)

> **Es una foto fechada, no el estado de ahora.** Las cifras de esta tabla son de las 14:30, y su
> histórico (**2.527.902 filas**) es **anterior** a que se añadieran las 23.405 filas recuperadas de
> Alcampo ese mismo día: la foto de ahora (52.982 productos, 2.551.307 filas, 8.875 grupos) la
> reescribe `projects/cesta/cifras.py` en `docs/CIFRAS.md` al final de cada pasada.

> **Corrección del 4/11/2026.** La versión anterior de esta tabla decía «cobertura diaria:
> **solo Lidl**, 21 días». **Era falso**, y el motivo importa: salía de leer
> `cobertura_declarada` en el manifiesto, donde solo escribe Lidl. La cobertura diaria se
> mide con `uv run python -m projects.cesta.cobertura_diaria` y con `data/gold/precio_diario.parquet`.

| Dato | Valor |
|---|---|
| Productos en catálogo | **52.342** |
| Grupos comparables | **8.897** |
| **Grupos con precio en 2+ cadenas** | **8.864** (22,9 % de 38.682 comparables) |
| Comparables por kg/l/m | **42.862** |
| Con código de barras | **25.649** |
| Con sello | **11.619** · con certificado **995** |
| Con Nutri-Score | **8.545** · con tabla nutricional **3.907** |
| Histórico | **2.527.902 filas**, 59 días |

Cobertura diaria **por cadena** (días con precio en gold desde el 01/10, y filas de hoy):

| Cadena | Días | Filas hoy | Cobertura hoy |
|---|---:|---:|---|
| Mercadona | 32 | 4.226 | 98,9 % de su referencia |
| Aldi | 32 | 2.499 | 91,8 % |
| Carrefour | 31 | 16.782 | 99,9 % (1 error de catálogo crónico) |
| DIA | 29 | 5.698 | 97,6 % |
| Alcampo | 21 | 23.405 | recuperado hoy desde el crudo; su vara es un día atípico |
| Lidl | 21 | 91 | **ofertas semanales parciales**, no catálogo |

Traducido: **la comparación existe y es de cinco cadenas**, no de una. Lo que se cae es una
cadena un día suelto — y hasta hoy el sistema lo contaba mal. El trabajo vivo está en
`BACKLOG.md`; el estado corto, en `ESTADO-AGENTE.md`.

## Cobertura declarada, medida (2026-11-04, 17:39)

Desde hoy cada cadena de catálogo **declara su día con lo medido sobre su bronce**:
`data/cobertura/<fuente>-<fecha>.json` lleva filas, referencia y su fecha, %, huecos, veredicto
y **la novedad del día** (ids nuevos, precios cambiados, desaparecidos frente a la captura
anterior). Antes ese directorio solo lo escribía Lidl, y de ahí salía la frase «solo Lidl,
21 días».

- Efecto: `data/gold/manifiesto.json` pasa de **21 a 26** entradas declaradas y
  `GET /api/estado` enseña `cobertura` para **las seis cadenas**; la pantalla viva
  (`Ajustes → Frescura y cobertura de los precios`) lo pinta por cadena.
- La demostración con números (30 días, novedad por día, frescura de la partición):
  `docs/COBERTURA-DIARIA-2026-11-04.md`; el instrumento es
  `scripts/auditar_cobertura_diaria.py`.
- **El reloj que lo produce ya está arreglado (4/11, 19:18).** La tarea del Programador `Cesta
  diaria` apuntaba a la ruta anterior al movimiento (`F:\aprendizaje\scrap`, inexistente);
  David la re-registró como administrador y se verificó: acción `F:\Proyectos\cesta\ejecutar.bat`,
  3 disparadores (06:00, al arrancar, al iniciar sesión), disparo manual con `LastTaskResult 0` y
  próxima ejecución **5/11 06:00**. Queda documentado en `docs/COBERTURA-DIARIA-2026-11-04.md` §11.

## Panel: `metricas-cesta.json` (2026-11-04)

En la raíz del proyecto, reescrito por `projects/cesta/metricas.py` al cerrar cada pasada:
por cadena si trae datos hoy y cuántos días lleva, la última ejecución en hora local, los
comparables con precio del día (**39.115**), cuántos tienen precio en **2+ cadenas**
(**8.829**, la cifra que dice si de verdad se puede comparar) y los días de historial (59).
Las definiciones exactas, en `DECISIONES.md` §6. Matiz medido: 8.829 es «precio en 2+ cadenas
con importe»; **comparables de verdad** (unidad dominante + comparación fiable) son **8.066
(20,1 %)** — la app dirá siempre cuál enseña.

## App de consumo (2026-11-04, tarde)

David cambió el foco a la app para el consumidor; el alcance manda en `ALCANCE-APP.md`. Antes
de escribir la primera pantalla hay tres piezas, ya hechas y pendientes de su aprobación:

- `INVESTIGACION-APP.md`: qué hacen Soysuper, Idealo, CamelCamelCamel, Lidl Plus, Mercadona y
  Yuka (con enlace y fecha), qué copiamos con criterio y qué no.
- `docs/DATOS-APP-2026-11-04.md`: viabilidad medida de cada función. Hacer: comparar cesta,
  €/kg, historial (59 días, no «90»), alternativas y avisos. Limitadas: etiquetado (sin
  aditivos), calorías (23 %) y despensa. No: recetas con coste (0/242 recetas costeables).
- `designs/`: sistema de diseño «Cesta App» (tokens claro/oscuro, 92 parejas AA medidas) y
  canvas con artboards móviles de Portada y Producto sobre datos reales, para que David los
  abra y apruebe. `plataforma/web` **no se ha tocado** todavía.

## Cómo trabajas

Lee y sigue `F:\EspacioCodigo\_flujo-dsh\PROTOCOLO-AUTONOMIA.md`.

- **Nivel 1**: decide solo (refactor, pruebas, docs, accesibilidad).
- **Nivel 2**: decide solo y lo anotas en `DECISIONES.md`.
- **Nivel 3**: paras y preguntas (alcance, datos, credenciales, dinero, otro proyecto, ramas).
- **Una tarea bloqueada no para la sesión**: la marcas y sigues con la siguiente.

## Backlog y primera tarea

El backlog vive en `docs/BACKLOG.md` y se complementa con `BACKLOG.md` en la raíz si hace falta. Nunca menos de 5 tareas listas.

**Primera tarea**: poner al día el estado —qué está verde de verdad y qué solo lo dice un documento— y atacar la cobertura de una segunda cadena. Sin dos cadenas no hay comparación, y sin comparación no hay producto.

## Skills y plugins instalados: úsalos

Están instalados en DSH y son obligatorios cuando tocan:

- **`claude-design-system`** — sistema de diseño (tokens, tipografía, componentes). **Antes** de tocar la interfaz de la plataforma.
- **`claude-design`** — artboards para revisar pantallas antes de implementarlas.
- **`claude-dashboard`** — cuadros de mando con datos: ideal para las gráficas de cesta, evolución de precios y comparativas.
- **`claude-slides`** — presentaciones, si hay que enseñar el producto.
- **`data_profile` · `data_clean` · `data_verify`** (`dsh-data-quality`) — **perfilado, limpieza y verificación de los datos de scraping**. Úsalos antes de dar una ingesta por buena: mide nulos, duplicados, tipos mixtos y coherencia.

## El catálogo de repositorios: consúltalo

En `F:\Inforepositorios` hay **468 fichas** de repositorios y **1.424 repositorios dentro de recopilaciones**, con licencia, límite y recomendación. Periódicamente:

```powershell
& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto scraping
& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto "precios supermercado"
& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto openfoodfacts
```

Si algo sirve, se propone con su ficha, su licencia y su límite. **No se adopta por intuición.**

## Al terminar cada sesión

Deja `ESTADO-AGENTE.md` actualizado con este formato exacto:

```
titulo: Cesta — superapp de compra, recetas y calorias
estado: en-curso
tarea: lo que estabas haciendo
nivel: 1 | 2 | 3
siguiente: lo proximo
bloqueado: la pregunta de nivel 3, si la hay
fecha: AAAA-MM-DD
```

Y recuerda: **sin commit y sin push, no está terminado.**


## Consultar el catálogo de repositorios (no busques a mano)

Antes de buscar una librería, una herramienta o una referencia, pregunta al catálogo personal de David: más de 500 fichas documentales y ~1.400 repositorios dentro de recopilaciones, con licencia real, límite y recomendación.

```powershell
python F:\Inforepositorios\consultar.py "<lo que necesitas>" -n 5 --json
```

Puedes hacer **varias consultas seguidas** en la misma tarea, una por necesidad (OCR, scraping, PDF, agentes…); cada consulta es independiente y tarda 2-4 s. Devuelve los mejores candidatos con su licencia y la ruta de su ficha; abre solo esas fichas y mira la sección 9 (cuándo no elegirlo) y la 6 (licencia). Si solo quieres repositorios del catálogo, añade `--tipo ficha`. Es evidencia documental: nada se ha clonado, instalado ni ejecutado, así que da **candidatos que merecen revisión, no la garantía de que algo funcione**. Guía: `F:\Inforepositorios\RAG.md`. Para una palabra exacta: `& F:\Inforepositorios\scripts\Buscar-Todo.ps1 -Texto <término>`.
