# B13 · **El defecto que el plan avisa: se sirve `Suite`, y `Nav` esta al lado** -- y el «lanzador de tres apps»

*(13 de octubre de 2026. **Segunda ronda de B13. Y el aviso del plan esta confirmado, midiendo.**)*

## 1. El aviso del plan, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:340`:

> **B13 · UX con datos reales y pruebas de recorridos**
>
> *«*** Inventariar rutas y componentes montados, evitar arreglar `Nav` si se sirve `Suite` ***. ...»*

## 2. Y esta confirmado: **los dos existen, y se sirve `Suite`**

```
plataforma/web/app/src/componentes/Nav.tsx      <- existe
plataforma/web/app/src/componentes/Suite.tsx    <- *** y es el que se monta ***

App.tsx:1:   «Las rutas de la suite: LANZADOR, TRES APLICACIONES y las pantallas de [...]»
App.tsx:20:  import { APLICACIONES, *** LayoutSuite ***, aplicacionDe, tituloDeSeccion } from './componentes/Suite'
App.tsx:154: <Route path="/compra" element={<LayoutSuite app="compra">...</LayoutSuite>} />

$ git grep -ln "Suite" -- plataforma/web/app/src/
   App.tsx
   componentes/Suite.tsx
   *** y `Nav.tsx` NO aparece: no lo importa nadie desde App.tsx ***
```

> *** O sea: **el aviso del plan no es una precaucion teorica: *** *hay **dos** componentes, y **el que se sirve es
> `Suite`**.* *** Arreglar `Nav` no cambiaria NADA de lo que ve una persona. ***
>
> *** Y es **la tercera vez** que el plan prohibe un accidente concreto que ya conoce: ***
> ```
> B09:  «no modificar grupos de listas historicas POR ORDINAL»   <- el fallo de B03
> B13:  «evitar arreglar `Nav` si se sirve `Suite`»               <- el componente equivocado
> §8:   «no convertir la recomendacion [de OWASP] en un requisito de token impuesto sin analizar contexto»
> ```
>
> *** Los tres son **la misma clase de aviso**: *** **no arregles lo que parece, arregla lo que corre.** *

## 3. Y `App.tsx:1` dice **lo que el encargo pide**, con las palabras del encargo

> *** «Las rutas de la suite: *** LANZADOR, TRES APLICACIONES *** y las pantallas de [...]» ***
>
> *** Y el encargo pide: *** *«una superapp domestica profesional con *** Compra, Recetas y Calorias SEPARADAS POR
> NAVEGACION *** y conectadas por operaciones explicitas»*. *
>
> *** O sea: **las «tres aplicaciones» y el «lanzador» estan en la primera linea de `App.tsx`** *** -- *y **la
> separacion por navegacion es `LayoutSuite app="compra"` / `app="recetas"` / `app="calorias"`.** *
>
> *** Y `componentes/Suite.tsx` exporta `APLICACIONES`, `aplicacionDe`, `tituloDeSeccion` y `LayoutSuite` *** -- *o
> sea: **la lista de las tres, el resolutor, el titulo, y el marco comun.** *
>
> *** Y eso es **el objetivo del encargo, con nombre y linea** -- *y **lo que B13 pide inventariar**.* *

## 4. Y B13, con dos rondas

```
  1) RUTAS Y COMPONENTES MONTADOS   *** EMPEZADO: *** `App.tsx` monta `LayoutSuite`; `Nav.tsx` existe y
                                    **NO se monta**; hay **tres aplicaciones y un lanzador**
  2) LOS CINCO RECORRIDOS           *POR HACER -- «cinco recetas, compra y diario», con usuarios de prueba*
  3) MOVIL/DESKTOP, TEMAS Y ZOOM    *POR MIRAR*
  4) HTTP RETENIDA/ERROR/CANCELACION/LLEGADA TARDIA   *POR MIRAR*
  5) CAPTURAS CON VERSION/COMMIT/CATALOGO/FECHA/HASH + MANIFIESTO SIN DATOS PRIVADOS   *POR MIRAR*
  6) MEDIR PASOS plan->lista y receta->consumo      *POR MIRAR*
  7) Y LA REGLA                     *** «no cerrar A09 entero con vacios unicamente» ***
```

> *** Y el paso (1) es **el que el plan pone primero, y por una razon**: *** *«inventariar **rutas y componentes
> montados**» -- *porque **sin eso, se puede trabajar una ronda entera sobre un fichero que no se sirve.** *
>
> *** Y **ya esta empezado, y con el resultado del aviso**: *** *** `Suite` se sirve, `Nav` no. ***
>
> *** Y **las otras seis clausulas son de ejecucion** *** -- *capturas, recorridos, zoom, HTTP retenida -- *y **no se
> pueden leer: hay que hacerlas.** *
>
> *** Que es **lo mismo que B12**: *** *«el informe por capacidad» y «los recorridos» **no son lecturas**. *
> **Son las dos cosas que quedan por HACER en este encargo** -- *y **las dos piden datos reales.** *
