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

## Estado real el 2026-11-04 (medido, no supuesto)

| Dato | Valor |
|---|---|
| Productos en catálogo | **52.342** |
| Grupos comparables | **8.897** |
| Comparables por kg/l/m | **42.862** |
| Con código de barras | **25.649** |
| Con sello | **11.619** · con certificado **995** |
| Con Nutri-Score | **8.545** · con tabla nutricional **3.907** |
| Cobertura diaria | **solo Lidl**, 21 días (13 oct – 4 nov) |
| Alcampo | a medias (`data/alcampo_por_donde_iba.txt`) |
| Carrefour | falló el 18; el encargo pide investigarlo **sin duplicar una ingesta activa** |

Traducido: hay **catálogo y datos de producto**, pero la **cobertura de precios por cadena es de una sola cadena**. Un comparador con una cadena no compara.

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
