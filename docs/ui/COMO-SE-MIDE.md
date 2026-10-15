# *** Cómo se mide aquí, *y las cuatro veces que medí mal *** *

*Existe porque en **una sola sesión** me salieron **cuatro falsos negativos**, *y los
cuatro eran **de medir**, no de que algo estuviera roto.* *Un falso negativo es **peor que
un fallo**: *un fallo te hace mirar, *y un falso negativo te hace **concluir**.*

---

## 1. *** Pipeline en PowerShell *-> el código de salida se pierde ***

```
*** MAL ***: *`uv run python -m plataforma.prueba_e2e 2>&1 | Select-Object -Last 25` *
   *-- *el `2>&1` mete el **stderr** de `uv` *(-- un `StarletteDeprecationWarning` --)*
      *en la tuberia, *PowerShell lo marca **`NativeCommandError`** *y **el codigo sale 1**
      *aunque el programa haya salido 0 ⚠️
*** BIEN ***: *redirigir a un fichero, *y **preguntar `$LASTEXITCODE`**: *
   `uv run ... > $env:TEMP\x.txt 2>&1; $LASTEXITCODE` ✓
*** -> *y asi se supo: *** el E2E sale 0 y dice `== TODO BIEN` *** ✓
```

## 2. *** `lazy(() => import(...))` *no lleva `from` ***

