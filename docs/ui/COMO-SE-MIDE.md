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
