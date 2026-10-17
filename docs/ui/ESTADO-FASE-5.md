# Estado de la FASE 5, *vigente*

*15/10/2026. *Este fichero es el **inventario**, *no un plan.* *Su unica regla es que
**toda afirmacion lleva su evidencia**, *y que las tres cosas de abajo **no se mezclan**:*

```
*** IMPLEMENTADO ***: *esta escrito en el codigo. *No dice nada sobre si funciona.*
*** VERIFICADO ***: *se ha visto funcionando, *y hay captura o prueba que lo enseña.*
*** LIMITADO ***: *no se ha podido ver, *y se dice **por que** y **que haria falta.***
```

*** Y la correccion que abre esta version ***: *la version anterior afirmaba que
«no se puede pulsar» y que «no se puede medir por debajo de 500 px».* *** Las dos cosas
eran falsas, y las desmintieron las rondas 52 y 54 de esta misma sesion *** *-- ver
`COMO-SE-MIDE.md` §14 *(-- «Si se puede pulsar» --)* *y `LA-BARRA-DE-ABAJO.md` §9
*(-- «Y por fin a 390 px» --)* --. *El limite real **no era de herramientas**: *
*era, y sigue siendo, *** el acceso a datos.*** *

---

## 1. *IMPLEMENTADO*

| *que* | *donde* |
|---|---|
| *Escalas: 6 pasos tipograficos, radios, sombras, 2 duraciones y 1 curva, espaciado* | *`tailwind.config.js` + `DIRECCION.md`* |
| *Fuentes WOFF2 locales con sus OFL* | *`DIRECCION.md`* |
| *Las 18 piezas contra los tokens* | *`componentes/ui.tsx`* |
| *Navegacion: 4 iconos a mano, cajon, barra de abajo* | *`componentes/Suite.tsx`* |
| *Entrada de pantalla 220 ms · esqueletos* | *`estilos.css` · `Cargando`* |
| *Una pieza para el fallo de PANTALLA* | *`Fallo`, con `titulo` configurable* |
| *Una pieza para el fallo de ACCION* | *`Etiqueta tono`* |
| *El color propio* | *de 611 clases de fabrica a **6*** |

---

## 2. *VERIFICADO*

| *que* | *evidencia* |
|---|---|
| *FASE 1, 2, 3, 4 y 6* | *pruebas, *y `test_contraste.py` calcula WCAG* |
| *El color, de 611 a 6* | *censo, *y el trinquete `test_la_paleta_de_fabrica_no_crece`* |
| *`Fallo` en pantalla* | *visto en `Despensa`, `Panel`, `Tendencias`, `Recetario`, `Diario`, `PlanSemanal`, `Producto`, `Escaner`* |
| *** El error de accion *** | *** pulsado de verdad ***: *se relleno `/unirme` y se pulso «Entrar»* |
| *La invitacion dentro del armazon* | *`/unirme/:codigo`, *antes de borde a borde* |
| *16 rutas, ninguna sin armazon* | *contado **dos veces** *(-- un cero puede venir del patron --)* |
| *** El movil a 390 px *** | *** medido ***: *sin desbordamiento, *y la barra de abajo funciona* |
| *Estados vacios que llenan* | *`Escaner`, `Avisos`, `Favoritos`, `Ajustes`, *y las **dos tarjetas** de `Unirse`* |
| *** Dos cambios estructurales *** | *** con antes y despues ***: *la tarjeta de entrar de `Cesta`, *y `Unirse`* |

*** Y una que NO se pudo verificar, *y se dice ***: *los cambios de patron en `Ajustes`,
`Avisos` y `Cesta` sin listas quedaron **justificados** *(-- faltaban las dos condiciones
del patron --)* *pero **sin captura**.* *** Y SE ACTUALIZA EN LA RONDA 44 ***: *la
puerta del navegador (`prueba_navegador.py`) *** recorre y pasa*** *esas pantallas con
datos reales, *y lo que falta es *** la captura ***, *no la verificacion.*

---

## 3. *LIMITADO -- y esto es lo que queda*

*** REESCRITA EN LA RONDA 44. *** *Esta seccion decia que «el limite es UNO: *hace
falta API con datos controlados», *y *** eso dejo de ser cierto***: *el propietario
autorizo la base desechable, *el entorno *** se monto, *se uso y se desmonto***, *
*y la puerta *** paso 87 comprobaciones con cero fallos***. *Se conserva en el historico.* *

*** Y LO QUE SIGUE LIMITADO, *medido***: *

```
*** 1 ***. *** Siete pantallas con sesion, *capturadas***: *`Recetario`, *`PlanSemanal`,
   *`Diario`, *`Cesta` sin listas, *`Ajustes`, *`Avisos`, *`Favoritos`. *
   *-- *la puerta *** las recorre y las pasa***; *falta *** la captura y el
   *juicio de legibilidad *** ✓
*** 2 ***. *** ACTUALIZADO EN LA RONDA 86: *LA PUERTA YA LLEGA AL FINAL *** *
   *-- *su causa estaba *** medida ***: *a movil las subsecciones *** viven dentro
   *del cajon ***, *y ademas *** los cuatro caminos empezaban en una pantalla
   *sin menu *** ✓
   *-- *y se arreglo: *** un ayudante *** que abre el cajon + *** los cuatro
   *caminos *** empezando por su raiz ✓
   *-- *** y la puerta paso de morir en el primer enlace a ***
      *** 194 comprobaciones sobre 23 secciones *** ✓✓✓
   *-- *y las *** 15 que fallan son dos ***, *y las dos son de la prueba: *
      *el `sr-only` de «Saltar al contenido» *y la curva que la app *** niega
      *con razon *** *(-- *lo explica en pantalla --)* ✓
*** 3 ***. *** Tres decisiones del propietario ***: *que cuenta la seccion de los
   *toques; *si `data/publicado/` es muerto; *y donde se declara la cobertura de
   *las cadenas que no son Lidl ✓
```

