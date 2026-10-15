# Estado de la FASE 5, *medido*

*15/10/2026. *Este fichero **no es un plan**: *es el **inventario** de lo que hay, *con la
distincion que ha costado mas trabajo de toda la fase: *** hecho y verificado *** *no es
lo mismo que *** aplicado y sin verificar.*** *

---

## 1. *Lo cerrado y verificado *

| *que* | *evidencia* |
|---|---|
| *FASE 1, fuentes y escalas* | *WOFF2 local con sus OFL, y 6 escalas en `DIRECCION.md`* |
| *FASE 2, las 18 piezas* | *reescritas contra los tokens* |
| *FASE 3, la navegacion* | *4 iconos a mano, cajon de movil, barra de abajo en `Suite.tsx`* |
| *FASE 4, movimiento* | *entrada de pantalla 220 ms, esqueletos en `Cargando`* |
| *FASE 6, contraste* | *`tests/test_contraste.py` calcula WCAG de verdad* |
| *** el color *** | *** de 611 clases de fabrica a 6 *** *, y el censo ve ya `white` y `black`* |
| *** el error de pantalla *** | *una pieza, `Fallo`; *7 sitios; *visto en `Despensa`, `Panel`, `Tendencias`* |
| *** el error de accion *** | *una pieza, `Etiqueta tono`; *22 sitios convertidos* |
| *** la invitacion *** | *`/unirme/:codigo` dentro del armazon; *16 rutas sin ninguna suelta* |
| *** el desbordamiento del movil *** | *** NO LO HAY *** *, medido: `scroll == cliente == 500`* |
| *** los estados vacios *** | *** 24 de 37 *** *`Vacio` con `grow`; *4 pantallas vistas llenandose* |

*** Las cuatro pantallas con captura propia ***: *`Escaner`, *`Avisos`, *`Favoritos`,
*`Ajustes` *-- *el recuadro pasa de ~250 px a **llenar la pagina**.* *

---

## 2. *Lo aplicado y SIN verificar, y por que *

*Esto **no** es trabajo pendiente: *es trabajo hecho **que no se puede enseñar** con las
herramientas que hay.* *Y va separado a proposito.* *

| *que* | *por que no se puede ver* |
|---|---|
| *8 estados vacios con `grow`* | *sus pantallas necesitan datos; sin API no se pintan* |
| *`Tendencias`, `RecetaDetalle`, `PlanSemanal`* | *ya verificadas de forma indirecta* |
| *`Ajustes`, el error de guardar* | *solo sale **despues de un guardado fallido** *-- *hace falta pulsar* |
| *el viewport por debajo de 500 px* | *Chrome **no baja** el viewport de 500; *un movil mide 390* |

*** Y el limite comun a todo esto es UNO ***: *`--screenshot` **no puede interactuar**
*ni bajar de 500 px de viewport.* *No es una pieza que falte: *es **una capacidad.*** *

---

## 3. *Lo que NO se ha hecho, y con que criterio *

| *que* | *por que* |
|---|---|
| *`Ajustes`, `Avisos`, `Favoritos`, `Grupo` «sin raiz»* | *** ya resuelto ***: *tres estaban bien con `comoPagina` + `grow`* |
| *los mensajes de accion de `Ajustes` y las mutaciones* | *** necesitan titulo a medida *** *, no `Fallo`* |
| *`CocinaModo:96`* | *** no es un error ***: *es `text-tinta-suave`, un mensaje suave* |
| *los `returns` tempranos que no son `Vacio`* | *se sabe que *** `min-h-full` no funciona ***; *`grow` **si*** |

---

## 4. *Las reglas de medida, *que son el activo mas util de la fase *

*Estan en `COMO-SE-MIDE.md`, *trece secciones, *y **todas nacieron de un error mio**.* *
*Las cuatro que hay que leer antes de tocar nada:* *

