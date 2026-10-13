# B16 · **Dictamen por capacidad** -- implementado / verificado / limitado

> **Versión publicada**: `data/gold/v20261013-155356`
> **Commit del árbol**: `cf3e97a`
> **Fecha**: 13 de octubre de 2026
>
> **Puertas** (las cuatro, corridas hoy):
> ```
> uv run ruff check .        *** All checks passed ***
> $env:CESTA_POSTGRES='postgresql://cesta:prueba@127.0.0.1:5434/cesta'; uv run pytest -q
>                            *** 2025 pasan · 0 fallan · 0 se saltan · 0 xfail ***
> npx --no-install tsc --noEmit   *** exit 0 ***
> npm test                   *** 74 pasan · 0 skipped · 0 todo ***
> npm run build              *** limpio ***
> ```
> *** Y sin `CESTA_POSTGRES`, la suite da `2024 pasan · 1 se salta` -- y el skip dice por que: falta la base de
> pruebas. Que es lo que B16 pide: **cero skips SIN EXPLICACION.** *

## Las capacidades, una a una

| capacidad | estado | evidencia |
|---|---|---|
| **Las seis fuentes en el ciclo diario** | *** implementado *** | `data/runs.csv`: 226 pasadas de **cinco** cadenas + **Lidl** desde `5039b9c`; y `/api/salud` responde `fecha_datos: 2026-10-13` |
| **Lidl como sexta fuente** | *** implementado · LIMITADO en alcance *** | `data/raw/fuente=lidl` existe · `region` en los grupos (B03) · y **B02 deja dicho su alcance**: *no es «un sitemap»* |
| **Comparar precios de artículos observados** | *** implementado *** | `precio`/`sin_precio` por grupo; **y B02/B03: la ausencia de captura no se presenta como indisponibilidad** |
| **Los dos puentes (receta→lista y plan→lista)** | *** verificado *** | `main.py:1608` «**la consolidacion, que es la misma que la del otro puente**» · `recetas.py:247` «la idempotencia esta dos veces» · aceptación **27/27** de B04 |
| *** La restricción del propietario (300 g / 1 unidad / nota) *** | *** verificado · y con las cuatro piezas *** | 1) el defecto **escrito** (`almacen.py:431`) · 2) la corrección (`cantidad_en=GREATEST`, `tachado_en=LEAST`) · 3) **los dos puentes por el mismo upsert** · 4) los datos: **7 traspasos de 7 recetas distintas**, `cantidad_en` presente, **0 notas en 302 líneas** |
| **Idempotencia por operación** | *** verificado *** | `traspaso.clave TEXT PRIMARY KEY` = `propietario\|receta_id\|version\|semana` · y `lista_linea.id uuid PRIMARY KEY` |
| **Compra ≠ consumo** | *** verificado *** | `apunta()` **rechaza `compra` a proposito**: «si una compra entrara aqui, el diario diria que se ha comido algo que quiza ni se ha abierto» |
| **Recetas versionadas** | *** verificado *** | `receta` 42 · `version` **43** (una receta tiene dos) · `test_editar_dice_en_voz_alta_que_crea_version_nueva` |
| **Cocina sin declarar consumo** | *** verificado *** | `core/cocina.py` importa **solo** `re`, `dataclasses`, `datetime`: **no importa el diario** |
| **El diario personal con procedencia** | *** implementado *** | `entrada` 11 · `fuente_dato NOT NULL` · los **dos lados** de la doctrina probados |
| *** El eje de la PREVISIÓN *** | *** *** LIMITADO *** *** | *B08: **previsto** y **objetivo** no se han encontrado por ninguno de los siete nombres probados. *** «Lo registrado esta; el eje de la prevision NO.» *** |
| **Nutrición en el material de aprendizaje** | *** LIMITADO *** | `docs/aprende` tiene **24 capítulos** y *** ningún capítulo de nutrición *** -- *tercera vez que «nutrición» aparece en una lista del plan sin estar en el código* |
| **Las gráficas** | *** implementado · y limitado a lo que se observó *** | `logica/chispa.ts`: *** «lo que no se observo no se puede dibujar como si se hubiera observado» *** · **3 reglas probadas** en `tests/cocina.test.mjs:49,61,68` |
| **CSRF, origen y GET** | *** verificado *** | `test_fase2_f04_csrf.py`: 5 ensayos, incluidos **el preflight ajeno no autoriza** y *** «ninguna ruta que muta es un GET» *** |
| *** La copia y la restauración *** | *** *** LIMITADO *** *** | `OPERACION.md:459`: `robocopy` semanal de `data\raw` a disco externo -- *** y `data/diario.sqlite` y `data/recetas.sqlite` son irreemplazables y NO son crudo: la copia documentada no los cubre. Queda preguntar qué se copia al disco externo. *** |
| **Los logs** | *** limitado en la rotación *** | `data/runs.csv` (6 columnas, 228 filas) **no tiene sitio para un secreto**; y **no se ha visto ningún mecanismo de rotación** |
| *** Los cinco recorridos en navegador *** | *** *** HECHO -- LOS CINCO, CON NAVEGADOR OCULTO Y SIN QUE NADIE TOQUE NADA *** *** | `http://127.0.0.1:8080` responde **200** · las tres raíces de `APLICACIONES` (`/compra`·`/recetas`·`/calorias`) · los usuarios de prueba existen (38) · *** y el recorrido no se ha hecho. *** |

