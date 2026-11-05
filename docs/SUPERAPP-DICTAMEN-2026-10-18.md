# Dictamen por tipo de uso — 18/10/2026

**Qué es este documento.** *No es un resumen del trabajo: es el **dictamen** que la especificación pide
por separado, porque «uso doméstico», «móvil», «piloto» y «público» no son el mismo listón.*

**Cómo se ha escrito.** *Cada afirmación va con lo que **se ha medido**, y lo que no se ha medido se
dice como no medido.* *No hay ninguna capacidad declarada por una pantalla que pinte ni por un número
de pruebas.*

---

## 1. Uso doméstico (una casa, una o dos personas, sin prisa)

**Dictamen: APTO con reservas declaradas.**

| lo que se ha medido | cómo |
|---|---|
| Se entra como una persona del banco y la pantalla distingue «sin lista de casa» de «sin listas» | *medido en 8080/5174 con `c_sin_listas` y `a_casa`: dos textos distintos* |
| La comparación de precios no presenta la horquilla del grupo como ahorro del artículo | *4 superficies verificadas leyendo el texto de la página* |
| El diario explica por qué no puede proponer nada en vez de no hacer nada | *`ver.isError` añadido y probado con `tsc`* |
| La lista elegida se recuerda **por persona**, no por navegador | *`PUT /api/preferencias`, servidor por `usuario_id`* |
| Ausencia de dato no se convierte en cero | *7 pruebas del §8 + 5 del diario + las de `Cocina`/`Tendencias`* |
| El error de una cadena de recolección ya no se pierde | *`log_error` con rotación, y dos pruebas de que se llama* |
| **El escenario del §8 pasa entero, medido por HTTP** | *A: Casa + Viaje y **5 recetas**; B: Mi lista y **0 recetas**; C: ninguna. `B → /api/listas/<la de A>` = **404**.* *Y dos marcas con dos EAN sin fusionar* |
| **La suite entera, en una base que funcione** | *`2114 passed, 17 skipped, 0 failed`* |

**Y una nota sobre cómo se ha medido el escenario**, porque es la parte que más se suele saltar:
*no se ha declarado por una pantalla que pinte. Se ha medido con tres cuentas reales del banco de
ensayo, pidiendo `/api/listas` y `/api/recetas` con la cookie de cada una, y comprobando **lo que no se
ve**: B pidiendo la lista de A recibe un **404**.*

*Detrás de eso había un defecto que ninguna pantalla podía enseñar: la API de recetas abría
`data/recetas.sqlite` —**el de casa**— porque la ruta sólo se podía fijar en código. Devolvía cero
recetas para todo el mundo, y una pantalla vacía no distingue «no tienes recetas» de «estoy mirando el
recetario de otra casa». Se arregló con `CESTA_RECETAS`.*

**Reservas, y son de datos, no de código:**
- *Calorías sólo puede enseñar el dato de **1 de cada 5** productos (21,8 % de `grupo` con `kcal_100g`).*
  *Los tres ingredientes del escenario —arroz, leche, huevos— **no lo tienen**.*
- *El catálogo de ensayo tiene **una sola fecha de precios**, así que «cuánto ha bajado» no se puede
  ejercitar en él.*
- *La tarjeta de primera vez (`LoQueSeCompra`) **no se ha visto en pantalla**: necesita una cuenta sin
  historial y no llegué a reproducirla.*

---

## 2. Uso móvil (el mismo producto, en un teléfono, de pie en el pasillo)

**Dictamen: APTO en lo medido; NO VERIFICADO en lo que toca este trabajo.**

| lo que se ha medido | cómo |
|---|---|
| La puerta de interfaz móvil mide la ficha del producto a 390×844 con `has_touch` | *`prueba_navegador.py:2306`, ruta `/compra/productos/…`* |
| Los objetivos táctiles de la ficha cumplen 44 px | *`test_ui_movil.py`, 33 pruebas verdes tras corregir la ruta desfasada* |
| Una pantalla sin red no pierde los cambios: se encolan y se suben al volver | *`Cesta.tsx`, cola sin cobertura* |

**Reservas:**
- ***De las cuatro superficies corregidas, dos están leídas también en móvil (390×844, `has_touch`).***
  *La salvedad del grupo: «La diferencia es entre los artículos del grupo…» **sale** (3 504 caracteres,
  cero errores).* *Y **la tabla de la ficha**, que es la que tuvo el defecto original:*

      /compra/productos/ensayo/arroz-a  main=1  texto=2479  errores=[]
        «diferencia +9,1 %»            <- el ahorro EXACTO de su mismo articulo
        «diferencia otro articulo» x2  <- las dos marcas distintas, NO como ahorro
        «De la mas barata a la mas cara de este MISMO articulo hay 9 % de diferencia por kg»

  *** El 41 % que comparaba el Pote con el Hacendado ya no puede aparecer: *** *el arroz A muestra su
  **9,1 %** real contra el mismo EAN, y el arroz B sale marcado como «otro articulo».*
- *La columna del buscador y la tarjeta de ejemplos **siguen verificadas sólo en escritorio**.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*
- *La PWA (instalación, offline real, arranque en frío) **no se ha probado** en esta sesión.*

