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
