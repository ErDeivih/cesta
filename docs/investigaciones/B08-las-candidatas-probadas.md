# B08 · **Las candidatas, probadas**: `objetivo` esta en el frontend y **no en la API** -- y las dos clausulas de la vista siguen sin nombre

*(13 de octubre de 2026. **Septima ronda de B08. Y el mapa de palabras queda hecho.**)*

## 1. Las seis candidatas, contadas

```
$ git grep -li "<palabra>" -- core/ plataforma/api/ plataforma/web/app/src/

  necesidad      3 ficheros
  planificad     4
  calculad      24
  objetivo       8
  prevision      0        <- y esta no aparece en NINGUN sitio
  teoric         3
```

> *** Y `calcular` aparece en 24 ficheros, que es **casi todo** -- *o sea: **no sirve de pista**. Es como buscar
> «dato».*
>
> *** Y `prevision` **no aparece en ningun sitio**: *** *esa candidata esta **muerta**, y **medida**.*

## 2. Y `objetivo` -- la clausula (4) -- esta **en el frontend, y no en la API**

```
core/despensa.py · core/equivalencias.py          <- y probablemente en PROSA, no como concepto
plataforma/api/                                    <- *** NADA ***

plataforma/web/app/src/componentes/Cabecera.tsx
plataforma/web/app/src/estilos.css
plataforma/web/app/src/paginas/Cocina.tsx
plataforma/web/app/src/paginas/Grupo.tsx
plataforma/web/app/src/paginas/Producto.tsx
```

> *** Y eso es **un dato que vale**, aunque no cierre nada: ***
>
>   - **la palabra `objetivo` esta en cinco ficheros del frontend** *-- *y **dos de ellos son de la familia que
>     importa**: `paginas/Cocina.tsx` y `componentes/Cabecera.tsx`;*
>   - **y NO esta en `plataforma/api/`** *-- *o sea: **el frontend la usa, y la API no la nombra**.*
>
> *** Que puede significar **dos cosas**, y no se elige: *** **o que el objetivo se calcula o se guarda con otro
> nombre**, **o que esta en la pantalla sin respaldo en la API** -- *y **la segunda seria el defecto que el
> propietario pidio no dar por bueno**: «no consideres terminado lo que solo abrio una pantalla vacia».*
>
> *** Pero `Cocina.tsx` y `Cabecera.tsx` **no son pantallas vacias**: son **las que el plan pide** («acceso rapido
> desde plan/cocina»). *** *Asi que **lo mas probable es que la API lo llame de otra forma** -- y **no se dice
> cual**. ***

## 3. Y `necesidad` -- la palabra del plan -- esta en **tres ficheros, y ninguno es el diario**

```
core/off.py · core/waf.py · y un tercero
```

> *** Y `waf.py` **no es de nutricion**: *** *es **el modulo del WAF**, y «necesidad» ahi **es otra cosa**.*
>
> *** Quinta vez que la misma palabra significa cosas distintas en el mismo proyecto. ***

## 4. Y entonces B08 tiene **dos clausulas sin nombre, y el mapa de palabras hecho**

```
  1) PREVISTO != REGISTRADO    *** SIN NOMBRE. Probadas y descartadas: `previsto` (nada), `previa` (es de
                               compra), `analisis` (es de precios), `prevision` (no existe),
                               `necesidad` (en waf/off, otro sentido), `calculad` (24 ficheros: no sirve) ***
  4) EL OBJETIVO Y LAS GRAFICAS *** SIN NOMBRE EN LA API. `objetivo` esta en CINCO ficheros del frontend,
                               incluidos `Cocina.tsx` y `Cabecera.tsx`, y en NINGUNO de la API ***
```

> *** Y lo que queda por probar, **dicho con precision**: ***
>
>   - **para la (1)**: *el nombre **en español neutro** que el proyecto usa para «lo que el plan calcula que vas a
>     comer» -- *y **las candidatas probadas estan agotadas**, asi que **hay que mirarlo por OTRO camino**: **leer
>     `plataforma/api/diario.py`**, que es **el modulo hermano**, y **ver que funciones tiene**;*
>   - **para la (4)**: *lo mismo -- **y ahi hay una pista concreta**: *`Cocina.tsx` **usa** `objetivo`, **y hay que
>     ver de donde lo saca**.*
>
> *** O sea: **se acabo el camino de las palabras; empieza el de leer el fichero hermano.** *** *Que es **exactamente
> el paso (2) del metodo**, y **por eso el metodo tiene cinco pasos y no uno**.*