---

## 3. Piloto (unas pocas casas de verdad, con datos reales)

**Dictamen: APTO en código, con dos condiciones de entorno antes de arrancar.**

**La suite entera, en una base que funcione** (`55433`, desechable, fuera de 5432/5433/5434):

```
2114 passed, 17 skipped, 0 failed   (4:56)
```

**Y no se ha relajado ninguna prueba para llegar ahí.** *Los diez fallos que había tenían **una sola
causa, y era mía**: un fixture de `test_ahorro_exacto.py` que hacía `sys.modules.pop` y volvía a
importar el módulo del catálogo, dejando **dos copias vivas**. Los cinco fallos de
`test_g04_catalogo_de_ensayo.py` —incluido «una conexión ve una sola versión»— **estaban detectando
justo eso**.* *La prueba hacía su trabajo.*

**Las dos condiciones de entorno, y ninguna es de código:**

1. **La base compartida de pruebas (5434) no acepta conexiones.** *No es un esquema desfasado: el
   puerto no escucha.* *Las mismas pruebas pasan en una base limpia.* *Hay que recrearla o usar una
   propia.*
2. **`test_g03_cierre.py` necesita el catálogo de casa** *(grupo 6803, alcampo a 518).* *En una base
   sintética **se salta diciéndolo** desde esta sesión.* *Para un piloto: sembrar el catálogo, correr
   esas pruebas contra una copia, o reescribirlas para que siembren el suyo — que es lo que ya hace
   `test_fase2_f01_sustitucion.py`.*

**Lo que sí está listo para un piloto:**
- *El banco de ensayo (`plataforma.ensayo`) crea un entorno completo, idempotente y aislado, y lo
  limpia sin tocar nada ajeno: **25 contenedores propios intactos en las cinco pasadas**.*
- *Cada recolección fallida deja su traza en `data/errores.log` con rotación.*

---

## 4. Público (cualquiera, con datos de cualquiera)

**Dictamen: NO APTO. Y no es una cuestión de trabajo pendiente.**

| lo que lo impide | dónde está |
|---|---|
| Los datos son de **uso privado**, con cuentas por persona: no hay separación multi-inquilino probada | *`almacen` filtra por `usuario_id`; **no** se ha probado aislamiento entre inquilinos* |
| No hay TLS, ni despliegue, ni límites de tasa por IP pensados para público | *`CESTA_API` va por HTTP en loopback* |
| La cobertura de catálogo es parcial por cadena, y el README lo dice | *«cobertura no es catálogo completo»* |
| Las calorías cubren el 21,8 %, y publicar un total sería mentir | *medido* |

**Y sobre todo**: *el encargo dice explícitamente **no desplegar públicamente**.* *Este dictamen no
cambia eso: lo documenta.*

---

## Lo que este dictamen NO dice

- *No dice que la aplicación esté terminada: **quedan M05–M22**.*
- *No dice que lo verificado lo esté en todas partes: **cuatro superficies en escritorio, no en móvil**.*
- *No convierte en «cerrado» nada que no tenga una lectura en pantalla o una prueba que lo fije.*

**Lo que sí dice, y es lo único que puedo firmar hoy**: *que la comparación de precios ya no puede
presentar dos artículos distintos como si fueran el mismo, que eso está probado en el contrato y
leído en cuatro pantallas, y que lo que falta para cada tipo de uso está escrito arriba con su motivo.*

---

# Revisión del 20/10/2026 — lo que ha cambiado desde este dictamen

*Este dictamen se escribió con lo medido hasta el 18/10. Estas son las cosas que han cambiado, y las
que **no** se han podido medir.*

## Lo que ahora está verificado y antes no

| | |
|---|---|
| **M15 · instalable** | *`site.webmanifest` con 192×192, 512×512 y `maskable` 512; `apple-touch-icon` en PNG; los seis activos servidos por HTTP con su tipo (`image/png`, `application/manifest+json`).* |
| **M15 · armazón con marca** | *`ArmazonDeLaMarca` en `App.tsx`: lo que se ve mientras carga es el marco de la casa, **en el trozo principal**, no una frase en el vacío.* |
| **M15 · offline** | ***Probado cortando la red de verdad.*** *31 trozos precacheados en `install`, verificados uno a uno; tres renders completos sin red (270 caracteres, cero errores).* **Límite dicho: funciona desde la segunda visita** — un service worker no sirve nada antes de estar activo. |
| **M06 · cotización → confirmación → persistencia** | *Por HTTP, con servidor y base de verdad: 409 sin escribir si el sello no coincide, `confirmado: false` si no se manda revisión, `procedencia_importe: "calculado"`, y **409 al republicar el catálogo entre la comprobación y el guardado**.* |
| **M06 · tienda elegida ausente** | *La línea sale sin precio, con `motivo` y con `alternativas` separadas. No se cambia de tienda en silencio.* |
| **M06 · viaje** | *`viaje_cent`/`neto_cent` son `null` salvo que alguien dé el coste.* |
| **M07 · medida del banco** | *`core/banco_identidad.py`: precisión **sobre evaluables**, `null` si no hay; desconocido no es negativo.* |

