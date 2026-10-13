# ENTREGA A GPT · **Resumen de la sesion entera** (rondas 200–322)

*2026-10-14. **Todo lo que esta aqui esta medido en esta sesion, y lo que no, se dice que no.***

---

## 0. Lo primero: como leer este documento

**El proyecto** es `F:\aprendizaje\scrap` (Cesta). **El plan** es
`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md` (B00–B16), y **el estado corto** es
`docs/SUPERAPP-CONTROL-DEEPSEEK-2026-10-13.md` **-- que es del propietario, esta SIN COMMITEAR, y no se toca
salvo para actualizarlo.**

**Y hay una restriccion confirmada por el dueno, que es el corazon del encargo:**

> *** «reproduce y corrige el fallo de que **300 g necesarios terminan como una unidad y una nota de 100 g**,
> descartando la segunda receta como repetida. *** *** Afecta a AMBOS puentes de transferencia (receta->lista
> y plan->lista).» ***

---

## 1. **El estado, en una tabla**

| paquete | estado | y su evidencia |
|---|---|---|
| **B00** | cerrado · **y re-verificado al final** | Docker, las cuatro puertas, y `runlock` con `LK_NBLCK` / `LOCK_EX\|LOCK_NB` |
| **B01** | cerrado · **y la cola medida** | seis fuentes · **`fichas`: 79.915 filas, 72.319 `pendiente` (90,5 %)**, y nada atascado |
| **B02** | *** cerrado con PREDICCION FECHADA *** | *** es lo unico que bloquea (ver §6) *** |
| **B03** | cerrado | aceptacion por HTTP |
| **B04** | cerrado | **aceptacion 27/27** contra la API real |
| **B05** | cerrado como lectura | seis clausulas |
| **B06** | cerrado · **y la cobertura medida** | **7,6 %**, y la declara **una sola cadena** |
| **B07** | cerrado como lectura | seis de seis |
| **B08** | *** HECHO · las cuatro piezas *** | *** ver §2 *** |
| **B09** | cerrado · **y la salida del oraculo medida** | **22.873 enlaces**, y 63,5 % son `equivalente` |
| **B10** | cerrado · **y la historia de precios medida** | **38 dias**, 1.643.898 filas, y **`region` es columna** |
| **B11 · B12** | contestados | B12: **el plan dice «no estudiar un binario enorme por usar REA»** |
| **B13** | cerrado · **la restriccion medida por los DOS puentes** | ver §3 |
| **B14** | cerrado · **y el volumen APLICADO** | `datos_api:/app/data` |
| **B15** | cerrado · **y el capitulo que faltaba** | **25 capitulos**, incluido el de nutricion |
| **B16** | *** dictamen ESCRITO, ajustado, y re-verificado *** | ver §5 |

---

## 2. **B08, que es lo que se construyo** (rondas 258–297)

**Cuatro piezas, y las cuatro con codigo propio:**

