# B08 · **CORRECCION DE ENCUADRE: el plan SÍ pide la vista de previstos** -- y por eso queda trabajo

*(13 de octubre de 2026. **Y es el hallazgo que impide cerrar el objetivo: no era una invencion mia ni solo una decision del propietario.**)*

## 1. El criterio de B08, literal (`plan:291`)

> *** «Vista de PREVISTOS SEPARADA DEL DIARIO REAL. *Elegir receta versionada, porciones efectivas y comida;
> consultar **snapshot nutricional y cobertura ANTES DE CONFIRMAR**. *Acceso rapido desde **plan/cocina** con
> recibo de consumo y correccion/borrado propios. *** Objetivo OPCIONAL por persona y fecha; ***
> *** GRAFIAS DE REGISTRADO VERSUS PREVISTO VERSUS OBJETIVO, *** *sin totalizar un dia no completo ni colorear
> diagnosticos medicos. *Aceptar **R1=270, media=135**, ausencia de energia con proteina conocida, idempotencia,
> recarga y aislamiento A/B; *** compra nunca genera consumo por si sola. ***» *

## 2. *** Y LO QUE ESTA MEDIDO, clausula por clausula ***

| B08 pide | ¿esta? |
|---|---|
| *«vista de **PREVISTOS** separada del diario real»* | *** ***NO — ausencia medida en tres capas*** *** ⚠️ |
| *«elegir receta **versionada**, porciones efectivas y comida»* | *la receta es versionada (`version`, medido hoy); y el diario tiene `raciones`* |
| ***«snapshot nutricional y cobertura ANTES de confirmar»*** | *** la cobertura SI (diario y `desde-la-compra`); y el snapshot... por comprobar *** |
| *«acceso rapido desde **plan/cocina** con recibo de consumo»* | *** y `desde-la-compra` **es** el recibo*** ✓ |
| ***«OBJETIVO opcional por persona y fecha»*** | *** ***NO*** *** ⚠️ |
| ***«GRAFICAS registrado VERSUS previsto VERSUS objetivo»*** | *** y `Tendencias.tsx` tiene **registrado**; **previsto** y **objetivo**, no*** ⚠️ |
| *«sin totalizar un dia no completo»* | *** SI: `cobertura` y `Diario.tsx:3` («las dos cifras van juntas») *** ✓ |
| *«ni colorear diagnosticos medicos»* | *y `Tendencias.tsx:105` tiene «el hueco, con la palabra»* ✓ |
| ***«compra nunca genera consumo por si sola»*** | *** SI, y con su motivo escrito: `desde-la-compra` *** ✓ |

> *** O sea: *** *** **la mitad de B08 esta, y la mitad no.** *Y **la que falta es la que da nombre al paquete**:
> *** la VISTA DE PREVISTOS, el OBJETIVO, y las GRAFICAS de los tres. *** *
>
> *** Y **no es una invencion mia** *** -- *lo pide **el plan**, con estas palabras: *«vista de previstos»,
> «objetivo opcional», «graficas de registrado versus previsto versus objetivo». *

## 3. *** Y por eso NO se marca el objetivo cumplido *** -- y es la conclusion de la ronda

> *** Lo que yo escribi en las ultimas rondas: ***
> > *«la ausencia del eje de la PREVISION» -- *y **lo trate como una limitacion declarada**, *y **en algun
> > momento como una decision del propietario.** *
>
> *** Y **el plan dice otra cosa**: *** *** «vista de previstos» **es una clausula**, *y **esta sin hacer.** *
>
> *** O sea: *** *** **queda trabajo, y no es ni un permiso ni una invencion: es un paquete del plan a medias.** *
> *Y **la politica de este encargo es clara**: *«no consideres terminado lo que solo abrio una pantalla vacia» --
> *y **aqui ni siquiera hay pantalla.** *

## 4. Y **lo que se puede hacer sin inventar nada**, que es la parte util

```
*** LO QUE YA ESTA, Y SIRVE DE MATERIA PRIMA: ***
  *** el plan ***           -> *`comensales` y `version` por receta* (medido hoy)
  *** la receta ***         -> *`raciones`, e ingredientes con `cantidad`/`unidad`*
  *** el coste ***          -> *`logica/costeReceta.ts`: «nutricion por racion y coste estimado»*
  *** la cobertura ***      -> *`desde-la-compra`: `cobertura: {con_dato, total}` y `sin_dato` con sus nombres*
  *** y la grafica ***      -> *`logica/chispa.ts`: «lo que no se observo no se puede dibujar como si se hubiera
                              observado», *y **sus tres reglas probadas***

*** Y LO QUE FALTA, con su dificultad dicha: ***
  1. *** la vista de previstos ***  -> *sumar `costeReceta` sobre las recetas del plan, **con su cobertura** *
  2. *** el objetivo opcional ***    -> *** y aqui hay que decidir DONDE vive** (una tabla nueva, o preferencia)*
  3. *** y las graficas de los tres ***  -> *y `chispa.ts` **ya sabe** dibujar **tres cosas sin mezclarlas** *
```

> *** Y **la (1) es la unica que se puede hacer sin decidir nada nuevo**: *** *la suma y su cobertura, con el
> patron de `desde-la-compra`. *
>
> *** Y **la (2) necesita una decision**: *** *«objetivo por persona y fecha» es **un dato nuevo**, *y **el
> encargo dice «no inventes... objetivos de salud»** -- *o sea: **la estructura se puede hacer**, *y **el valor
> no se inventa: lo pone la persona.** *
>
> *** Y **la (3) es la mas barata** *** -- *porque **`chispa.ts` ya tiene las reglas** *y **solo le falta la serie
> del previsto.** *

## 5. Y el estado, **con el objetivo SIN cumplir y el motivo escrito**

```
*** B08 · y NO es 4 de 5: le falta una clausula que el plan nombra. ***
  *** lo que esta: *** *version, raciones, cobertura, recibo de consumo, «sin totalizar un dia incompleto»,
     «sin colorear diagnosticos», y «compra nunca genera consumo»*
  *** lo que falta: *** *** la VISTA DE PREVISTOS · el OBJETIVO opcional · y las GRAFICAS de los tres ***
  *** y la materia prima esta, y el patron de la cobertura tambien. *** *
```

> *** Y **NO se marca el objetivo como cumplido** *** -- *porque **queda un paquete del plan a medias**, *y
> **declararlo «hecho» seria exactamente lo que el encargo prohibe: cerrar por cansancio, o por numero de
> rondas, o porque «casi esta».** *