## Lo que empeora el dictamen, y hay que decirlo

- **El cierre concurrente sigue sin resolver.** *Se intentó un `SELECT … FOR UPDATE` sobre la lista y se
  revirtió porque las pruebas se colgaban; después se vio que **el cuelgue era la base caída**, no el
  lock.* ***O sea: la dirección es correcta y está sin re-probar.*** *Hoy, dos cierres simultáneos pueden
  crear **dos compras del mismo dinero**.*
- **El importe guardado es `calculado`, no `pagado`.** *El histórico todavía no distingue calculado /
  declarado / acreditado.*
- **El aislamiento entre cuentas está probado en listas y recetas, no en todos los endpoints.**
- **El banco de 200 pares de M07 no existe.** *Está la medida que lo contaría, y el permiso para
  construirlo con autoría declarada.*

## Veredicto revisado, por audiencia

| audiencia | antes | ahora | por qué |
|---|---|---|---|
| **doméstico** | APTO con reservas de datos | **APTO con reservas de datos** | *Sin cambio: la comparación, la lista y el diario siguen honestos, y ahora además **abre sin red desde la segunda visita**.* |
| **móvil** | APTO en lo medido | **APTO en lo medido, y más medido** | *Ahora hay marca instalable (192/512/maskable) y offline probado cortando la red. **Lo que sigue sin medirse: el iPhone físico y la barra inferior con el `safe-area`** (el código lo usa, no se ha visto en un aparato).* |
| **piloto** | NO APTO | **NO APTO, y por menos motivos** | *La suite pasa entera (2 125) y la aceptación HTTP de M06 también. Quedan dos: **el cierre concurrente** y **el banco de M07**.* |
| **público** | NO APTO | **NO APTO** | *Por lo mismo que antes, más lo nuevo: un `docker` caído durante diez rondas dejó sin probar la sincronización y el lock. **No se puede vender lo que no se ha probado con la base viva.*** |

## Lo que no se ha podido medir, y por qué

*Docker dejó de responder a mitad de la sesión y no volvió en diez rondas.* *Con él se fue:*
- *`pytest` (necesita PostgreSQL) — **la suite no se ha vuelto a correr desde hace diez rondas***
- *el banco de ensayo, y con él **la sincronización sin red** (la cola de cambios)*
- *el lock del cierre*

*Lo que sí se pudo, y con qué límite:*
- *`ruff`, `tsc`, `lint`, `npm test` (113), componentes (15) y `build` — **todos verdes***
- *HTTP contra la app servida en 8080 — **la marca y los seis activos***
- *el navegador con `patchright` — **el offline, cortando la red***

*** Un dictamen que diga «APTO» sin poder correr la suite es un dictamen que no vale. Por eso el de
piloto y público siguen siendo NO APTO. ***

---

# Revisión del 21/10/2026 — qué cambia, y qué no

*Han pasado **veinticinco rondas** desde la revisión del 20.* *Docker **no ha vuelto**: ya no es «diez
rondas», son **dieciocho** al cerrar esta revisión.* *Así que lo que sigue separa con cuidado **lo que se ha
medido** de **lo que sigue sin medirse**, porque confundirlos es lo que invalidaria el dictamen entero.*

## Lo que ahora está verificado y antes no

**1. El banco de identidad existe y se mide.** *Paso de «no hay banco» a:*

    **210 pares** (el objetivo eran 200), estratificados, con evidencia por par, autor y fecha.
    El **42 %** toca la mitad del catalogo que no tiene EAN.
    precision **100 %** sobre 52 predicciones · especificidad **100 %** sobre 70 pares distintos.
    Los cuatro estados suman 210: 52 exacto, 4 probable, 128 alternativa, 26 cuarentena.

*** Y lo que hace esa precision creible no es el numero: es que el motor **solo puede** decir «exacto» por una
via -- dos GTIN validos e iguales --, comprobado contando las lineas de `decide()`.*** *Un falso exacto
exigiria **un EAN mal puesto en los datos**, no una heuristica equivocada.*

*El umbral queda **documentado** como un arbol de diez reglas, no como una cifra de confianza inventada.*

**2. El cierre ya no es un callejon sin salida.** *Cuando el total cambia entre mirar la lista y cerrarla, el
servidor contesta 409 con la cotizacion nueva.* *Ese cuerpo **se recibia y se tiraba**.* *Ahora viaja en
`ErrorApi.cuerpo`, la pantalla **dice el total nuevo** y ofrece **cerrar con el**, reintentando con el sello
nuevo.*

*** Es la primera vez que el 409 es una conversacion y no un error. ***

**3. El codigo puro del cliente esta entero.** *113 → **320 pruebas de node** y 15 → 22 de componente.*

    `logica/` ... **16 modulos, todos con prueba, y sin una sola dependencia de `api/`**
    `estado/` ... **6 de 6**, incluida la cola offline (guardar y mandar)
    `api/` ....... formato, cliente HTTP y las dos rutas del cierre

