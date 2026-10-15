# *** La barra de abajo del movil: *escrita, *y perdida en un refactor *** *

*15/10/2026. *Existe porque **el objetivo la pide por su nombre** *(-- «*y la barra de
abajo del movil **que ya tiene reglas escritas**» --)* *y porque **yo di la FASE 3 por
cerrada sin comprobarlo.*** *

---

## 1. *** Que hay, *exactamente ***

```
*** `src/componentes/Nav.tsx:143-145` *** *
   *// `pb-[env(safe-area-inset-bottom)]` para el iPhone, que tiene una raya*
   *className="fixed inset-x-0 bottom-0 z-40 border-t border-borde bg-papel …"*
*** -> *la barra esta ENTERA: *fija abajo, *con su borde, *su `z-40`, *y el hueco
   *del iPhone resuelto con `env(safe-area-inset-bottom)` ✓
```

## 2. *** Y por que no se ve ***

```
*** `Nav.tsx` NO LO IMPORTA NADIE *** *-- *salvo `Cabecera.tsx`, *que **tambien esta
   *muerto.*** *Los dos estan en `LOS-FICHEROS-MUERTOS.md` ⚠️
*** y **NO HAY OTRA**: *buscando `fixed bottom-`, *`inset-x-0 bottom`, *`safe-area` *
   *y `bottom-0` en TODO `src/`, *los unicos resultados son **las tres lineas de
   *`Nav.tsx`*** ✓
*** -> *** la barra de abajo del movil esta escrita y NO SE RENDERIZA *** ⚠️⚠️
```

## 3. *** Y como se perdio, *que es lo que importa ***

```
*** `Cabecera.tsx` + `Nav.tsx` eran el layout ANTERIOR: *cabecera arriba, *barra abajo,
   *y **la barra tenia sus reglas escritas** ✓
*** `Suite.tsx` los SUSTITUYO *(-- es el que tiene `APLICACIONES`, *el lateral y el
   *cajon de movil --)* *y **se llevo el lateral y el cajon, *pero NO la barra** ⚠️
*** -> *** no es que la barra no se hiciera nunca: *es que se PERDIO al cambiar de
   *layout *** ✓✓✓
*** -> *y por eso esta en un fichero muerto: *los ficheros muertos **no son solo
   *basura**, *son **la version anterior de la app**, *y ahi dentro hay cosas que la
   *nueva no tiene ✓✓✓
```

## 4. *** Y LO QUE DIJE MAL ***

```
*** dije, en cinco informes seguidos, que la FASE 3 estaba CERRADA *** *
*** y **no lo esta**: *la mire por el lado del lateral *(-- que si quedo hecho: *
   *los iconos, *el estado activo, *el cajon --)* *y **no mire el otro lado**, *
   *que es la barra de abajo ⚠️
*** -> *y el objetivo la nombra **en la misma frase** que lo que si hice ✓
*** -> *** comprobar la mitad de un requisito y dar el requisito por bueno es
   *exactamente el defecto que llevo toda la sesion cazando, *cometido por mi *** ✓✓✓
```

## 5. *** Y lo que falta, *concreto ***

```
*** 1) La barra, *en `Suite.tsx` *(-- que es el que se pinta --)*, *con las tres
   *aplicaciones y su icono, *`fixed inset-x-0 bottom-0`, *y **solo en pantalla
   *estrecha** *-- *el lateral ya lleva `lg:` --.* *
*** 2) Y el hueco del iPhone: *la regla **ya esta escrita** en `Nav.tsx`, *asi que
   *no hay que inventarla: *`pb-[env(safe-area-inset-bottom)]`.* *
*** 3) Y el sitio para que no tape: *el `main` de `LayoutSuite` necesita un
   *`pb` que deje hueco a la barra, *o el ultimo renglon de cada pantalla queda
   *detras ✓
*** 4) Y decidir **que lleva**: *las tres aplicaciones bastan para no perder la
   *orientacion, *pero el menu de secciones del cajon **tambien esta en el
   *lateral**, *asi que la barra **no necesita repetirlo.*** *
```

*** Y no se copia `Nav.tsx`: *se **rehace** en `Suite.tsx` con los tokens y con los
iconos que ya existen.* *Lo que se **reutiliza** es **la regla del iPhone**, *que es la
unica parte que era dificil de recordar.* *

---

