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

---

## 10. *** El cero que no era del patron, *y como se supo ***

*15/10/2026, ronda 40. *Se cerro el defecto de la ronda 39 *(-- *`/unirme/:codigo` se
saltaba el armazon de la app --)* *y quedo la pregunta: *** cuantas mas lo hacen ***.* *

```
*** LA PRIMERA PASADA ***: *una expresion que buscaba `<Route path=... element={...}>`
   *en **una linea**, *y dio *** 0 de 16 *** ✓
*** -> *pero esa expresion *** solo pilla las rutas de una linea ***, *
   *y en `App.tsx` hay rutas que ocupan **varias** ⚠️
*** -> *o sea que el cero podia ser *** del patron, *no del codigo *** ✓✓✓
*** -> *y un cero que viene del patron es *** exactamente *** el error de la ronda 25,
   *cuando «de 611 a 9» salio de un patron que no contaba `white` ni `black` ✓
```

*** ASI QUE SE REPITIO, *cortando por BLOQUES ***: *desde cada `<Route` hasta su `/>`,
*sin suponer cuantas lineas ocupa.* *Y dio *** 0 otra vez ***, *con las mismas 16 rutas.* *
*Y esta vez **si** vale, *porque el segundo patron no depende del formato.* *

*** Y LA REGLA ***: *cuando un censo da **cero**, *hay que preguntarse **si el cero es
del codigo o del patron.*** *Y la forma de saberlo es *** contarlo de dos maneras
distintas ***: *si las dos dan cero, *es del codigo.* *

---

## 11. *** La medida era correcta. *La pantalla, *no. ***

*15/10/2026, ronda 44. *En la ronda 30 se le puso `grow` a `Fallo` *y a `main` para que
los errores *** llenaran la pantalla en vez de quedarse arriba con cientos de pixeles
vacios debajo.*** *Y la comprobacion fue: *capturar `/compra/despensa` antes y despues.* *
*Dio *** el MISMO SHA-256 ***, *o sea byte a byte identica,* *y se concluyo que el cambio
*** no hacia nada visible.*** *

```
*** Y ERA FALSO ***. *En la ronda 44 se capturo *** `/panel` *** *-- *que si usa `Fallo` --, *
   *y el panel de error sale *** CENTRADO ***, *en y≈495-608 de un area que va de 88 a 900.* *
*** -> *antes estaba *** pegado arriba con ~550 px de vacio debajo *** ✓
*** -> *** el cambio llevaba funcionando desde la ronda 30 *** ✓✓✓
```

*** Y EL ERROR NO FUE DE MEDIDA: *FUE DE PANTALLA ***. *En la ronda 30, `/compra/despensa`
*** no usaba `Fallo`** *-- *pintaba un `<p>` crudo, *que es justo lo que se arreglo en la
ronda 31 --,* *asi que **no habia nada que cambia** ahi.* *La captura era correcta y la
conclusion era falsa, *porque *** la pantalla elegida no era la que usaba la pieza.*** *

*** Y LA REGLA, *que es la numero doce de esta lista ***: *antes de concluir que un cambio
«no hace nada», *hay que comprobar *** que la pantalla elegida USA lo que se cambio.*** *
*Y se comprueba con un `git grep` del componente, *no con la intuicion: *si `Fallo` no
aparece en el fichero de esa pantalla, *esa captura **no puede** demostrar nada sobre
`Fallo`.* *

---

## 12. *** `min-h-full` no sirve para un `return` temprano, *y lo dijo la medida ***

*15/10/2026, ronda 46. *Se vio en `/producto/...`: *el error sale *** pegado arriba
con ~570 px de vacio debajo ***, *aunque `Fallo` ya lleva `grow` desde la ronda 30.* *
*Y el motivo es que en esa pantalla el error esta en un *** RETURN TEMPRANO ***, *antes
de la raiz `min-h-full`: *su padre **no es un contenedor flexible con altura**, *y un
`grow` sin eso **no hace nada.*** *

```
*** LO QUE SE PROBO ***: *anadirle *** `min-h-full` *** al envoltorio de `Fallo`, *
   *esperando que `min-height: 100%` se resolviera contra el `main` del armazon ✓
*** -> *y la captura de `/producto/...` antes y despues dio *** EL MISMO SHA-256 *** *
   *-- *1B216EC023CCB1E0 --:* *** no cambio NADA *** ⚠️
*** -> *y el motivo es una sutileza de CSS: *** `min-height: 100%` NO se resuelve
   *contra un padre de altura `auto` *** ✓
*** -> *el `main` tiene `flex-1`, *pero su altura como elemento flexible es `auto`,
   *asi que *** el porcentaje no resuelve *** ✓✓✓
*** -> *se revirtio, *porque *** lo que no hace nada no se queda *** ✓
```