*Y por el camino se quitaron **dos acoplamientos** que impedian probarlo (`frase` y `curva` importaban
`api/formato`; `filtrosUrl` importaba de `api/consultas`), y se corrigio **una mentira**: `busquedasRecientes`
decia «guardado» cuando el navegador no habia dejado guardar.*

**4. Hay CI.** *`.github/workflows/comprobacion.yml` con tres trabajos: `ruff` + `pytest` con PostgreSQL de
servicio, `tsc` + lint + pruebas + build, y `comprueba_documentos`.* *** Verificado que los comandos
funcionan y que `uv sync --extra plataforma` instala lo que la suite necesita (el primer intento no lo
hacia, y se corrigio). *** *Sin ejecutar en remoto.*

## Lo que empeora el dictamen, y hay que decirlo

*** La suite completa lleva **dieciocho rondas** sin correr. *** *El ultimo dato es **2 125 pasan, 17
salten, 0 fallan**, de antes de que Docker cayera.* *Las 320 pruebas de node no lo sustituyen: **no tocan ni
una linea de Python**.*

*** Y una afirmacion que hay que retirar: *** *durante decenas de rondas escribi **«M08–M14 y M16–M22: sin
empezar»**.* *Es **falso**: hay **9.254 lineas de pagina** y cliente de API para cada uno de esos espacios,
con sus rutas registradas.*

*Lo que sigue siendo cierto es lo otro: **que exista la pagina no es que funcione**.* *Ninguno de esos
espacios esta verificado con datos.*

## Veredicto revisado, por audiencia

| audiencia | antes | **ahora** | por qué |
|---|---|---|---|
| **doméstico** | APTO con reservas de datos | **APTO con reservas, y las reservas son menores** | *El cierre ya dialoga en vez de bloquearse, y la identidad esta medida con especificidad 100 %. Siguen faltando las pruebas de Python.* |
| **móvil** | APTO en lo medido | **APTO en lo medido, con más medido** | *La cola offline esta probada **por los dos lados del cable**. Lo que falta es el viaje con servidor.* |
| **piloto** | NO APTO | **NO APTO, y por menos motivos** | *Queda **uno**: la suite completa sin correr tras dieciocho rondas y el cierre concurrente sin resolver. Antes eran dos.* |
| **público** | NO APTO | **NO APTO** | *Por lo mismo, y por lo que no cambia: sin auditoría externa, sin datos de otras casas, sin equipo de guardia.* |

*** Lo que separa «doméstico» de «piloto» es una sola cosa: que la suite se pueda correr. *** *No es una
carencia de funcionalidad; es una carencia de **prueba**, y por eso el piloto sigue siendo NO APTO aunque el
uso domestico este mejor.*

## Lo que no se ha podido medir, y sigue sin poder medirse

    `pytest` completo ................... necesita PostgreSQL (Docker, 18 rondas caido)
    la aceptacion de §8 ................ cinco recetas, dos personas, dos listas -- **el criterio integral
                                         del encargo**, y no se puede hacer sin base
    el cierre concurrente ............... dos cierres a la vez; necesita base
    el viaje de la cola offline ......... que `POST /sincronizar` aplique y la vacie al confirmar
    el separador de miles de `euros` .... depende del ICU del navegador; node puede no agrupar y el
                                         navegador si
    un iPhone fisico .................... `safe-area` esta en el codigo, sin verificar en aparato

*** Nada de lo de arriba se declara hecho, y ninguno de los «APTO» de arriba depende de ello. ***

---

# Revisión del 21/10/2026 (segunda del día) — **el motivo del piloto ya no existe**

*Esta revisión retira el unico motivo que quedaba para el NO APTO del piloto, y lo sustituye por lo que de
verdad impide subirlo. Es la correccion mas importante de las ultimas treinta rondas.*

## Lo que se dijo, y era falso

*El dictamen de esta mañana decia:*

> *«piloto: **NO APTO, y por menos motivos.** Queda **uno**: la suite completa sin correr tras dieciocho
> rondas.»*

*** Y no era cierto que no se pudiera correr. *** *Durante diecinueve rondas lo escribi asi, y era una frase
que me ahorraba averiguar **cual** parte de la suite necesita la base.*

## Lo que se midio hoy

    uv run pytest -q tests/

    **1345 passed, 797 skipped, 0 failed, 2 warnings in 2:10**

*** Cero fallos. *** *Y los 797 saltados **no se cuelgan: se saltan con motivo escrito**, porque se anadio a
`tests/conftest.py` un sondeo de dos segundos y un salto por fichero.*

*Antes de ese arreglo, la misma orden **se quedaba seis minutos sin sacar una linea**: cada intento de conexion
espera su `connect_timeout`, y son cientos.* *** Un cuelgue se lee como «no se puede» mucho mas facil que un
fallo. ***

*Y la cuenta cuadra: **1.345 + 797 = 2.142**, que es exactamente el total de la ultima corrida completa
(2.125 pasaban y 17 se saltaban), de antes de que Docker cayera.*

## Que significa para el veredicto

*** El motivo «la suite no se puede correr» desaparece. *** *Pero el piloto **sigue NO APTO**, por otro motivo
y mas estrecho:*