```
*** 1 ***. *** Que rama se esta mirando. *** *Sin API **solo se pintan dos**: *
   *los vacios que no dependen de datos *y **los errores**.* *
*** 2 ***. *** Comprobar que la pantalla USA lo que se cambio ***, *con un `git grep`. *
   *Si `Fallo` no esta en ese fichero, *esa captura **no prueba nada** sobre `Fallo`.* *
*** 3 ***. *** Contar dos veces. *** *Cuando un censo da **cero**, *hay que preguntarse
   *si el cero es del codigo o del patron.* *
*** 4 ***. *** El puerto y la aplicacion. *** *Comprobar que el puerto esta libre, *
   *mirar que aplicacion se sirvio, *y **no matar nunca un proceso que no se arranco
   *uno mismo.*** *
```

---

## 5. *Y lo que queda de verdad, *dicho en una linea *

*** Falta poder pulsar.*** *Todo lo demas esta hecho, contado y con su evidencia.* *

---

## 6. *** Y un defecto NUEVO, *medido a 390 px: *la pantalla de entrar ***

*15/10/2026, ronda 55. *Primera captura de `Cesta` a 390 px *(-- *la medida de la
ronda 54 --), *y sale **un defecto que no habia visto**: *

```
*** `/compra/listas` sin sesion *** pinta *** la tarjeta de entrar *** *
   *(-- Usuario, *Clave, *«Entrar», *«¿No tienes cuenta? Crea la» --)* ✓
*** -> *y la tarjeta *** acaba a un tercio de la pantalla ***, *
   *con *** ~600 px de vacio *** debajo ⚠️
*** -> *NO es un estado vacio: *es *** la rama previa a la sesion ***, *
   *y a esa tarjeta *** nadie le ha puesto el `grow` *** ✓
```

*** Y es la misma familia que todo lo demas ***: *contenido pegado arriba *y vacio
debajo.* *Pero **en una rama distinta** *-- *la de antes de entrar --,* *que es
justo el tipo de rama que **no se ve** cuando uno mira la pantalla con datos.* *

*** Y LO QUE HAY QUE HACER, que es de una linea ***: *envolver esa tarjeta para que
ocupe, *o centrarla en el alto que sobra.* *Esta **medido y no hecho**, a proposito:
la ronda que lo haga debe **poder verificarlo despues**, y la captura de 390 ya
esta.* *

---

## 7. *** Y LA ESTRUCTURA QUE IMPIDE EL ARREGLO, *dicha y justificada ***

*15/10/2026, ronda 57. *La decision (1) del objetivo dice: *«si al pulir una pantalla
aparece que **su estructura impide el arreglo**, *se dice y se justifica **antes de tocar
la estructura**».* *** Aqui esta, con el diagnostico cerrado y el plan exacto. *** *

```
*** EL DEFECTO ***: *en `/compra/listas` sin sesion, *la tarjeta de entrar *
   *acaba a un tercio de la pantalla *y quedan *** ~600 px de vacio *** debajo ✓
*** LA CAUSA, *leida en el fichero ***: *`Cesta.tsx:1304`, *la rama sin sesion devuelve *
   *`<div className="*** grid gap-4 ***">`* ⚠️
*** -> *NO es `flex min-h-full flex-col`: *es un *** grid, *sin `min-h-full` *** ✓
*** -> *** y esa es la razon de que fallaran los dos intentos ***: *
   *-- *** ronda 56 ***: *`grow` en la `Tarjeta` *** no hizo nada *** *
      *(-- *el padre no es columna flexible --)* ✓
   *-- *** ronda 46 ***: *`min-h-full` en un envoltorio *** tampoco *** *
      *(-- *no resuelve contra un padre de altura `auto` --)* ✓
*** -> *las dos medidas estan en `COMO-SE-MIDE.md`, *secciones 12 y 15 ✓
```

*** Y EL ARREGLO, *que es el patron de `Buscar` y esta verificado funcionando ***: *

```
*** 1 ***. *En `Cesta.tsx`, *la rama sin sesion: *
   *`<div className="grid gap-4">` *
   *** -> *** `<div className="flex min-h-full flex-col gap-4">` *** ✓
*** 2 ***. *Y en `Introducir`, *la `<Tarjeta>`: *anadirle *** `className="grow"` *** ✓
*** -> *y las dos juntas, *porque **una sola no hace nada**: *
   *el `grow` necesita el padre flexible, *y el padre flexible necesita el hijo que crezca ✓
```