```
*** MAL ***: *buscar los ficheros vivos con `from '...nombre'` *
   *-- *la app carga las pantallas con `lazy(() => import('./paginas/X'))`, *y **esa
      *forma no lleva `from`** ⚠️
   *-- *resultado: *** 80 muertos de 160 ***, *con `Cesta`, `Buscar`, `ui` y `Suite`
      *dentro, *que **se ven en pantalla** ✓
*** BIEN ***: *`(?:from|import)\s*\(?\s*['"]…['"]` *
   *-- *y el censo bueno: *** 3 muertos de 82 *** ✓✓✓
```

## 3. *** El CSS construido no se escribe como el fuente ***

```
*** MAL ***: *buscar `translateX(-100%)` en el CSS que se sirve, *y ver **NO**, *
   *y concluir que la animacion estaba rota ⚠️
*** BIEN ***: *el minificador lo reescribe a `translate(-100%)`, *que es **equivalente**
   *-- *`translate()` con un argumento **es el eje X** ✓
*** -> *lo mismo paso con `tinta-suave` al principio: *se buscaba donde no era ✓✓✓
```

## 4. *** `newline` en Windows *no conserva: *impone ***

```
*** MAL ***: *`Path.write_text(...)` a secas, *y un fichero *** LF *** pasa a *** CRLF *** ⚠️
*** MAL TAMBIEN ***: *`write_text(..., newline="\n")`, *y un fichero *** CRLF *** pasa
   *a *** LF *** ⚠️
*** -> *las dos veces mal, *y las dos veces el diff salio **del tamano del fichero
   *entero** *en vez del tamano del cambio* ✓
*** BIEN ***: *leer los **bytes**, *mirar que final tenian, *y devolverlos **con ese
   *mismo** ✓✓✓
*** -> *y hacia falta: *en `src/` hay *** LF y CRLF mezclados *** *-- *`Panel` y `Producto`
   *en LF, *`Grupo` y `RepartoEnTiendas` en CRLF, *y asi -- ✓
```

---

## *** Y la regla que sale de las cuatro ***

```
*** un resultado ROTUNDO es sospechoso ***: *
   *-- *«80 muertos de 160» *-- *y los cuatro ficheros clave estaban a la vista ✓
   *-- *«TOTAL: 0 clases» en ficheros que **tenian** clases ✓
   *-- *«`translateX` NO» en una animacion que **funciona** ✓
*** -> *cuando el numero cuadra demasiado, *o sale **cero**, *o sale **todo**, *
   *lo que hay que revisar es *** la medida ***, *no el sistema ✓✓✓
```

*Y una comprobacion mas, *que es la misma idea: *** comprobar en el sitio equivocado
da un falso negativo ***, *y el sitio equivocado casi siempre es **el fuente cuando hay
que mirar lo construido** *-- *o al reves.* *

---

## 5. *** Y un QUINTO intento que NO funciono, *y por que ***

*15/10/2026. *Se intento medir el ancho del viewport **dentro de la pagina**, *para
resolver si el movil desborda de verdad o si era un recorte de Chrome.* *

```
*** LO INTENTADO ***: *un componente temporal que escribe `innerWidth`, `clientWidth`,
   *`scrollWidth` y **los cinco elementos mas anchos** en el DOM, *y leerlo con
   *`chrome --headless --dump-dom` ✓
*** Y SALIO VACIO ***: *el volcado, **0 bytes**, *en los tres anchos probados ⚠️
*** -> *o sea que `--dump-dom` **no devuelve nada por esta via** *(-- *y ademas el
   *primer intento lo puso en un `useEffect`, *que **volcaria antes de que corriera** --)* ✓
*** -> *y el andamiaje se **quito entero**, *con `git checkout` de `App.tsx` y borrando
   *el fichero: *** un instrumento de medida NO se queda dentro de la app *** ✓✓✓
```

*** Y lo que se lleva aprendido, *que es lo unico que valia la pena de este intento ***: *

```
*** `--screenshot` y `--dump-dom` NO valen para medir *** *
   *-- *la captura no dice el ancho, *y el volcado no devuelve nada *
*** -> *lo que hace falta es *** emulacion por CDP *** *
   *(`Emulation.setDeviceMetricsOverride`), *que **no tiene el minimo de ventana**, *
   *o un CDP al que preguntarle `Runtime.evaluate` ✓
*** -> *y se intento `capture_browser_scenario` *y **fallo** *(-- *«Scenario navigation
   *failed before the initial state was captured» --), *y ademas lanzo **Chromium 155**,
   *que **no es el Chrome instalado** ✓
*** -> *** y aqui se para: *gastar contexto en herramienta no arregla la app *** *
   *-- *lo que si la arregla es `min-w-0` en vez de `min-w-[16rem]`, *que ya se hizo *
   *y **no dependia de esta medida** ✓✓✓
```

*** Y la afirmacion «el movil desborda horizontalmente» sigue RETIRADA *** *(-- *no
probada --), *y **eso es lo correcto**: *no se sostiene una afirmacion con una captura
que no puede probarla.* *

---

## 6. *** Y un CAMBIO INERTE, *que es peor que un falso negativo ***

*15/10/2026, ronda 24. *Se aplico `flex min-h-full flex-col gap-N` a la raiz de **siete
pantallas** *(-- `Cesta`, *`ImportarReceta`, *`Escaner`, *`Panel`, *`Despensa`,
*`CocinaModo`, *`PanelMatching`, *`Producto` --)* *y **solo dos hacen algo.*** *

```
*** LO QUE PARECE ***: *«poner `min-h-full` en la raiz hace que la pantalla llene» ⚠️
*** LO QUE ES ***: *`min-h-full` *y `flex-col` hacen que *** el CONTENEDOR *** llene,
   *pero *** los hijos NO crecen solos *** *
*** -> *y en `Buscar` y `Cesta` **si** crecia algo, *porque ahi se le puso *** `grow`
   *al hijo *** *(-- *el estado vacio --)* ✓
*** -> *en las otras *** no hay ningun `grow` ***, *asi que *** el cambio es inerte ***:
   *el contenedor mide mas, *y **nada lo ocupa.*** ⚠️⚠️
*** -> *y se ve en `docs/ui/capturas/11-panel-FASE5.png`: *`/panel` sigue con *** unos
   *550 px de vacio *** debajo de la tarjeta de error ✓✓✓
```

*** Y por que es peor que un falso negativo ***: *un falso negativo **al menos** no toca
nada.* *Un cambio inerte **ensucia el historial**, *parece que se ha arreglado algo, *
*y **cuenta como trabajo hecho** *en los informes.* *Es la version en el codigo de
**una afirmacion sin evidencia.*** *

*** Y la regla que sale ***: *un cambio de maquetacion **se comprueba mirando**, *y si no
se puede mirar la rama donde actua, *se dice **que no se ha comprobado**, *y **no se
cuenta como hecho.*** *Aplicarlo a siete ficheros «porque el patron es seguro» es
verdad *-- *no rompe nada --* *y **no es lo mismo que arreglar.*** *

*** Y la correccion ***: *el patron son **las dos cosas juntas** -- *el contenedor que
llena **y** el hijo que crece --, *y por eso los siete sitios necesitan **una pasada
mas** que mire **cual es el bloque que debe crecer** en cada uno.* *

---

## 7. *** Y la CUARTA vez, *en la misma ronda: *verificar contra el test equivocado ***

*15/10/2026, ronda 26. *Se intento cerrar el agujero del censo de color -- *el que no
cuenta `white` ni `black` -- *anadiendolos a `PALETAS` en `tests/test_interfaz.py`.* *

```
*** SE PROBO CON `test_la_paleta_de_fabrica_no_crece` *** *(-- *el trinquete --), *
   *inyectando `text-white`: *PASO ⚠️*
*** -> *y se concluyo que el cambio era INERTE *-- *y **se revirtio** -- ✓
*** -> *PERO `PALETAS` *** no gobierna el trinquete ***: *gobierna
   *`test_colores_conocidos` *(-- *linea 280: *`if primero in PALETAS` --)* ✓
*** -> *asi que la conclusion estaba bien **por casualidad**, *y el motivo era **falso** ✓
*** -> *se volvio a poner, *y esta vez se probo *** contra los dos ***: *
   *inyectando `text-white` pasan *** los 13 *** *-- *o sea que *** de verdad es inerte ***,
   *en los dos ✓✓✓
*** -> *y se volvio a quitar, *y **no se commiteo** ✓
```

*** Y la leccion, *que es la cuarta de la misma familia ***: *

```
*** una prueba tiene que ir CONTRA EL OBJETO QUE CAMBIAS *** *
   *-- *si tocas `PALETAS`, *el test que lo usa es el que hay que correr, *
      *no el que **te suena** que va de eso *
*** -> *y si el resultado sale bien *** por casualidad ***, *la conclusion **no vale**,
   *aunque sea la correcta ✓✓✓
*** -> *por eso la segunda vez se probo **contra los dos**, *y ahi si se pudo afirmar: *
      *** el cambio es inerte *** ✓
```

*** Y el agujero, *que SIGUE ABIERTO ***: *el censo de color de fabrica -- *el trinquete y
`test_colores_conocidos` -- *** no ve `white` ni `black` ***, *y no se cierra anadiendolos
a `PALETAS`.* *Hay que mirar **como cuenta cada uno**.* *Tres intentos, ninguno aplicado,
porque **ninguno se pudo demostrar.*** *

---

## 8. *** La causa del agujero del color, *encontrada y PROBADA ***

*15/10/2026, ronda 27. *Tres intentos habian fallado *(-- *ron-
da 26 --)* *y ninguno se pudo demostrar. *Esta ronda se encontro **por que**, *y **se
probo con un experimento**, *que es lo que faltaba.* *

```
*** EL AGUJERO ***: *el trinquete `test_la_paleta_de_fabrica_no_crece` **no ve**
   *`white` ni `black`, *y por eso «de 611 a 9» fue **falso** siete rondas* *
   *(-- *el numero real era **43**, *y las 34 clases se migraron en la ronda 25 --)* ✓
*** Y NO ES UNA LISTA INCOMPLETA ***: *el trinquete usa *** `_PALETA_DE_FABRICA` ***,
   *que tiene **su propia expresion**, *y **no** `PALETAS`* *
   *-- *por eso anadirlos a `PALETAS` no hacia nada: *`PALETAS` gobierna
      *** otro test *** *(`test_colores_conocidos`, *linea 280 --)* ✓
*** -> *la expresion exige un *** GUION DETRAS *** -- *`-(?:slate|gray|...|rose)-` --,
   *que es lo que separa el nombre del **tono**: *`text-neutral-500` ✓
*** -> *y `white` y `black` son *** los dos unicos colores de Tailwind SIN TONOS ***: *
   *se escriben `text-white`, *** sin nada detras *** ✓✓✓
*** -> *** no pueden casar NUNCA, *por mucho que se anada un nombre a una lista *** ✓
```

*** Y LA PRUEBA, *que es lo que da valor al diagnostico ***: *se reprodujo la expresion
del test en un script y se pregunto caso por caso.* *

```
    text-neutral-500     CASA
    text-emerald-700     CASA
    text-white           NO CASA
    bg-white             NO CASA
    text-black           NO CASA
```

*** Y EL INTENTO DE ARREGLO, *que NO se aplico ***: *poner **dos ramas** en la
expresion -- *la de siempre, *con tono, *y una segunda para `white|black` con
`(?!\w-)` detras --.* *Se aplico y *** rompio la expresion ***: *`re.error: unbalanced
parenthesis at position 275`, *y el fichero de test entero dejo de cargar.* *Se
**revirtio en el acto**, *porque *** un fichero de test roto es peor que un agujero sin
cerrar.*** *Los 18 volvieron a pasar.* *

*** Y LO QUE QUEDA PARA LA PROXIMA ***: *el agujero **sigue abierto**, *pero ya no es
un misterio.* *La rama esta **escrita entera en el mensaje del intento**, *y lo que
hay que hacer es anadirla **con la expresion compilada a mano antes de tocar el
fichero**, *en vez de escribirla dentro de un `rf"..."` partido en dos lineas y confiar
en que cuadra.* *

*** Y LA LECCION ***: *tres intentos se hicieron **sin entender la causa**, *y por eso
ninguno valio.* *El cuarto fue **encontrar la causa primero**, *y esa parte si valio
aunque el arreglo fallara.* *Cuando algo no se puede demostrar, *lo que suele faltar
**no es el arreglo: *es el diagnostico.*** *

---

## 9. *** Que rama se ve, *y por que casi todo lo que arreglo no se puede mirar ***

*15/10/2026, ronda 29. *Se puso `className="grow"` al estado vacio de `Despensa` *-- *el
mismo arreglo que funciono en `Buscar` --,* *y la captura de `/compra/despensa` ensena
*** otra cosa**: *el titulo dice **«Compra»** *y el cuerpo es **una linea*** *-- *«El
servidor ha fallado» --,* *con *** ~750 px de vacio *** debajo.* *

```
*** LO QUE SE ESPERABA ***: *el `h1` «La despensa» *y su estado vacio ⚠️
*** LO QUE HAY ***: *`Despensa` **corta antes**: *sin API, *su consulta falla *y pinta
   *** `Fallo` *** ✓
*** -> *o sea que *** el `grow` del `Vacio` no se puede mirar ***: *esa rama **no se
   *pinta** sin datos* ✓
*** -> *y el defecto de verdad esta *** en `Fallo`, *que es LA RAMA QUE SE VE *** *
   *-- *en esta pantalla *y **en todas las demas sin API** --* ✓✓✓
```

*** Y por eso llevo ocho rondas arreglando cosas que no puedo mirar ***: *el frontend
servido sin API **solo pinta dos ramas** -- *los estados vacios que no dependen de datos,
*y los errores.* *Todo lo demas cae en `Fallo`.* *

*** Y EL DEFECTO, *que es de PIEZA y afecta a todas ***: *`Fallo` **no llena.*** *Se
pinta arriba, *y el `main` de `LayoutSuite` **no es columna flexible**, *asi que no hay
nada que reparta el alto.* *

*** Y EL PLAN, *con las lineas exactas, para que la proxima ronda no lo busque ***: *

```
*** 1) *** *`src/componentes/Suite.tsx:525`* *-- *el `main`: *anadirle *** `flex flex-col` *** *
   *(-- *es **seguro**: *las pantallas cuya raiz lleva `min-h-full` siguen igual,
   *porque `min-height:100%` se resuelve contra el alto del `main` --)* *
*** 2) *** *y en *** `src/componentes/ui.tsx`, *la funcion `Fallo` *(-- *linea 395 --),*
   *envolver *** SUS DOS `return` *** en `<div className="grid grow content-center">`: *
   *-- *la rama de sin red *(-- *`<Aviso tono="aviso" titulo="Sin cobertura">` --)* *
   *-- *y la de error *(-- *`<Aviso tono="mal" titulo="No he podido traer esto">` --)* *
*** -> *** Y CUIDADO: *los dos `return` acaban en `</Aviso>` seguido de `)` con la misma
   *sangria ***, *asi que **no se puede sustituir por texto**: *hay que hacerlo **por
   *posicion**, *o leer el fichero y contar.* *Eso es lo que me hizo parar hoy.* ✓
*** 3) *** *y `Fallo` **ya lleva su propio comentario** diciendo que se arregla en un
   *sitio y no en las seis pantallas: *«*si se arreglara pantalla por pantalla, *la
   *septima volveria a nacer en rojo*»* *-- *o sea que **el principio ya esta escrito
   *alli**, *solo falta aplicarlo al alto.* ✓
```

*** Y LA LECCION ***: *antes de arreglar una pantalla, *hay que saber *** que rama se
esta mirando***. *Y sin API, *casi siempre es `Fallo`.* *Arreglar el estado vacio de una
pantalla que no lo va a pintar **es trabajo que no se puede verificar**, *y esta noche he
hecho siete de esos.* *