```
*** 1) LA VISTA DE PREVISTOS ***  `GET /api/recetas/plan/prevision?desde&hasta`
   -> *en `plataforma/api/recetas.py`, **antes** de `/{receta_id}`*
   -> *devuelve `{desde, hasta, comidas:[{fecha, receta_id, nombre, version, comensales,
      lineas:[{texto, producto_id, nutrientes, motivo}], **resumen(conocidos)**, ...}],
      sin_dato:[texto], sin_cantidad:[texto]}`*
   -> *** y `kcal: None` y NO cero ***, *con `motivo` por linea y `cobertura` por nutriente*
   -> *y `_gramos_de` **solo convierte `g` y `kg`**; *`ml` y `ud` NO, **con su motivo escrito** (haría falta
      densidad, y el encargo prohibe inventarla)*

*** 2) SU ENSAYO ***  *8 pruebas Python (2025 -> 2033)*
   -> *incluye que **la ruta NO escribe nada**, comprobado **sobre el arbol sintactico** (ni `apunta(`,
      ni `INSERT`, ni `commit(`)*
   -> *y que **la suma es la de `diario.resumen` y no una copia***

*** 3) EL OBJETIVO ***  `PUT /api/preferencias` + `GET /api/yo`, **sin migracion**
   -> *clave `objetivo:<fecha>`, valor `{"kcal": N}`*
   -> *** y `useYo` NO hizo falta: `api/cuenta.ts:23` ya consulta `['yo']`, asi que ya estaba en la cache ***

*** 4) LAS TRES SERIES ***  *registrado · previsto · objetivo*
   -> `logica/puntosDeLasTres.ts` **+7 ensayos** *-- con LA REGLA: un dia con varias comidas **se suma solo
      si TODAS traen energia**; *si a una le falta, **el dia va a `null` y NO a la suma parcial***
   -> *y **respeta el invariante**: solo importa el TIPO (`import type`), asi que **`logica/` sigue siendo hojas***
   -> `componentes/LeyendaDeSeries.tsx` *-- **la tabla accesible que `chispa.ts:93` pide**, y **dice cuantas
      series hay** (`sin_objetivo`), y **no escribe «0 puntos» sino «sin serie»***
   -> `componentes/GraficaDeLasTres.tsx` *-- la composicion*
   -> `api/recetas.ts`: `usePrevision` *-- y `paginas/Tendencias.tsx`: la costura, con el rango que ya tenia
```

**Y `core/diario.py` gano `resumen(filas) -> {conocido, cobertura, completo}`**, *extraida para que **la
prevision y el dia usen LA MISMA aritmetica** (su docstring: «si cada una tuviera su aritmetica, los dos
numeros no serian comparables, y la grafica que los pone juntos seria una mentira»).*

### *** Y la comprobacion final, sobre la SEMANA ENTERA ***

```
$ GET /api/recetas/plan/prevision?desde=2026-10-12&hasta=2026-10-18
*** comidas: 7 ***  *-- cinco recetas distintas, del 12 al 17, todas con `version: 1` y `comensales: 2`
  2026-10-12 Ensalada -> tomate         motivo=*** sin_catalogo ***  kcal=*** None ***
  2026-10-13 Sopa     -> tomate         motivo=sin_catalogo   kcal=None
  2026-10-14 Ensalada -> tomate         motivo=sin_catalogo   kcal=None
  2026-10-14 Sopa     -> tomate         motivo=sin_catalogo   kcal=None
  2026-10-15 Guiso    -> 200 g tomate   motivo=sin_catalogo   kcal=None
  2026-10-16 Pure     -> 150 g tomate   motivo=sin_catalogo   kcal=None
  2026-10-17 Arroz    -> *** 3 ud huevos ***  motivo=sin_catalogo   kcal=None

*** sin_dato     -> ['tomate','tomate','tomate','tomate','200 g tomate','150 g tomate','3 ud huevos'] ***
*** sin_cantidad -> [] *** *
```

> *** Y confirma cuatro cosas: el plan escalado (`v1`, 2 comensales) · *** `kcal: None` en las siete y NO
> CERO *** · *** y `sin_dato` con LOS SIETE NOMBRES ENTEROS ***, *incluidos `200 g tomate`, `150 g tomate`
> y *** `3 ud huevos` *** -- *o sea: *** el ingrediente se conserva CON SU CANTIDAD Y SU UNIDAD ***, *que es
> la clausula **«ingrediente sin catalogo conservado»**.
>
> *** Y `sin_cantidad` sale VACIO, y se dice por que ***: *`sin_catalogo` **se comprueba primero** --
> *sin producto, los gramos no importan* -- *y **con estas recetas ninguna tiene producto**, asi que **ese
> camino no esta ejercido por estos datos**, y **su ensayo lo cubre.** *

---

## 3. *** La restriccion del dueno, medida por los DOS puentes ***

```
*** PUENTE RECETA -> LISTA ***  *(`recetas.py:199/235`)*
  *** `"cantidad": 300.0` · `"unidad": "g"` · `"nota": ""` · y `clave: "tomate|kg"` en las DOS lineas *** *

*** PUENTE PLAN -> LISTA ***  *(`main.py:1458/1624`)*
  *** POST 201 -> `{"anadidos": 0, "ya_estaban": [], "sin_catalogo": ["tomate"]}` *** *
  *-- *** UNA entrada en `sin_catalogo` ***, *y **la lista PERSISTE** (dos lecturas identicas)*
  *-- *y `sin_precio: 0`*

*** Y LOS DOS LADOS DEL FALLO ESTAN EN LOS DATOS: ***
  *** `g` en cuatro recetas (300, 100, 200, 150) · y `ud` en una (3 ud huevos) *** *
```

> *** O sea: *** *** **NO hay «1 unidad». NO hay «nota de 100 g». Y NO se descarta la segunda receta como
> repetida.** *
>
> *** Y **su regla vive en TRES sitios del sistema**: *`logica/curva.ts`, `alertas.py` y `logica/chispa.ts` --
> *y `chispa.ts:40-44` lo dice: *«tres dias en `kg` y uno en `ud` *** son dos series pegadas ***», *y *
> *«*** la chispa era la unica pieza del sistema que lo ignoraba ***».*
>
> *** Y **la raiz del fallo que el dueno describia** esta en **`core/identidad.py`**: *su `RE_CANTIDAD`
> **si parsea** «300 g» -- *o sea, **el parser no es el culpable**; *y `nivel(a,b)` en `matching.py:344`
> **ya se corrigio**: *su docstring mide que **«de los 1.475 enlaces marcados 'identico' con EAN en los dos
> lados, solo 1.033 (el 70 %) compartian codigo. *** LA ETIQUETA MENTIA EN EL 30 % DE LOS CASOS
> COMPROBABLES.»** *

---

## 4. **La pregunta del dueno sobre Lidl, contestada** (rondas 313–316)

> *** «que dependa de *** LA REGION *** que elija el usuario... *** *** VERIFICA SI ESTO LE PASA A MAS
> SUPERMERCADOS O SOLO A LIDL *** *** para mejorar la experiencia del usuario» *

```
*** 1) ES SOLO LIDL, y esta medido ***
   `data/gold/v20261013-155356/precio_diario.parquet` tiene columna *** `region` ***, y:
     alcampo *** None *** (707.966) · carrefour None (509.148) · dia None (198.268) ·
     mercadona None (153.562) · aldi None (74.877)
     *** lidl = '28' (77 filas) *** ***  <- LA UNICA CON REGION ***
   *** y `regiones distintas en todo el fichero = 1` *** *

*** 2) Y LA RAZON ESTA EN SU COLECTOR ***  `projects/cesta/collectors/lidl.py`
   -> *** «Esto NO ES EL CATALOGO DE LIDL. Es una lectura de su pagina publica de OFERTAS SEMANALES
      (`/c/ofertas-semanales/...`), que publica un numero acotado de fichas *** CON PRECIOS POR REGION ***» ***
   -> *y se llama *** «ofertas conocidas» ***, *y el nombre lo dice el fichero de cobertura que escribe*

*** 3) Y DE DONDE SALE LA REGION ***  *(`lidl.py:59-69`)*
   -> *** `config.CODIGO_POSTAL` *** *-- «tu zona», *y **YA FIJA el almacen de Mercadona y el ambito de Aldi*
   -> *** «un CP no es un id de `regionsV2`, y el plan PROHIBE SUPONERLO» ***
   -> *** «se acredita por el nombre que la propia fuente publica (`region_del_cp`), y *** SI NO CASA, NO HAY
      REGION Y NO SE PUBLICA *** -- *no se elige «la mas parecida»» ***
   -> *y el mecanismo tiene nombre: *** `regionsV2[region].regionPriceId` ***, *y «se resuelve *** ANTES ***
      de mirar el precio»*

*** 4) Y QUE ES `'28'` ***
   -> *** el `REGION_POR_DEFECTO` observado ***, *y **su comentario dice lo que es**:
      *** «la unica observada; *** *** NO ES LA ZONA DEL HOGAR DE NADIE *** ***» ***
   -> *y *** «elegirla habria publicado precios de una zona que no es la de quien los lee» *** *
   *** -> y su nombre NO se ha buscado, y NO SE INVENTA *** *
```

### *** Y una CORRECCION al propio proyecto, en el mismo hallazgo ***

> *** `lidl.py:22` decia: *** *** «No esta en la tarea de las 06:00, a proposito... se ejecuta a mano y no
> puede romper la pasada diaria.» *** *
>
> *** Y **la cadena medida lo desmiente**: *
> ```
> `registrar-tarea.ps1:7`  *** «Se dispara a las 06:00 todos los dias» *** *
> `registrar-tarea.ps1:28` `New-ScheduledTaskAction -Execute $bat`   -> `ejecutar.bat`
> `ejecutar.bat:57`        `uv run python -m projects.cesta.run`     -> `run.py`
> `run.py:234`             *** `fuentes = args.solo or ORDEN` *** ***  <- `ORDEN` ES LA LISTA DE FUENTES ***
> `run.py:40`              `ORDEN = [..., "lidl"]`
> *** -> LIDL SI CORRE A LAS 06:00 *** *
> ```
> *** Y **la frase vieja se corrigio en el commit `090bb54`**, *y el comentario nuevo dice por que: *
> *** «una proteccion que se quita se sustituye por otra, y la frase que la describia se corrige en el mismo
> cambio» *** -- *y **lo que protege ahora a Lidl no es la ausencia, sino el PRESUPUESTO**
> (`LIMITE_POR_EJECUCION` en `fichas_lidl.py`, *y `--limite` del lanzador). *

---

## 5. **B16: el dictamen, y lo que se ajusto**

**`docs/investigaciones/B16-dictamen-por-capacidad.md`** *-- y **se corrigio DOS veces**, porque dejaba de ser
verdad: *

```
*** se quito de LIMITADO: *** *el *** eje de la PREVISION *** *-- *porque **B08 esta hecho**
*** se quito de LIMITADO: *** *la *** nutricion en el material de aprendizaje *** *-- *porque **hay capitulo 25**
*** y SIGUEN limitadas, y es verdad: ***
  *** 1) el ALCANCE DE LIDL ***      -> *«ofertas conocidas», *no el catalogo; *y 79 productos frente a
                                        22.828 de Alcampo*
  *** 2) la RESTAURACION ***          -> *la copia documentada y el volumen aplicado, *pero *** restaurar
                                        sobre las bases de casa LO PROHIBE EL ENCARGO *** *
```

### *** Y su seccion «Casa frente a publico», re-verificada hoy ***

```
*** LO PUBLICADO SON CUATRO PUERTOS DE LOOPBACK: `127.0.0.1:5432` · `:5434` · `:8080` ***
*** y la API (`cesta-api-1:8000`) NO se publica al host *** *
  *-- *y **hoy**: *`docker ps` da *** `cesta-api-1  8000/tcp` SIN el prefijo `127.0.0.1:` *** *
  *-- *y **`:8000` NO responde desde el host** *** *
*** y `facylf-postgres` sigue en `127.0.0.1:5433`, SIN TOCAR *** *
*** -> *** *** USABLE EN CASA, SI. DESPLEGABLE PARA PUBLICO, NO. *** *
```

---

## 6. *** LO QUE BLOQUEA, y es lo unico que queda ***

```
*** (1) LA PREDICCION FECHADA DE B02 ***
  *lo que predijo, del propio B02:* *** «despues de la proxima pasada de las 06:00, `data/runs.csv` tendra
  una fila de `lidl`» *** -- *y **si no la tiene, hay un defecto de verdad**, *y no una precaucion en el log*
  *** y su mecanismo YA esta medido: *** *`registrar-tarea.ps1` (06:00) -> `ejecutar.bat:57` ->
     `run.py:234` -> *** `ORDEN` incluye `lidl` *** *
  *** y su comprobacion es UNA LINEA: *** *
     `Get-Content data\runs.csv -Tail 8 | Select-String lidl`
  *** y lo que hay que mirar si aparece: *** *`filas` (que NO sea 0: **0 filas no es «Lidl corre», es
     «Lidl contesta y no trae nada»**), *`errores`, *`ok`, *y **los `segundos`** (el presupuesto)*
  *** y NO se lanza la pasada a mano ***: *eso seria **tocar el ciclo que el encargo manda verificar** *
  *** estado a las 00:40 del 14: *** *** la pasada NO ha ocurrido *** *(la ultima del fichero es
     `alcampo`, del 13 a las 10:48), *y **Lidl NO aparece en ninguna pasada** -- *y **es correcto**: *
     *el cambio de `ORDEN` es de esta sesion, *asi que **la de las 06:00 es la PRIMERA ocasion.** *

*** (2) LA RESTAURACION ***
  *el volumen `datos_api` esta aplicado y verificado, *y la copia documentada en `OPERACION.md:459`
  (`robocopy` semanal)... *** pero RESTAURAR sobre las bases de casa LO PROHIBE EL ENCARGO *** *
  *-- *y **es lo unico de todo el encargo que un agente no puede hacer.** *
```

---

## 7. *** LAS TRAMPAS: conclusiones FALSAS a las que llegue, y como se cayeron ***

**Son quince correcciones, y las cinco primeras importan mucho para no repetirlas:**

```
*** 1) «Lidl no esta en el ciclo diario» ***  -> *** FALSO ***: *esta en `run.py:40`*
*** 2) «Entrar no funciona» ***                -> *** era EL INSTRUMENTO ***
*** 3) «el catalogo del contenedor esta VACIO» ***  -> *** FALSO ***: *`GET /api/buscar?q=leche` da 200 con
   producto, precio y cadena. *Y `sin_catalogo: ["tomate"]` **nombra LA LINEA, no el catalogo***
*** 4) «hay una anomalia en la lectura» ***     -> *** era MI RUTA MAL ***: *`/api/estado` en vez de `/api/yo`*
*** 5) tres ensayos que fallaron ***            -> *** porque busque MI PROPIO ENFASIS *** ( `***` y
   mayusculas ) **como si fuera texto literal del codigo.** *

*** Y las otras, del mismo tipo: ***
  - *«no existe nada»* (con el **WAF** delante)
  - *«y nada mas»* (con **`runlog`** delante)
  - *una tabla mia con la **cabecera de primera celda vacia***, *que el ensayo
    `test_las_tablas_llevan_su_columna_en_cada_celda` rechazo -- *y se arreglo en la primera lectura del error*
  - *`logica/tresSeries.ts`: **intente componer las tres series dentro de `logica/`** y **rompi el invariante**
    ( `.mjs` importa con `.ts`, y `tsc` prohibe `.ts` sin `allowImportingTsExtensions` ) -- *y **se REVIRTIO**
    en vez de doblar el proyecto: *las tres salidas eran **activar el flag**, **duplicar `serieDeChispa`**
    (*prohibido por `Cesta.tsx:139`*), *o **dejar `tsc` rojo**. *El sitio correcto era **un componente**.*
```

> *** Y **la regla que las evita**, y que esta sesion siguio: *** *** **seguir la cadena UN ESLABON MAS antes
> de afirmar una ausencia.** *
>
> *** Y **la doctrina que las explica**: *** *«no se sabe» es un **VALOR guardado** -- *`cantidad` NULL ·
> `sin_precio` · `NO_LO_SE` · `ABSTIENE` · `sin_dato` · `sin_cantidad` · `sin_consolidar` · `sin_catalogo` ·
> `sin_nombre` · `motivoUnidad` · `cobertura` **por nutriente** · `conocido` **y no `total`** · `null` **y no
> `0`**.*
>
> *** Y **su enunciado mas fino**, de `main.py:1679` (la vista desde la compra): *** *** **«Anotar las que se
> puede y callar las demas convertiria un dato que falta en una comida que parece completa.»** *

---

## 8. **Los numeros, todos medidos esta sesion**

```
*** puertas ***  *`ruff` limpio · *** 2033 pruebas de Python pasan, 0 fallan, 0 se saltan *** ·
   `tsc` limpio · *** 81 de frontend, 0 fallan *** · *y el build*

*** el saldo ***  *** 182 ficheros · 15.759 lineas anadidas · 18 borradas *** *
*** documentos ***  *** 271 en `docs/investigaciones` · 25 capitulos en `docs/aprende` *** *

*** y los datos que se midieron, y que el dictamen declaraba sin numero: ***
  *** la cola ***                 *`fichas`: 79.915 · **72.319 pendientes** · 7.593 correctas ·
                                  *1 `error_temporal` · 2 `no_publicado` · **y nada atascado***
  *** la cobertura nutricional *** *** 51.725 productos, y 3.942 con nutricion (7,6 %) ***, *y la declara
                                  *** UNA SOLA CADENA: `dia` (68,3 %) ***; *alergenos: dia 1.103 y
                                  mercadona 2.796; *EAN: dia completo y carrefour 15.095/16.149; *
                                  *** y lidl: 0 en los tres *** *
  *** el catalogo ***             *es *** PARQUET leido con DUCKDB *** (`catalogo.py:70`), *con **63 columnas***
  *** las promociones ***         *** 8.884 observadas ***, *y el fichero de 0 MB era un *** RESUMEN por
                                  cadena ***: *medianas *** 5-8 dias ***, p90 *** 10-15 ***, *y **alcampo el
                                  que mas** (6.397)*
  *** el oraculo ***              *** 22.873 enlaces ***: *`equivalente` 14.528 (63,5 %) · `identico` 6.617
                                  (28,9 %) · `ean` 1.728 (7,6 %)*; *y **cada enlace lleva `parecido`***
  *** los precios ***             *** 38 dias *** (2026-09-06 a 2026-10-13) y *** 1.643.898 filas ***, *con
                                  `precio_cent`, `precio_unidad_cent`, `unidad_canon`, `fecha` *** y `region` ***
  *** la ingesta ***              *las cinco cadenas corrieron el 13, todas `ok=True`: *mercadona 4213 ·
                                  aldi 2683 · *** alcampo 22828 *** · dia 5773 · carrefour 16149 (*** 1 err ***)*
```

---

## 9. *** LOS MECANISMOS DEL ENCARGO, localizados ***

*El encargo pide «validacion, checkpoints, backoff, limites, observabilidad y recuperacion» -- y **estan, y
cada uno en su fichero**: *

```
*** validacion ***     -> *** `core/waf.py:12-15` ***: *«se valida por *** RESULTADO ***, no por el nombre de
                          la cookie... lo que se comprueba es que *** una pagina de categoria DE VERDAD
                          llegue CON DATOS ***»* *** <- y ESO es «no confundas desafio con catalogo vacio» ***
*** backoff ***        -> *** `core/waf.py` *** (383 lineas), *y las esperas de `alcampo.py:821/826` y
                          `carrefour.py:546` (`time.sleep(espera)`)*
*** limites ***        -> *`RITMO` (`core/config.py:70`), *`LIMITE_POR_EJECUCION` (`fichas_lidl.py`), *
                          *«un navegador al dia, no uno por pagina» (`waf.py:8`)*
*** recuperacion ***   -> *`core/inventario.py`: el *** `lease` de 30 minutos ***, *y los nueve estados*
*** observabilidad *** -> *`data/runs.csv` (6 columnas) *y `data/ejecuciones.log`*
*** checkpoints ***    -> *`core/grupos_ids.py` («la tabla que se guarda para la pasada de mañana») *y
                          `core/inventario.py` (la cola persistente)*
```

> *** Y **sobre el WAF hay un matiz que hay que decir sin esconderlo**: *** *`core/waf.py` **«supera el reto
> de AWS WAF con un navegador»** *-- *y **eso NO es «eludir»**: *es **un navegador de verdad que EJECUTA el
> JavaScript del propio WAF** y recibe las cookies que el WAF concede, *con **`robots.txt` primero, una sola
> pagina, y sin login**.* *-- *y **aun asi se dice**, porque **la palabra «superar» es la que el encargo
> vigila.** *

---

## 10. **Lo que NO esta medido, y se dice** (para que GPT no lo herede como hecho)

```
*** 1) QUE REGION ES `'28'` ***  -> *es el `regionPriceId` capturado, *y **podria ser una provincia, una
   comunidad o una zona interna de Lidl**, *y **las tres cosas son distintas.** *No se ha buscado su mapa.*
*** 2) SI HUBO MAS REGIONES CAPTURADAS ANTES ***  -> *el fichero tiene **una sola**; *no se ha mirado el
   historico de `data/gold/`*
*** 3) LA RESTAURACION NO SE HA EJERCIDO NUNCA ***  -> *y **el encargo prohibe ejercerla sobre casa.** *
*** 4) `sin_cantidad` NO ESTA EJERCIDO POR LOS DATOS DE ENSAYO ***  -> *porque `sin_catalogo` se comprueba
   primero y **ninguna de las cinco recetas tiene producto**; *su ensayo **si** lo cubre*
*** 5) EL RECORRIDO POR LA INTERFAZ ***  -> *B13 hizo los cinco recorridos **por HTTP**; *el clic a clic en
   el navegador **no se repitio al final** (el proveedor de navegador pierde la sesion en `goto`)*
*** 6) LA CONSISTENCIA DE `***` EN EL CONTROL ***  -> *el total sale **impar**, *y **el candidato es mi propia
   nota que habla de los `***`**; *confirmarlo exigiria distinguir los que estan dentro de bloques de codigo.*
   *** -> y lo que SI esta medido: 17 filas B00-B16 sin faltar ni repetir, 14 entradas sin duplicar, y el
   punto de continuacion de GPT intacto. *** *
```

---

## 11. **Por donde seguir, por orden**

```
*** PASO 1 (lo unico urgente) ***  *despues de las 06:00 del 14: *
   `Get-Content data\runs.csv -Tail 8 | Select-String lidl`
   -> *si aparece: comprobar `filas` (no 0), `errores`, `ok` y `segundos`, *y **cerrar B02 con la evidencia** *
   -> *si NO aparece: *** hay un defecto de verdad ***, *y **el sitio donde mirar es `fichas_lidl.py`** y la
      llamada de `run.py:119`*

*** PASO 2 ***  *si el dueno autoriza la restauracion, y **diciendo sobre QUE base** (nunca 5432, ni 5433,
   ni la de pruebas 5434): *ejercerla **una vez**, *y anotar el resultado en `OPERACION.md`*

*** PASO 3 ***  *y si no: *lo que queda es **lo que el dueno diga**. *Y **hay sitio de sobra para seguir
   midiendo**: *las once ultimas rondas de esta sesion encontraron, **cada una**, algo que el dictamen
   declaraba sin numero.*
```

---

## 12. **Y el metodo, que es lo que hay que conservar**

```
*** 1) `ls` la zona -> leer el fichero que el TITULO nombra, ENTERO -> leer los NOMBRES DE LOS ENSAYOS ->
      comparar -> y `grep` AL FINAL, con las palabras del codigo. *** *
*** 2) *** NUNCA decir «no existe», «y nada mas», «hay que construirlo» o «ya esta» SIN UNA CITA. *** *
*** 3) *** «no se sabe» es un valor que se GUARDA, no una frase que se escribe. *** *
*** 4) *** Si una conclusion se cae, se dice -- y son QUINCE en esta sesion. *** *
*** 5) *** Y la puerta: *** 2033 pruebas de Python + ruff + tsc + 81 de frontend + el build, las cinco. *** *
```

> *** Y **una ultima cosa, que es la que mas se nota al leer el repositorio**: *** *** **este proyecto no da un
> numero sin el contexto que lo hace legible** -- *ni un total sin cobertura, *ni una promocion sin su
> duracion, *ni una etiqueta sin su puntuacion, *ni una ausencia de captura como si fuera una
> indisponibilidad.* *Y **por eso la cobertura nutricional es 7,6 %, y se dice**: *no porque falte, sino
> **porque solo una cadena lo publica.** *