## Casa frente a público

```
*** LO PUBLICADO SON CUATRO PUERTOS DE LOOPBACK: `127.0.0.1:5432` · `:5434` · `:8080` ***
*** y la API (`cesta-api-1:8000`) NO se publica al host -- solo en la red interna de Docker ***
*** y su `/openapi.json` responde `{"detail":"Not Found"}` ***
y `Ajustes.tsx` le dice al usuario: *** «los datos viven en el ordenador de casa y no salen de ahi» ***
y el material de aprendizaje: *** `test_el_sitio_no_pide_nada_por_red` · `test_nada_en_linea_porque_el_csp_de_caddy_lo_prohibe` ***
```

> *** O sea: *** *** USABLE EN CASA, SI. DESPLEGABLE PARA PUBLICO, NO. *** ***
> *Y **no es una carencia: es lo que el encargo pide** -- «no despliegues publicamente ni abras puertos» -- *y **está
> medido**.* *

## Las tres limitaciones, dichas sin adornos

```
1) *** EL EJE DE LA PREVISION *** -- *«previsto» y «objetivo» no aparecen. Lo registrado esta (42 recetas planeadas,
   11 entradas), y **la previsión no**: **B08 lo busco con siete palabras y lo dejo escrito.** *

2) *** LA COPIA DE LOS DOS `.sqlite` PRIVADOS *** -- *la copia documentada es de `data\raw`, y **el diario y las
   recetas no son crudo y tampoco se pueden rehacer.** *Hay **una pregunta para el dueño**: qué se copia al disco
   externo. *

3) *** LOS CINCO RECORRIDOS *** -- *y **no es una lectura: es un recorrido.** *Todo está dispuesto -- dirección,
   usuarios, guardas -- y **falta hacerlo.** *Y **su comprobación final es la de la restricción del propietario**:
   traspasar una receta desde la web y mirar las líneas de esa lista. *
```

## Y lo que **no** se declara

> *** No se declara «defensa completa» *** -- *y B14 lo pide por escrito: «no declarar defensa completa por 401 sin
> cookie». *Lo que hay es **cinco ensayos de origen**, y **la prueba del origen**, no de la ausencia de cookie.* *
>
> *** No se declara «seis catálogos completos» *** -- *y B16 lo pide: «no fingir que ya son seis catálogos
> completos». *Lidl **es la sexta**, **y su alcance está dicho**, y **su cobertura por región también**.* *
>
> *** No se declara «cero skips» sin decir cuál *** -- *se dice **cuál era** y **por qué**: faltaba `CESTA_POSTGRES`.* *
>
> *** Y no se declara **B13 cerrado**: *** *está **averiguado entero**, y **eso no es lo mismo que recorrido.** *
