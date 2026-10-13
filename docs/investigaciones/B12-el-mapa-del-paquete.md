# B12 (y B13) · **El mapa** -- y B12 dice la regla que esta sesion ha seguido sin saberla

*(13 de octubre de 2026. **Lo siguiente por el plan. Y el paquete de REA no pide estudiar binarios.**)*

## 1. El criterio de B12, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:331`:

> **B12 · Estudio de referencias con REA y documentacion**
>
> *«**Ver seccion 8: una funcion por investigacion.** **Priorizar consolidar el menu, porciones/diario y flujos de
> lista.** **No estudiar un binario enorme por usar REA.** **Aplicar ideas con codigo propio y disenar la prueba
> equivalente en Cesta.** *** Una funcionalidad anunciada en una web no acredita su mecanismo interno. ***»*

## 2. Y desglosado, son cinco reglas -- y **cuatro son «no hagas»**

```
1) UNA FUNCION POR INVESTIGACION      -- y **la seccion 8** tiene el como
2) Y EL ORDEN DE PRIORIDAD            -- *** consolidar el MENU, PORCIONES/DIARIO y FLUJOS DE LISTA ***
3) NO ESTUDIAR UN BINARIO ENORME      -- «por usar REA»: *la herramienta no justifica el objetivo*
4) CODIGO PROPIO + PRUEBA EQUIVALENTE -- *** «la prueba equivalente EN CESTA» *** -- *no copiar software ajeno*
5) Y LA REGLA QUE LO CIERRA           -- *** «una funcionalidad anunciada en una web NO ACREDITA su
                                         mecanismo interno» ***
```

> *** Y la (5) es **la regla de esta sesion entera**, y no la habia leido: ***
>
> *** «Una funcionalidad **anunciada** en una web **no acredita su mecanismo interno**.» ***
>
> *** O sea: **que un README diga que hace algo no es prueba de como lo hace** *** -- *y **es exactamente** la razon
> por la que **esta sesion ha leido el codigo en vez de la documentacion** para cada clausula:*
>
> ```
> «Lidl esta integrado»        -> y habia que ver SI, y con que alcance (B02/B03)
> «las graficas declaran...»   -> y habia que ver `logica/chispa.ts` (B11)
> «el oraculo es completo»     -> y su docstring decia que NO cubre `umbral` (B09)
> «idempotencia y consistencia» -> y estaba en `ON CONFLICT` + `LEAST`/`GREATEST` + `traspaso` (B05/B10)
> ```
>
> *** Y **el propio plan lo pide dos veces**: *** *aqui («no acredita su mecanismo interno») **y en el encargo**
> («documentacion **y observacion** para UX»).*
>
> *** Y la (4) es **la misma idea desde el otro lado**: *** *** «aplicar ideas con **codigo propio** y diseñar la
> **prueba equivalente** en Cesta» *** -- *o sea: **entender el mecanismo, y volver a escribirlo**, *no **traerlo**. *
> ***

## 3. Y la (2) dice **por donde empezar**, y son tres cosas -- y las tres ya estan leidas

```
B12 PRIORIZA:  «consolidar el MENU, PORCIONES/DIARIO y FLUJOS DE LISTA»
   -> el MENU           *** B05/B10: `planificar`/`plan`/`quitar_del_plan`/`escala` ***
   -> PORCIONES/DIARIO   *** B08: `apunta` (que rechaza `compra`), `de_ficha`, `_cobertura` ***
   -> FLUJOS DE LISTA    *** B04/B05/B10: los dos puentes, `anade_linea`, `LEAST`/`GREATEST` ***
```

> *** Y las tres son **las que esta sesion ha mirado mas a fondo** *** -- *o sea: **el orden de esta sesion y el del
> plan coinciden**, *y **eso no es casualidad**: *las tres son **donde el propietario puso su restriccion** («afecta a
> AMBOS puentes»).*

## 4. Y de propina, el criterio de B13 -- que trae un **defecto concreto** por nombre

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:338`:

> **B13 · UX con datos reales y pruebas de recorridos**
>
> *«*** Inventariar rutas y componentes montados, evitar arreglar `Nav` si se sirve `Suite` ***. Recorrer cinco
> recetas, compra y diario con usuarios de prueba, no cuentas reales. Movil/desktop, temas y zoom, HTTP
> retenida/error/cancelacion/llegada tardia. Capturas con version de frontend/API, commit, catalogo, fecha y hash,
> mas manifiesto sin datos privados. Guardar evidencia referenciable sin commitear nutricion personal. Medir pasos
> para plan->lista y receta->consumo; corregir mensajes, no tolerar fallos porque haya publicacion concurrente.
> *** No «cerrar A09 entero» con vacios unicamente ***.»*

> *** Y la primera frase **es un defecto con nombre y apellidos**: ***
>
> *** «Inventariar rutas y componentes montados, *** EVITAR ARREGLAR `Nav` SI SE SIRVE `SUITE` ***.» ***
>
> *** O sea: **hay dos componentes que podrian parecer el mismo**, *y **arreglar el que no se sirve** **no cambia
> nada** -- *y **el plan lo dice antes de que ocurra**, porque **ya ocurrio** o **se vio venir.** *
>
> *** Que es **la misma clase de aviso que «no modificar grupos historicos por ordinal»** (B09): *** *** el plan
> prohibe el accidente concreto que ya conoce.** *
>
> *** Y la ultima frase -- «no "cerrar A09 entero" con vacios unicamente» -- es **el encargo, otra vez**: ***
> *«**no consideres terminado lo que solo abrio una pantalla vacia**».*
>
> *** Tercera vez que el plan escribe esa regla, y las tres con palabras distintas: ***
> ```
> el encargo:  «no consideres terminado lo que solo abrio una pantalla vacia»
> B13:         «no "cerrar A09 entero" con vacios unicamente»
> y B11:       *** «utiles, no decorativas» *** (que es lo mismo, aplicado a un dibujo)
> ```

## 5. Y el orden de trabajo para B12, que **no es el de los otros paquetes**

```
  1) LEER la seccion 8 del plan        *** -- que es donde esta el COMO de REA, y NO se ha leido ***
  2) Y elegir UNA funcion              -- de las tres que el plan prioriza (menu, porciones/diario, listas)
  3) Ver si hace falta artefacto       -- *** y el plan ya dice que NO, si el binario es enorme ***
  4) Y aplicar con CODIGO PROPIO       -- *** y diseñar la prueba equivalente en Cesta ***
```

> *** Y el paso (1) es **el unico sitio del encargo donde el plan remite a si mismo** *** -- *«**ver seccion 8**» -- *y
> **no se ha leido.** *
>
> *** Y mientras no se lea, **no se sabe que pide REA exactamente** *** -- *y **no se supone.** *