*** Y LO QUE ESTO ENSEÑA ***: *que el `grow` funciona cuando el padre **es** un
contenedor flexible con altura *(-- *los casos de las secciones 10 y 11 --), *y que
**no hay una solucion de una palabra** para el caso del `return` temprano.* *La salida
honesta es *** una pantalla por pantalla *** *o *** una unidad de viewport ***,
*rellenar el lado del armazon.* *Pero eso **no se elige sin medirlo**, *y hoy solo se
sabe que `min-h-full` **no** es la respuesta.* *

*** Y LA MEDIDA ES LO QUE LO DICE ***. *Sin la captura, *«le pongo `min-h-full` y ya
esta» habria sido una afirmacion razonable, *y **falsa**, *y se habria quedado en el
codigo pareciendo un arreglo.* *

---

## 13. *** LA CAPTURA ERA DE OTRA APLICACION, *y mate un servidor que no era mio ***

*15/10/2026, ronda 48. *Esto no es un falso negativo de medida: *es **peor**, *y va
primero porque es lo que hay que leer antes de volver a capturar nada.* *

```
*** LO QUE SE HIZO ***: *`vite preview --port 4173 --strictPort`, *esperar 7 segundos,
   *y capturar `/avisos` ✓
*** LO QUE SALIO ***: *una aplicacion que NO es esta* *-- «OpoFuente», *con Temario,
   *Tests, *Simulacros, *Formacion, *tema claro *y **otra tipografia** -- ⚠️
*** -> *** `--strictPort` significa «falla si el puerto esta ocupado» *** ✓
*** -> *o sea que *** `vite preview` NO ARRANCO ***, *y Chrome cargo *** lo que ya
   *estaba escuchando en 4173 *** ✓✓✓
*** -> *y despues, *al terminar, *** mate el proceso que ocupaba el puerto *** ⚠️⚠️⚠️
```

*** Y ESO ES LO GRAVE ***: *el comando de limpieza mata «el que escuche en 4173»,
*sin preguntar **de quien es.*** *Y esta vez **no era mio.*** *He tumbado el servidor de
vista previa de **otro proyecto** del propietario, *sin saberlo y sin poder deshacerlo.* *

*** Y LAS TRES REGLAS QUE SALEN, *que son obligatorias desde ya ***: *

```
*** 1 ***. *** Comprobar que el puerto esta LIBRE **antes** de levantar nada ***, *
   *y si `--strictPort` falla, *NO capturar: *el servidor no es el tuyo.* *
*** 2 ***. *** Mirar QUE APLICACION se sirvio *** antes de dar una captura por buena: *
   *el titulo de la pestana *o el nombre del lateral tienen que decir **«Cesta»**.* *
   *Una captura de otra app **no prueba nada** y ademas **despista**.* *
*** 3 ***. *** No matar nunca un proceso que no se ha arrancado uno mismo ***. *
   *Se mata **el proceso que se lanzo** *(-- *el `Start-Job` --)*, *no «el que ocupe
   *el puerto»* *-- *que es una forma de decir «mata lo que haya», *y esta vez
   *habia algo **ajeno** --.* *
```

*** Y LA CAPTURA DE ESTA RONDA SE DESCARTO ***, *no se commitearon sus bytes, *y el
cambio queda como *** aplicado y SIN VERIFICAR *** *-- *que es la verdad.* *

---

## 14. *** SI SE PUEDE PULSAR. *Y lo tenia delante. ***

*15/10/2026, ronda 52. *Durante veinte rondas he escrito que el limite era
«*`--screenshot` **no puede interactuar**»*, *y que por eso los estados que dependen de
datos **no se podian verificar.*** *** Y era verdad a medias.*** *

```
*** `--screenshot` NO puede pulsar *** ✓
*** -> *** pero `capture_browser_scenario` de REA SI ***: *
   *`goto`, *`fill`, *`click`, *`wait_for`, *y captura al final ✓✓✓
*** -> *y se comprobo en `/escaner`: *se relleno el campo con «NO - ES - UN - CODIGO»,
   *se pulso «Buscar», *y la captura sale con *** el campo relleno *** *
   *y *** el `Fallo` con su boton «Volver a intentarlo» *** ✓
*** -> *** la capacidad que creia que faltaba estaba delante *** *
   *-- *quinta vez en dos noches --* ✓
```