## 6. *** Y HECHA, *con un defecto que la captura ensena ***

*`docs/ui/capturas/08-barra-movil.png`, *a **390 x 844**, *que es un iPhone de los
pequenos.* *

```
*** LO QUE FUNCIONA ***: *la barra esta, *fija abajo, *con las **tres aplicaciones**,
   *su **icono**, *y **`Compra` en terracota** porque es la activa ✓
*** Y LO QUE NO ***: *** «Calorias» SE SALE DE LA PANTALLA *** ⚠️
   *-- *y **no es la barra**: *en la misma captura, *«Escribe al menos dos letras,
      *o elige un pas…» sale **cortado**, *y el buscador **se sale por la derecha** ✓
   *-- *o sea que *** la PANTALLA ENTERA tiene desbordamiento horizontal ***, *y la
      *barra es **una victima mas**: *`fixed inset-x-0` mide **lo ancho del viewport**,
      *y si algo de dentro **empuja** mas alla, *los demas **lo siguen.*** *
*** -> *** y esto NO se arregla en la barra ***: *se arregla **en lo que desborda**,
   *y hasta saber que es, *tocar la barra seria **esconder el sintoma** ✓✓✓
```

*** Y es exactamente lo que pide la FASE 3 *** *(-- «*y la barra de abajo del movil …» --), *
*asi que **queda a medias a proposito y dicho**: *la barra esta puesta, *y **el
desbordamiento es lo siguiente**, *porque una barra a la que **le falta un tercio** no
sirve para navegar.* *

*** Y lo que NO se ha hecho ***: *averiguar **que** desborda.* *Se sabe que se ve en
`/compra` y que afecta al buscador y al bloque de sugerencias; *no se sabe **cual de los
dos** empuja, *ni si es uno o son varios.* *Y no se supone: *se mide con
`document.scrollingElement.scrollWidth` contra `clientWidth`, *y despues se busca el
elemento **mas ancho que su padre**.* *

---

## 7. *** CORRECCION: *el desbordamiento **NO esta probado** ***

*** Lo que dije en la seccion 6 queda retirado. *** *

```
*** DIJE ***: *la captura a 390 x 844 demuestra desbordamiento horizontal ⚠️
*** Y NO LO DEMUESTRA ***: *Chrome en Windows tiene un ancho de ventana *** MINIMO *** *
   *(-- alrededor de 500 px --), *y `--window-size=390` **no puede bajar de ahi**: *
   *la pagina se maquetaria a ~500 y la captura seria *** un RECORTE de 390 *** ✓
*** -> *y eso explicaria **por si solo** la barra cortada, *el buscador cortado *y
   *** «Calorias» fuera ***, *SIN que haya desbordamiento ninguno ✓✓✓
*** -> *y ademas: *los tres botones de sugerencia *** SI llevan `flex-wrap` *** *
   *(`Buscar.tsx:213`), *asi que la hipotesis del desbordamiento **no explica**
   *por que se cortan ellos ✓✓✓
```

*** Y lo que SI es un defecto, *y se ha arreglado ***: *

```
*** `TablaResultados.tsx:425` tenia *** `min-w-[16rem]` *** *(-- 256 px --)* dentro de
   *un `grid-cols-[1fr_auto_auto]`, *y en un movil de 390 px la columna `1fr` **no
   *puede encoger por debajo de ese minimo** ✓
*** -> *y lo concluyente **no es mi medicion**: *es que *** el arreglo ya estaba
   *escrito en esta misma app ***, *a tres lineas del campo de `Buscar.tsx`: *
   *«*`min-w-0`, *no `min-w-[16rem]`. *Esto desbordaba la pantalla en un movil…*» ✓✓✓
*** -> *** el mismo defecto, *arreglado en un sitio *y DEJADO EN OTRO, *
   *con la explicacion al lado *** ✓✓✓
```

*** Y para medirlo de verdad *** *hace falta **emulacion por CDP**
(`Emulation.setDeviceMetricsOverride`), *que **no tiene el minimo de ventana**, *o una
comprobacion de `scrollWidth` contra `clientWidth` **dentro de la pagina**.* *Se intento
con `capture_browser_scenario` y **fallo**; *y ademas lanzo **Chromium 155**, *que **no
es el Chrome instalado.*** *No se ha insistido: *gastar contexto en herramienta **no
arregla la app.*** *