*** Las 797 pruebas que se saltan son las de la API, el almacen, el ensayo y la aceptacion de §8. ***
*Y la aceptacion de §8 --**cinco recetas, dos personas y dos listas**-- es el criterio integral del encargo.*
*No es una prueba de regresion mas: es la que dice si la aplicacion hace lo que se promete.*

*O sea:*

    antes ..... «no se puede correr la suite»          -> no se sabia nada
    ahora ..... «la suite corre, 0 fallos, y **797 pruebas no pueden correr**» -> se sabe **que** falta

*Que es peor para el animo y mucho mejor para decidir: **el piloto no espera a que Docker vuelva para saber si
el codigo esta roto -- esta verde --, espera para saber si hace lo que dice.***

## Veredicto revisado (segunda vez hoy)

| audiencia | esta mañana | **ahora** | por qué |
|---|---|---|---|
| **doméstico** | APTO con reservas menores | **APTO con las mismas reservas** | *Sin cambio: el uso domestico ya contaba con que el cierre concurrente y la aceptacion estan sin probar.* |
| **móvil** | APTO en lo medido | **APTO en lo medido** | *Sin cambio.* |
| **piloto** | NO APTO por **un** motivo: la suite sin correr | **NO APTO por un motivo distinto y más estrecho: 797 pruebas de API y §8 no pueden correr** | ***El primero era una falsa alarma; el segundo es el de verdad.*** |
| **público** | NO APTO | **NO APTO** | *Sin cambio.* |

## Lo que hay que dejar de decir

*** «La suite no se puede correr» *** *-- nunca mas. Hay que decir:*

    corre entera en 2:10 sin base, con 1.345 pasan y 797 saltan por motivo;
    y lo que falta es **poder quitar ese salto**, que es el 37 % de las pruebas.

---

# Revisión del 21/10/2026 (tercera) — **el número era del salto que yo puse**

*La revisión de hace unas horas decia «1.345 pasan y 797 saltan», y lo presentaba como el resultado de la
suite.* *** Y era el resultado de un salto que puse yo. ***

## Lo que se midio despues

*Se hizo configurable la espera del pool (`CESTA_ESPERA_BASE`, por defecto 30 como siempre) y se apago el salto:*

    uv run pytest -q tests/      (CESTA_ESPERA_BASE=1, CESTA_SALTAR_SIN_BASE=0)

    **2077 passed, 1 failed, 32 errors, 32 skipped in 4:47**

*** 2.077, no 1.345. El salto tapaba 731 pruebas que pasan. ***

*Y los 32 errores y el unico fallo son, uno a uno, ficheros que necesitan PostgreSQL: fallan en `arranca()` o
con `ConnectionTimeout`.* *Ninguno es un defecto del codigo de la aplicacion.*

## Y entre esas 731 aparecio un defecto real, mio

    test_interfaz.py::test_colores_conocidos
    App.tsx: `borde/70` pide opacidad sobre `borde`, que es una variable de CSS
    App.tsx: `borde/60`  idem

*Eran del **armazon de marca que escribi yo**.* *`borde` es `var(--borde)`, y Tailwind **no puede ponerle
opacidad a una variable CSS**: omite la clase **en silencio** y el estilo no se aplica.*

*** Las barras del esqueleto de carga que diseñe nunca tuvieron la opacidad que pedian. *** *Nadie lo vio
porque un color plano no da error: se pinta y parece bien.* *Arreglado con `bg-borde opacity-70`.*

## Y un test que daba dos respuestas

*`test_g01_recibo_del_puente` **se saltaba solo** y **fallaba dentro de la suite**.* *Causa: `almacen._pool`
es **un global de modulo** (`almacen.py:48`) que otra prueba dejaba puesto, y `arranca()` no volvia a
comprobar.*

*Arreglado con una fixture que cierra el pool despues de cada prueba.* *** Un `skip` que cambia segun el orden
es peor que un fallo: el mismo comando da dos respuestas. ***

## Lo que esto cambia del veredicto

*** Nada, y es importante decir por que. *** *El piloto sigue NO APTO por el mismo motivo: **las 32 pruebas que
no pueden correr son las de la API, el almacen, el ensayo y la aceptacion de §8**.* *Hablar de 797 o de 32 no
cambia el dictamen; cambia **lo que se sabe**.*

| | antes de esta revision | **ahora** |
|---|---|---|
| pruebas que pasan sin base | *1.345 (con mi salto)* | **2.077** |
| pruebas que necesitan base | *797 «no pueden correr»* | **32 errors + 1 fallo, todos identificados** |
| determinismo | *un test cambiaba segun el orden* | ***el mismo comando da siempre lo mismo*** |
| defectos encontrados | — | ***uno, mio, de opacidad que nunca se aplico*** |

*** Y la frase del dictamen anterior, «corre entera en 2:10 con 1.345 pasan», queda sustituida por esta: corre
entera en 4:47 con **2.077 pasan**, y lo que falta son **33 pruebas que necesitan una base que no hay**.***

---

# Revisión del 21/10/2026 (cuarta) — **§8 no estaba entero bloqueado: la mitad corre y pasa**