*** Y DOS COSAS QUE HAY QUE SABER ANTES DE USARLO ***: *

```
*** 1 ***. *** El servidor tiene que sobrevivir entre llamadas. *** *
   *Un `Start-Job` dentro de una llamada a `pwsh` *** muere con su proceso***, *
   *y REA navega *** en otra llamada ***: *por eso el primer intento dio *
   *«Scenario navigation failed». *Hay que levantarlo como *** trabajo en segundo
   *plano gestionado ***, *que si sobrevive ✓
*** 2 ***. *** REA usa TEMA CLARO por defecto *** *(`color_scheme: light`), *
   *asi que sus capturas **no** son comparables con las de `--screenshot`, *
   *que salen en oscuro.* *Y eso, *de paso, *** ensena que el tema claro existe y
   *funciona*** ✓
```

*** Y LO QUE SIGUE SIN PODERSE VER, *que ahora se sabe por que ***: *la rama de **400**
de `/escaner` *-- «No tengo ese codigo» --* **necesita que la API conteste**, *
*no solo poder pulsar: *sin API, *la peticion falla **por red** *y sale el `Fallo`, *
*que es lo correcto pero **no es esa rama.*** *

---

## 15. *** La tarjeta de entrar, *y `grow` tampoco sirve ahi ***

*15/10/2026, ronda 56. *La ronda 55 midio el defecto: *en `/compra/listas` sin sesion,
*la tarjeta de entrar *** acaba a un tercio de la pantalla *** *y debajo quedan
*** unos 600 px de vacio***. *Y el arreglo parecia de una linea: *`className="grow"` en
la `Tarjeta`, *que **si acepta `className`.*** *

```
*** SE HIZO Y SE MIDIO ***: *la captura a 390 px despues del cambio tiene *
   *** EL MISMO SHA-256 *** *-- `b547e089d0220ae1d8348091f50391ca32f93329cef796e85cfe8f1814f5842c` --,* *
   *o sea *** byte a byte identica *** ⚠️
*** -> *** `grow` no hizo nada *** ✓
*** -> *y el motivo es el mismo de la ronda 46: *`grow` solo actua si el padre es
   *** un contenedor flexible con altura***, *y **el de esa tarjeta no lo es** ✓
*** -> *se revirtio: *** lo que no hace nada no se queda *** ✓
```

*** Y LO QUE ESTO DEJA CLARO, *que ya son dos casos ***: *el patron `grow` funciona
**dentro** de la raiz de una pantalla *(-- *`Buscar`, *`Escaner`, *`Avisos`, *`Favoritos` --), *
*y **no funciona** ni en un `return` temprano con `min-h-full` *(-- ronda 46 --)*
*ni en una pieza cuyo padre no es columna flexible *(-- esta --).* *

*** O sea que el defecto de la tarjeta de entrar NO es de una linea ***: *hay que
**envolverla** en algo que si sea columna flexible con altura, *o cambiar la raiz de
la rama.* *Y eso *** no se hace sin poder medirlo despues ***, *que es exactamente por
lo que se dejo medido y sin tocar en la ronda 55.* *

---

## 16. *** El censo decia «pendiente» y la medida dijo que NO. *Otra vez el patron. ***

*15/10/2026, ronda 63. *El censo de la ronda 60 dejo cinco raices `grid gap-4` sin
`min-h-full` *como «pendientes», *y se arreglaron dos *(-- `Ajustes` *y `Avisos` --)* *
y una *(-- `Unirse`, *con antes y despues --).* *Quedaban `Cesta:1358` *y `Favoritos:275`.* *

```
*** SE FUE A TOMAR EL ANTES DE `Favoritos` A 390 px ANTES DE TOCARLO *** *
   *(-- *que es la regla que salio de la ronda 60 --)* ✓
*** -> *y la captura ensena que *** EL RECUADRO YA LLENA LA PANTALLA ***: *
   *de *** y≈196 a y≈1495 *** *de 1688, *con «Entra para ver tus favoritos» centrado ✓
*** -> *** `Favoritos:275` NO NECESITA EL ARREGLO *** ✓✓✓
*** -> *aunque su raiz *** sea *** `grid gap-4` sin `min-h-full` ✓
*** -> *porque su `Vacio` *** ya lleva `grow` ***, *y **ya funciona asi** ✓✓✓
```

