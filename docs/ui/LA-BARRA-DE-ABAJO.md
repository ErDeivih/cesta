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

---

## 8. *** MEDIDO: *no hay desbordamiento. *Y la hipotesis era correcta ***

*15/10/2026, ronda 42. *Esto llevaba **abierto desde la ronda 17**, *veinticinco rondas,
*diciendo que hacia falta emulacion por CDP.* *Y no hacia falta.* *

```
*** EL TRUCO QUE FALTABA ***: *no `--dump-dom` *(-- *que salio **vacio** en la ronda 18 --), *
   *sino *** poner el numero EN LA PANTALLA y leerlo de la captura *** ✓
*** -> *una barra roja con `viewport=… cliente=… scroll=…` *y una captura normal ✓
*** RESULTADO, pidiendo `--window-size=390` ***: *
   *** `viewport=500  cliente=500  scroll=500` *** ✓✓✓
*** -> *o sea que el viewport CSS real es *** 500 ***, *no 390: *
   *Chrome **no baja de ahi*** *(-- *y la imagen mide 390 porque es *** un recorte
   *de un render de 500 *** --)* ✓
*** -> *y *** `scroll == cliente` ***: *** NO HAY DESBORDAMIENTO *** ✓✓✓
```

*** Y ESTO CIERRA LA DUDA DE LA RONDA 17 ***: *aquel «Calorias se sale de la pantalla»
*no era un desbordamiento: *era *** el recorte *** de una captura de 390 sobre un
render de 500.* *La hipotesis era correcta **y ahora esta medida.*** *

*** Y LO QUE SIGUE SIN PODERSE MEDIR, *dicho con precision ***: *por **debajo de 500 px**
*-- *un movil de verdad mide 390 --* *** no se puede medir con esta herramienta ***,
*porque Chrome no baja el viewport de 500.* *Lo que **si** se sabe es que **a 500 no
desborda**, *y que el `min-w-0` de la ronda 17 **era** un defecto real por el precedente
escrito en `Buscar.tsx`, *aunque no fuera la causa de lo que se veia.* *

*** Y la regla, *que va con las otras diez ***: *cuando una herramienta **no puede bajar
de un minimo**, *el numero que hay que leer es *** el que la pagina dice de si misma ***,
*puesto donde se vea.* *

---

## 9. *** Y POR FIN A 390 px: *no desborda, *y la barra funciona ***

*15/10/2026, ronda 54. *La seccion 8 cerro que **a 500 no desborda**, *y dejo dicho que
**por debajo de 500 no se podia medir** porque Chrome no baja el viewport de ahi.* *
*** Y si se podia.*** *

```
*** EL TRUCO ***: *REA acepta *** `environment.viewport` ***, *y ademas **si puede
   *navegar** *(-- *descubierto en la ronda 52 --).* *
*** -> *con `width: 390, height: 844, device_scale_factor: 2` *se obtiene *
   *** un viewport CSS de 390 x 844 ***, *que es un movil de verdad ✓✓✓
*** -> *y la captura sale a 780 x 1688 *-- *el doble, por el factor 2 --* ✓
```

*** Y EL RESULTADO ***: *

```
*** el armazon de movil esta ***: *el boton ☰ Compra *(-- el cajon --)* arriba, *
   *y la *** barra de abajo *** *con Compra activo en terracota, *Recetas y Calorias ✓
*** -> *** no se corta nada ***: *el buscador, *los botones de micro y de codigo, *
   *«Filtros cadena, pasillo, dieta, ofertas…», *«Guardar estos filtros» ✓
*** -> *y el estado vacio de `Buscar` *** llena la pantalla ***, *
   *con sus *** tres chips de ejemplo centrados *** ✓✓✓
```

*** O sea que la hipotesis de la ronda 17 queda cerrada del todo ***: *aquel «Calorias se
sale de la pantalla» era *** el recorte *** de una captura de 390 sobre un render de 500,
*y **a 390 de verdad no desborda nada.*** *

*** Y LA REGLA DE MEDIDA ***: *antes de decir que una herramienta «no alcanza», *
*hay que mirar **que parametros acepta.*** *El `viewpor` estaba en el esquema del
proveedor desde el principio.* *