*El encargo pide «el escenario obligatorio de **cinco recetas, dos personas y dos listas** como aceptacion
integral».* *Este dictamen llevaba diciendo, en cada revision, que eso **no se podia hacer** sin base.*

*** Y no es cierto: se puede hacer la mitad, y esa mitad lleva meses escrita. ***

## Lo medido

    tests/test_escenario_cinco_recetas.py ....... **7 de 7 pasan**  (1,67 s, sin base)
    la previa de compra (plan -> necesidades -> envases) ... **24 de 24 pasan**

*Los siete, con nombre y apellido:*

    las cinco recetas son cinco y de su dueno
    *** b_no_ve_las_recetas_de_ana ***            <- **las dos personas**, y B no ve lo de Ana
    el arroz del plan suma 350 g
    la leche suma mil ml
    los huevos son tres de un envase de seis
    R1 a cuatro raciones son 300 g de arroz
    lo que no tiene cantidad no la gana

*Corren sobre **SQLite**, no sobre PostgreSQL: el escenario de recetas no necesita la base de la aplicacion.*

## Lo que si sigue bloqueado

    test_revision_a09_compra_hogar ....... las **dos listas con compras cerradas**  (13 errors)
    test_fase2_f07_otro_hogar ............ el **otro hogar**                          (errors)

*** O sea: el bloqueo de §8 no es «§8», es **el cierre de compras de dos listas**. *** *Las recetas, las dos
personas y el calculo de necesidades estan verdes desde hace meses y nadie lo habia mirado.*

## Lo que esto cambia del veredicto

*** Por primera vez desde que empezo este dictamen, el piloto tiene un motivo que **no** es «no se puede
comprobar».***

| audiencia | antes | **ahora** | por qué |
|---|---|---|---|
| **doméstico** | APTO con reservas | **APTO con las mismas reservas** | *Sin cambio: lo nuevo refuerza, no abre.* |
| **móvil** | APTO en lo medido | **APTO en lo medido** | *Sin cambio.* |
| **piloto** | NO APTO: la aceptacion integral sin poder correr | **NO APTO, y por un motivo mucho mas estrecho: el cierre de compras de dos listas** | ***Ya no es «no se puede comprobar §8»: es «§8 tiene una parte comprobada y una que necesita base».*** |
| **público** | NO APTO | **NO APTO** | *Sin cambio: sin auditoria externa ni datos de otras casas.* |

## Y la frase que hay que dejar de decir

*** «§8 necesita la base» *** *-- nunca mas. Hay que decir:*

    §8 tiene dos piezas. Las recetas con dos personas y el calculo de necesidades **pasan**
    (7 + 24 pruebas, sobre SQLite). Lo que necesita PostgreSQL es **cerrar compras de dos listas**.

*** Que es una diferencia grande: la primera frase paraliza, la segunda dice a quien hay que pedirle que
arranque Docker y para que.***

---

# Revisión del 21/10/2026 (quinta) — **las cifras, cuadradas**

> *** Las cifras de esta seccion son las de ESE MOMENTO, y ya no son las de hoy. ***
> *Se dejan escritas porque cuentan **por que** las anteriores estaban mal, que sigue siendo cierto.*
> *La cuenta vigente esta al final del documento.*

*Las revisiones anteriores de hoy dieron 1.345, luego 2.077, luego «2.077 y 32 errors».* *** Ninguna de las tres era
la cuenta final, porque cada una medía con una configuración distinta que yo mismo había puesto antes. ***
*Esta es la que cuadra al número exacto, y dice por qué.*

## La cuenta

    pytest --collect-only -q tests/ ....... **2.142 pruebas recogidas**
    de ellas, pasan ....................... **2.092**
    no pueden correr ...................... **50** (32 errors + 1 failed + 17 skipped)
                                             *todas de la API, el almacen, el ensayo y la aceptacion de §8*

    246 ficheros de prueba, y **ninguno fuera de `tests/`** (comprobado).

*Y fuera de `pytest`:*

    npm test ............... 335
    componentes ............ 22
    `test_aprende` ......... 20 (dejaron de saltarse al instalar el extra `docs`)

*** Total: 2.092 + 335 + 22 + 20 ≈ 2.469 pruebas que pasan, y 50 que no pueden. ***

## Por qué las cifras anteriores no eran esta

*Las tres eran honestas y las tres estaban mal, por la misma razon: **medían con una configuracion que escondia
pruebas**.*

    1.345 ... con un salto mio que tapaba todo fichero que mencionara `almacen` (731 pruebas de mas saltadas)
    2.077 ... sin el extra `docs` (20 de `aprende` saltadas)
    2.092 ... con los dos extras y sin el salto

*** Y lo que hace creible esta ultima no es que sea mas alta: es que `--collect-only` da 2.142, y 2.142 = 2.092 + 50.
La cuenta cierra. ***

## Lo que se ha corregido hoy, y no es codigo de la aplicacion