*** Y LO QUE HAY QUE SABER ANTES DE HACERLO, *que le costo a esta ronda ***: *el ancla
de texto **no coincide** *-- *la indentacion real no es la que uno escribe *--,* *asi que
**hay que leer el fichero y editar por posicion**, *no sustituir de memoria.* *
*Y `/unirme/:codigo` pinta **la misma** `Introducir` *(-- `Unirse.tsx:101` --), *
*asi que el arreglo **tambien la mejora a ella.*** *

---

## 8. *** Y SE CERRO: *la tarjeta de entrar ya llena la pantalla ***

*15/10/2026, ronda 58. *La seccion 7 dejo el diagnostico y el plan; *esta lo cierra. *
*Y lo que vale no es el arreglo: *es *** como se llego a el.*** *

```
*** RONDA 55 ***: *se midio el defecto *-- *tarjeta a un tercio, *~600 px de vacio --* ✓
*** RONDA 56 ***: *se probo `grow` **solo**, *y *** la medida lo tumbo *** *
   *(-- *la captura salio *** byte a byte identica*** --)* ✓
*** RONDA 57 ***: *se encontro la causa *** leyendo el fichero *** *
   *(-- *la raiz era `grid gap-4`, *sin `min-h-full` --)* *y se dejo *** el plan
   *escrito *** ✓
*** RONDA 58 ***: *se cambio la raiz a `flex min-h-full flex-col` *y se le puso
   *`grow` a la `Tarjeta` *** -- las dos juntas -- *** *
*** -> *y la captura cambio: *`b547e089…` -> `4b1c5153…` ✓ *
*** -> *y la tarjeta pasa *** de y≈1010 a y≈196-1495 ***: *** llena la pantalla *** ✓✓✓
```

*** Y ES EL PRIMER CAMBIO ESTRUCTURAL DE TODO EL OBJETIVO ***, *y necesito exactamente
lo que manda la decision (1): *** decirlo y justificarlo **antes** de tocarlo.*** *
*Tres rondas para dos lineas, *y **funciono a la primera**, *despues de **dos intentos
fallidos.*** *

*** Y LO QUE COSTO, *que ya esta escrito y no se vuelve a pagar ***: *el ancla de texto
**no coincide** con lo que uno escribe.* *La indentacion real era de **4 y 6 espacios**
*y se escribieron **8 y 10** tres veces.* *Se resuelve *** leyendo las lineas exactas con
el numero delante *** *y editando con esa cadena literal.* *

*** Y TAMBIEN MEJORA `/unirme/:codigo` ***, *porque pinta **la misma `Introducir`** *(-- `Unirse.tsx:101` --).* *

---

## 9. *** Y LO QUE QUEDA, *sin adornos y con su razon ***

*** HECHO Y VERIFICADO ***: *las fases 1 a 4 y la 6; *el color de 611 a 6; *las dos
piezas de error, vistas funcionando; *la invitacion dentro del armazon; *24 de 37
estados vacios con `grow`; *el movil a 390 px sin desbordamiento y con la barra; *
*y la tarjeta de entrar de `Cesta`, con antes y despues.* *

*** LO QUE QUEDA, Y POR QUE ***: *

```
*** `Grupo` (34 KB) *** *y *** `Panel` (62 KB) ***: *nunca han tenido una pasada de
   *composicion propia.* *Se les aplico **el patron** *y **las piezas de error**, *
   *pero **no se ha medido ninguna captura suya con datos**, *y sin API no se pintan.* *
*** 8 estados vacios ***: *llevan `grow`, *y *** necesitan la API para verse.*** *
*** el viewport por debajo de 500 ***: *no se puede medir; *a **390 si**, *y no desborda.* *
```

*** Y LA CONCLUSION, *que es lo unico que puedo afirmar sin inventar ***: *lo que se ha
podido medir **esta medido y esta bien**; *y lo que queda, *o *** necesita la API ***,
*o *** necesita una sesion con datos ***.* *No queda nada que se pueda cerrar
**mirando una pantalla vacia.*** *