*** Y ESO CORRIGE DOS COSAS ***: *

```
*** 1 ***. *** El censo estaba mal ***: *tener una raiz `grid` sin `min-h-full` *
   *** no implica que falte el patron ***. *Lo que importa es si **el bloque que debe
   *llenar** llega a hacerlo, *y eso *** solo lo dice una captura.*** *
*** 2 ***. *Y explica por que en la ronda 60 *** no se pudo probar *** que `Ajustes`
   *y `Avisos` necesitaran el cambio: *sus capturas «antes» eran a **1440**, *donde
   *ya llenaban, *y **probablemente tambien llenaban a 390**. *O sea que **es posible
   *que aquellos dos cambios no hicieran falta.*** *Quedan como APLICADOS Y SIN
   *VERIFICAR EN SU EFECTO, *y ahora se sabe **por que**.* *
```

*** Y LA REGLA, *que es la 4 de esta lista otra vez ***: *un censo por **clases de
Tailwind** dice **donde mirar**, *no **si falta algo**.* *El «pendiente» de un censo
**no es un defecto** hasta que una captura lo ensena.* *

---

## 17. *** CONSOLIDAR NO ES ARREGlar: *ES FOTOGRAFIAR ***

*15/10/2026. *Y esta es la que mas me ha costado ver, *porque *** la cometi mientras
creia que estaba arreglando el problema***. *

### Lo que paso

```
*** en la ronda 1 *** *de este encargo recibi un encargo explicito: *
   *«`ESTADO-FASE-5.md` conserva afirmaciones OBSOLETAS; *hay que corregirlo» ✓
*** -> *y lo hice: *le puse *** un resumen vigente arriba ***, *separe el historico, *
   *y elimine las cuatro contradicciones ✓✓✓
*** -> *** y lo di por bueno *** ⚠️
*** -> *** y desde esa foto, *el mundo se movio ***: *
   *-- *se monto un entorno aislado *(-- *rondas 22 a 35 --)* ✓
   *-- *se corrio una puerta que paso *** 87 de 87 *** ✓
   *-- *y *** cuatro documentos se quedaron atras *** sin que nadie lo notara ⚠️
```

### Y los cuatro, *uno por uno*

```
*** 1 ***. *`docs/DICTAMEN.md`, PARTE 2: *decia «el recorrido completo: *** NO HECHO ***», *
   *«que lo servido se comporte: *** NO VERIFICADO ***»...* *-- *ronda 42 ✓
*** 2 ***. *`docs/DICTAMEN.md`, PARTE 1: *decia que el limite era *** «el acceso a datos» ***, *
   *y el acceso a datos *** se habia conseguido *** *-- *ronda 43 ✓
*** 3 ***. *`docs/ui/ESTADO-FASE-5.md`: *su conclusion decia *** «el limite es UNO: *** *
   *** hace falta API con datos controlados» ***, *y la API *** se monto y se uso *** *
   *-- *ronda 44 ✓
*** 4 ***. *`docs/ui/VERSION-SERVIDA.md`: *«NO VERIFICADO TODAVIA: *** que lo servido
   *** se comporte bien» ***, *y la puerta *** navega y pulsa la aplicacion *** *
   *-- *ronda 45 ✓✓✓
```

*** Y los tres primeros los encontre *** por casualidad***, *trabajando en otra cosa. *
*No los busque: *tropecé.*

### Y la causa, *que es lo que importa*

```
*** consolidar un documento *** no lo mantiene vivo***: *lo *** fotografia *** ✓
*** -> *y una foto *** es cierta el dia que se hace ***, *y no despues ✓
*** -> *** el documento no se quedo obsoleto por descuido: *
   *** se quedo obsoleto porque EL TRABAJO SIGUIO *** ✓✓✓
*** -> *y yo lo habia dado por bueno *** al terminarlo ***, *que es lo mismo que *
   *dar por bueno un censo *(-- *la leccion 16 --)* ✓
```

*** Y ES EL MISMO FALLO QUE EL DE LA PUERTA MECANICA ***, *que es lo que lo hace
interesante: *