*Todo lo de abajo estaba **bien escrito y mal configurado**, y cada cosa escondia pruebas o mentia con ellas:*

    el salto de `conftest` .......... tapaba 731 pruebas y un defecto real (la opacidad de `App.tsx`)
    la espera de `arranca()` ........ 65 s por modulo: el cuelgue que parecia «no se puede correr»
    el extra `plataforma` ........... sin `fastapi`/`psycopg` la suite de la API no arrancaba
    el extra `docs` ................. 20 pruebas de `aprende` saltadas en silencio
    `CESTA_SALTAR_SIN_BASE` en CI ... la CI podia salir **verde sin correr nada**
    `almacen._pool` ................. global de modulo: un test daba dos respuestas segun el orden

## Y lo que se ha corregido en el codigo

    `App.tsx` ....................... `borde/70` sobre `var(--borde)`: Tailwind lo omitia EN SILENCIO
    la regla de «que lista» ......... 6 sitios caian a «la primera que haya»; uno de ellos ESCRIBIA en la
                                      lista de otra persona. Ahora es una sola regla con 10 pruebas
    `costeReceta` ................... `completo: true` con un ingrediente sin cantidad
    `panel.py` ...................... «0,00 EUR» de media y un ahorro del 100 % cuando el precio no se sabia;
                                      y dos `round(None)` que habrian dado un 500
    `Favoritos` ..................... «igual» cuando no sabia la variacion
    `Inicio` ........................ un total desconocido pintado como 0 EUR
    `vistasGuardadas` ............... devolvia «guardado» cuando el navegador no habia dejado guardar

## Veredicto, sin cambios en el fondo

| audiencia | veredicto | por qué |
|---|---|---|
| **doméstico** | **APTO con reservas menores** | *Las reservas son las 50 pruebas de base y el cierre concurrente; ninguna toca el uso diario.* |
| **móvil** | **APTO en lo medido** | *La cola offline esta probada por los dos lados del cable. Falta el viaje con servidor.* |
| **piloto** | **NO APTO, por un motivo** | ***El cierre de compras de dos listas. Todo lo demas de §8 esta verificado.*** |
| **público** | **NO APTO** | *Sin auditoria externa, sin datos de otras casas, sin equipo de guardia.* |

*** Las cifras no cambian el dictamen. Lo que cambia es que ahora se puede decir **exactamente** que falta, y
cuanto: 50 pruebas, y de ellas un caso de uso con nombre. ***

*Y una cosa que si conviene decir: **siete de los trece defectos corregidos hoy eran mios**, no del proyecto. Los
otros seis eran de configuracion. Ninguno era de calculo.*

---

# Revisión del 21/10/2026 (sexta) — **lo que se midió después, y con qué**

*Las revisiones anteriores contaban pruebas y defectos.* *Esta añade tres cosas que **se midieron con datos reales**
despues, y son las que sostienen lo que el dictamen puede afirmar hoy.*

## 1. El motor de identidad, medido por los dos lados

*En la ronda 113 se afirmo **leyendo el codigo** que solo hay una puerta al estado `exacto`: dos GTIN validos e iguales.*
*Era una lectura, no una medicion.* *Ahora hay dos:*

    GTIN DISTINTO ... 62 pares reales -> **0 exactos** (62 alternativas)
    MISMO GTIN ..... 195 pares reales -> 43 exactos, y **los 152 restantes en cuarentena por contradiccion
                     del dato**: 17 presentacion incompatible, 11 unidad no comparable, 10 marcas distintas...

*** O sea: el motor no acierta por ser listo, sino por no tener otra puerta. Y cuando el EAN contradice al nombre, a
la marca o a la unidad, se para. ***

*Y una mejora que se probo y **se descarto con numeros**: «una marca que contiene a otra es la misma marca» habria
fusionado **3.344 pares**; la version fina, **345**, y las palabras que se anaden son «baby», «zero», «bio», «men» --
variantes de producto, no la marca.* *** El motor se queda como esta, cauto, y no por falta de ideas. ***

## 2. Los dos calculadores del plan, barridos con 200 productos reales

    costeDeReceta .......... 200 productos del gold -> **0 valores imposibles**
    previa_de_compra ....... 200 productos del gold -> **0 valores imposibles**

*«Imposible» = coste negativo, `NaN`, o coste cero con cantidad pedida.* *No dice que acierten -- eso lo dira §8 con
base --, pero si que **no se rompen ni mienten con lo que hay**.*

## 3. Un defecto real que los datos reales destaparon

*Un envase de **131 g** por 924 cent, y una receta que pide **200 g**:*

    «usar» costaba ......... 1.410,69 cent
    «comprar» decia ........   924 cent   <- UN envase, cuando hacen falta DOS
    lo que sale del bolsillo  1.848 cent

*La pantalla decia que comprar costaba la mitad de lo que cuesta.* *Arreglado: `envasesQueHacenFalta` y `envasesCent`,
16 pruebas, y el artefacto reconstruido con el hash nuevo.*

## Lo que **no** ha cambiado

**Las cuatro audiencias.** *Domestico **APTO con reservas menores**; movil **APTO en lo medido**; piloto **NO APTO por
un motivo** (§8, cerrar compras de dos listas); publico **NO APTO**.*