*** Y el limite *** ya no es de herramientas ni de datos ***: *es *** ojo humano en
siete pantallas ***, *y *** tres decisiones ***. *Y eso es un limite mucho mas
pequeño que el que tenia este documento cuando se escribio.* *

| *que* | *que haria falta* |
|---|---|
| *8 estados vacios que dependen de datos* | *API con la lista vacia de verdad* |
| *`Grupo` y `Panel` con datos* | *API, *y una sesion* |
| *`Ajustes`, el error de guardar* | *un guardado fallido, *o sea API* |
| *** El recorrido completo *** | *** API ***: *5 recetas → plan → lista → compra → consumo → diario* |
| *Comparaciones, ofertas y graficas* | *API, *y datos de varias fuentes* |

*** Y NO se impone que todas las tarjetas llenen la pantalla ***: *el criterio es
**legibilidad y utilidad**, *y en algunos casos *** no llenar es lo correcto.*** *

---

## 4. *Lo que NO se hace, y con que criterio*

| *que* | *por que* |
|---|---|
| *Censos de clases sin defecto demostrado* | *** un censo dice DONDE MIRAR, *no SI FALTA ALGO*** |
| *`CocinaModo:96`* | *** no es un error ***: *es `text-tinta-suave`, un mensaje suave* |
| *Forzar `Fallo` en las mutaciones* | *un fallo de accion va en **una linea**, *no en un panel* |
| *Las tres `grid gap-1` de `Panel`* | *** no son raices ***: *son bloques internos* |
| *`min-h-full` para un `return` temprano* | *** no funciona ***: *no resuelve contra un padre `auto`* |

---

## 5. *Las cuatro reglas que hay que leer antes de tocar nada*

```
*** 1 ***. *** Que rama se esta mirando. *** *Sin API **solo se pintan dos**: *
   *los vacios que no dependen de datos *y **los errores**.* *
*** 2 ***. *** Comprobar que la pantalla USA lo que se cambio ***, *con un `git grep`.*
*** 3 ***. *** Contar dos veces. *** *Cuando un censo da **cero**, *hay que preguntarse
   *si el cero es del codigo o del patron.* *
*** 4 ***. *** El puerto y la aplicacion. *** *Puerto comprobado libre, *comprobar que
   *lo servido es Cesta, *y **no matar nunca un proceso que no se arranco uno mismo.*** *
```

*Las dieciseis estan en `COMO-SE-MIDE.md`, *y **todas nacieron de un error mio.*** *

---
---

# ANEXO · *Historico, *rondas 55 a 65*

*** Esto NO es estado vigente ***: *es el registro de **como se llego** a lo de arriba.* *
*Se conserva **separado a proposito**, *porque los errores valen mas que los aciertos.*

## A.1 · *El defecto de la tarjeta de entrar, *medido (ronda 55)*

```
*** `/compra/listas` sin sesion *** pinta la tarjeta de entrar ✓
*** -> *y acaba *** a un tercio de la pantalla ***, *con *** ~600 px de vacio *** debajo ⚠️
*** -> *NO es un estado vacio: *es *** la rama previa a la sesion *** ✓
```

## A.2 · *La estructura que lo impedia, *dicha antes de tocarla (ronda 57)*

```
*** LA CAUSA, *leida en el fichero ***: *`Cesta.tsx:1304` *devolvia *
   *`<div className="*** grid gap-4 ***">`* ⚠️
*** -> *y por eso fallaron *** dos intentos ***: *
   *-- ronda 56: *`grow` en la `Tarjeta` *** no hizo nada *** *(-- no era columna flexible --)*
   *-- ronda 46: *`min-h-full` en un envoltorio *** tampoco *** *(-- no resuelve contra `auto` --)*
```

## A.3 · *Y se cerro (ronda 58)*

```
*** ronda 55 ***: *se midio ✓ · *** ronda 56 ***: *la medida tumbo el intento ✓
*** ronda 57 ***: *se encontro la causa leyendo el fichero, *y se dejo el plan ✓
*** ronda 58 ***: *raiz a `flex min-h-full flex-col` *y `grow` a la `Tarjeta`, *
   *** las dos juntas *** ✓
*** -> *captura: *`b547e089…` -> `4b1c5153…`; *la tarjeta, *de y≈1010 a y≈196-1495 ✓✓✓
```

*** Y lo que costo, *que no se vuelve a pagar ***: *el ancla de texto **no coincide** con
lo que uno escribe.* *La indentacion real era de **4 y 6 espacios** *y se escribieron
**8 y 10** tres veces.* *Se resuelve *** leyendo las lineas exactas con el numero delante.*** *

## A.4 · *Y lo que quedo, *sin adornos (ronda 59, corregido en la 63)*

```
*** LO QUE SE HIZO ***: *17 raices señaladas por el censo entre las rondas 60 y 63:*
   *-- *** 2 arreglos verificados con antes y despues *** *(-- `Cesta` la de entrar, `Unirse` --)*
   *-- *** 3 justificados pero sin poder verificar *** *(-- `Ajustes`, `Avisos`, `Cesta` sin listas --)*
   *-- *** 1 que NO necesitaba nada *** *al medirlo *(-- `Favoritos` --)*
   *-- *** 3 que no eran raices *** *(-- los `grid gap-1` de `Panel` --)*
*** Y LA LECCION ***: *un censo por clases de Tailwind dice *** donde mirar ***, *
   *no *** si falta algo ***.* *El «pendiente» de un censo **no es un defecto** *
   *hasta que una captura lo enseña.*
```