```
*** `prueba_navegador.py` *** daba por bueno lo que ya no comprobaba*** *
   *(una frase reescrita, *cinco rutas movidas, *una espera de carrera)* ✓
*** -> *y *** los documentos daban por bueno lo que ya no era cierto *** ✓
*** -> *** los dos son una foto que se confunde con un estado *** ✓✓✓
```

### Y la regla que sale

```
*** 1 ***. *** Todo documento que afirme un estado lleva CUANDO se midio***, *
   *y *** que lo que dice caduca *** ✓
*** 2 ***. *** Cuando el trabajo sigue, *los documentos que lo describen ***
   *** hay que volver a mirarlos ***, *y *** enumerarlos ***, *no esperar a tropezarlos ✓
*** 3 ***. *y la mas importante: *** «lo arregle» no es «esta arreglado» *** ✓
   *-- *un documento consolidado el 15/10 es cierto *** ese dia ***, *
      *y *** hay que decir de que dia es *** ✓✓✓
```

*** Y la comprobacion que deberia haber hecho antes ***: *buscar en MIS documentos
las frases que affirman un limite *(-- *«no se puede», *«NO HECHO», *«sin verificar»,
*«el limite es» --)* *y *** mirar si siguen siendo ciertas***. *Es una busqueda de
un minuto, *y la hice en la ronda 45, *cuatro documentos tarde.* *

### Y la comprobacion, *corrida de verdad*

*** Y la he corrido *** al escribir esta seccion ***, *que es lo minimo que se puede
hacer despues de escribir una regla. *Buscar en los documentos *** vigentes ***
*las frases que affirman un limite *(-- *«NO HECHO», *«no se puede», *«sin verificar»,
*«el limite es» --)* *y mirar si siguen siendo ciertas: *

```
*** `docs/DICTAMEN.md` ***: *de las seis coincidencias, *una es la regla del documento, *
   *dos son las correcciones que acabo de hacer, *y *** tres affirman algo ***: *
   *-- *«pantallas con sesion, con captura: *** NO HECHO ***» *-- *y *** es cierto *** ✓
   *-- *«no se puede afirmar que el despliegue publico este listo» *-- *** cierto *** ✓
   *-- *y la tabla de la 1.2, *que ya es la version corregida ✓
*** `docs/ui/ESTADO-FASE-5.md` ***: *las dos coincidencias son *** las correcciones *** ✓
*** `docs/ui/VERSION-SERVIDA.md` ***: *una, *y es *** «lo que sigue SIN VERIFICAR» ***, *
   *que *** es cierto *** ✓
*** -> *** NINGUNA es un limite obsoleto *** ✓✓✓
```

*** Y eso cierra la seccion ***: *la regla no sirve de nada si no se corre, *y
*** correrla cuesta un minuto.*** *

### 17.bis *Y LA COMPROBACION, *PARA QUE SE PUEDA CORRER MAÑANA*

*** Y la escribi en un `$env:TEMP`, *que se borra solo***. *Asi que va aqui, *
*** que es donde vive la regla***: *si la regla no lleva la comprobacion al lado,
*es *** una regla que no se corre***. *

```
*** De los documentos VIGENTES, *no del historico ***: *el resumen y las PARTES 1
*y 2 del dictamen, *y los tres de `docs/ui` que dicen estado. *Busca numeros y
frases que *** el trabajo posterior dejo atras***: *

    VIEJAS = 87 ok | 177 ok | 190 ok | «no llega al final» | «NO HECHO»

*** En el dictamen, *el historico empieza en la PARTE 4 *y NO se mira*** ✓
```

*** Y SU PRIMERA PASADA ENCONTRO TRES *** *(-- *rondas 85 y 86 --)*: *«paso de
19 ok a ***177 ok***» *en el resumen, *y «la seccion de los toques ***no llega al
final***» *en las PARTES 1 y 2. *Las tres *** en la primera pagina del entregable.*** *

*** Y POR QUE SE ESCAPARON ***: *el script de la ronda 85 buscaba *** un bloque
exacto *** *y lo sustituyo, *y *** habia dos sitios con el mismo numero***. *Es
*** el mismo error de las 22 lineas***: *arreglar un sitio y no su vecino. *Y esta
vez lo encontro *** una comprobacion, *no mi memoria***. *

*** Y EL COMANDO, *para no volver a escribirlo*** (vive en
`plataforma/comprueba_documentos.py`): *

```powershell
uv run python -m plataforma.comprueba_documentos
```