*** Y no cambia porque lo de hoy no toca §8. Lo que cambia es que tres de las afirmaciones del dictamen dejan de ser
lecturas del codigo y pasan a ser mediciones con datos: el invariante del motor, la solidez de los dos calculadores, y
un defecto de precio encontrado por mirar numeros de verdad. ***

## Lo que falta, en una linea

***50 pruebas que necesitan PostgreSQL, y de ellas el cierre de dos listas. Docker lleva veinte rondas con el motor
atascado -- no caido: contestando 500 -- y su reinicio apaga tambien facylf, que no se toca.***

---

# Revisión del 21/10/2026 (séptima) — **lo que hace falta para instalar la app, y lo que le faltaba**

*Las seis revisiones anteriores miraban la aplicación: el motor, los calculos, las pantallas.* *Esta mira **lo que la
rodea y decide si se puede instalar y actualizar**, que hasta hoy no se habia mirado.*

## Lo que estaba bien, y ahora tiene prueba

*Tres piezas que funcionaban y que **nadie vigilaba**. No eran defectos; eran correcciones que se habrian roto sin que
nadie se enterase.*

    public/sw.js (5 pruebas) ....... el armazon con las cuatro piezas para abrir sin red (y `/` ES el index.html),
                                     los dos marcadores del sello, guardar **una a una y no `addAll`** (atomico: una
                                     URL que falle deja el armazon vacio), navegacion desde la cache, y el precache
                                     aparte del armazon
    site.webmanifest (5) ........... nombre, start_url, display, los dos colores, los cuatro iconos con su `type`,
                                     **el maskable distinto del normal** (el recorte se comeria el dibujo), y el
                                     tamano declarado igual al real (lee la cabecera PNG)
    index.html (6) ................. lang="es", viewport con initial-scale y **viewport-fit=cover**, dos theme-color
                                     distintos, titulo/icono/manifiesto/apple, descripcion y og:, y **ningun script
                                     ni estilo en linea** -- que es lo que la CSP permite

*** Y las tres se comprobaron por el lado que falla. *** *La de la portada, metiendo un `<script>alert(1)</script>` de
verdad: la prueba fallo, y al restaurar volvio a pasar con el fichero identico al commit.*

## Y un defecto de verdad, en un fichero que no es codigo

    plataforma/Caddyfile: **no llevaba `Cache-Control`**

*El problema concreto: `sw.js` sin `Cache-Control`.* *** Si el navegador cachea el propio service worker, no ve la
version nueva **nunca**, y la app se queda clavada en el armazon viejo. *** *Es el fallo clasico de una PWA, y no se
nota en desarrollo porque ahi no hay cache de por medio.*

*Arreglado, con tres lineas y cuatro pruebas:* `no-cache` para `sw.js` e `index.html`, `immutable` para `/assets/*`
*(llevan hash: pedirlos otra vez es gastar red sin motivo).*

## Lo que esto cambia en el dictamen, y lo que no

     domestico ...... **APTO con reservas menores** -- sin cambios: nada de esto se nota en el uso diario
     movil .......... **APTO en lo medido** -- y ahora un poco mas: el maskable y el viewport-fit estan comprobados
     piloto ......... **NO APTO, por §8** -- sin cambios: sigue siendo el cierre de dos listas
     publico ........ **NO APTO** -- y ahora se puede decir **por que, con nombre**: faltaba `Cache-Control`, que ya
                      esta; y siguen faltando la auditoria externa, los datos de otras casas y el equipo de guardia

*** Lo unico que cambia es que el «NO APTO» del publico tiene una linea menos y un motivo mas concreto. ***

## Sin cambios, y hay que repetirlo

*** 50 pruebas que necesitan PostgreSQL, y de ellas el cierre de compras de dos listas. ***
*Docker lleva veinte rondas con el motor atascado -- no caido: contestando 500 en `/version` -- y su reinicio apaga
tambien facylf, que no se toca.*

---

# **La cuenta vigente** — la que hay que leer

*Todo lo que sigue esta medido con el arbol tal como esta, no con una corrida anterior.*

```
pytest --collect-only -q tests/ ......  **2.149** pruebas recogidas, 246 ficheros
de ellas, pasan .....................  **2.099**
no pueden correr ....................  **50**  (todas necesitan PostgreSQL)

npm test ............................  **360**
componentes .........................   22
`test_aprende` ......................   20

TOTAL que pasa ......................  **2.099 + 360 + 22 + 20 = 2.501**
```

*Y la comprobacion de que la cuenta cierra:* ***2.149 = 2.099 + 50.***

*Las cifras de las revisiones anteriores (1.345, 2.077, 2.092, 335...) eran ciertas cuando se escribieron y **estan
superadas**.* *Se quedan porque cuentan **por que** estaban mal, que es la parte que se aprende; pero la que vale es
esta.*

## Y las puertas, con la cuenta de arriba

```
ruff ................. limpio
comprueba_documentos . TODO BIEN
tsc --noEmit ......... limpio
npm run lint ......... cero avisos
build desde cero ..... 43 ficheros, 0,82 MB, 32 trozos precacheados, 0 rotos
nada sin commitear
docker ............... **motor atascado**: 500 en /version, y su proxy ocupa los puertos 5432 y 5433
```

