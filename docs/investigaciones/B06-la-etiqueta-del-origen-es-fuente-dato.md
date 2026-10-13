# B06 · **La etiqueta del origen existe y se llama `fuente_dato`**, con lista blanca y su `ValueError`

*(13 de octubre de 2026. **Quinta ronda de B06. Y cierra la clausula que quedaba a medias.**)*

## 1. Lo que hay (`core/diario.py`)

```
l52:   fuente_dato TEXT NOT NULL,                     <- LA COLUMNA, y NO admite nulos
l136:  ... fuente_dato: str = DESC...                 <- y el defecto es una de las fuentes conocidas
l151:  if fuente_dato not in FUENTES:
l152:      raise ValueError(f"fuente de dato desconocida: {fuente_dato...}")
l172:  "fuente_dato": fuente_dato, "nota": nota
l195:  "hidratos_g, fuente_dato, nota, creada, propietario
```

> *** Y `FUENTES` es una lista blanca, con `ValueError` si no estas dentro. ***
>
> *Que es **lo mismo** que el proyecto hace con el estado de una linea, con la unidad, y con el ambito: **si el
> valor no es de los conocidos, se levanta** -- *no se guarda «otro» ni se adivina.*

## 2. Y es el «nativo / enriquecido / manual» de B06

```
B06 PIDE                                     Y AQUI ESTA
  «Campo NATIVO / ENRIQUECIDO / MANUAL»        *** `fuente_dato TEXT NOT NULL` *** + `FUENTES` + `ValueError`
```

> *** Y `NOT NULL` es la mitad de la decision: *** *no se puede guardar un dato **sin decir de donde salio**.*
>
> *Que es **exactamente** lo que la clausula (2) pide -- *y **con la forma fuerte**: no «conviene etiquetarlo»,
> **sino que no se puede guardar sin etiqueta**.*
>
> *** Y es la TERCERA vez en B06 que la respuesta del proyecto es **una restriccion del esquema**, no una
> convencion del codigo ***: *`cantidad` que admite NULL a proposito, `id uuid PRIMARY KEY` que impide la fila
> repetida, y ahora `fuente_dato NOT NULL` **que impide guardar sin origen**.*
>
> *** La forma fuerte de una regla: no una promesa, una imposibilidad. ***

## 3. Y aparece **la misma doctrina por octava vez**, ahora como restriccion

```
  1) la columna `cantidad` de la despensa    ->  NULL = «no se sabe», que no es 0
  2) sin_precio                              ->  «no se sabe el precio», que no es gratis
  3) diario.fuente_dato                      ->  de donde viene el dato          <- *** NOT NULL ***
  4) COALESCE en anade_linea                 ->  «no llega» no es «llega vacio»
  5) core/alimentos.py                       ->  «mezcla», que no es ni «si» ni «no»
  6) test_un_cero_no_se_confunde_con_no_haber_dato
  7) unidad_canon                            ->  sin unidad, las cifras NO SON COMPARABLES
  8) y `FUENTES` + `ValueError`              ->  un origen que no es de los conocidos SE LEVANTA
```

> *** Ocho sitios, y los ocho dicen lo mismo: *** **si el valor no se sabe, no se inventa un valor** -- *se guarda
> **que no se sabe**, o **se levanta**.*
>
> *** Y es, en este proyecto, **la unica regla que aparece en ocho modulos distintos** -- *que es mas de lo que
> cualquier otra convencion del encargo consigue.* ***

## 4. Y B06, con cinco rondas, tiene **cuatro de sus cinco** con respuesta

```
  1) EL INVENTARIO DE CAMPOS        LOCALIZADO -- 21 ensayos, campo por campo
  2) NATIVO / ENRIQUECIDO / MANUAL  *** HECHO: *** `fuente_dato NOT NULL` + `FUENTES` + `ValueError`
                                     (y `derive.enriquecer` produce el enriquecido)
  3) AUSENTE / NO APLICABLE / ...   «ausente» y «error» con ensayo; «no aplicable» en `core/alimentos.py`;
                                     *** «no publicado» y «pendiente» POR MIRAR ***
  4) LA COLA CON PRESUPUESTO        *** POR MIRAR *** -- «no 88 horas de fichas sin prioridad
                                     ni pedir cada detalle estable cada dia»
  5) Y EL HISTORICO DE FICHA        el historico existe y se usa (`precio_diario`, ventanas);
                                     *** «no mezclar precio actual con detalle obsoleto» POR MIRAR ***
```

> *** Y lo que queda -- las dos «por mirar» y una media -- es TODO lo mismo: ***
>
>   - **con que prioridad se pide un campo** (la cola),
>   - **y que se guarda del pasado** (el historico, sin mezclar).
>
> *** Que es una sola pregunta: **cada dato, de cuando es.** *** *Y con `fuente_dato` ya resuelto, B06 tiene **la
> mitad «de donde» contestada** -- *y **la mitad «de cuando», entera por mirar**.*
>
> *** Y esa mitad esta, casi con seguridad, en `core/publicacion.py` y `core/manifiesto.py` *** -- *los dos
> ficheros de la lista de doce **que siguen sin abrirse**, y que son **el recibo y la version de una publicacion**:
> *o sea, **exactamente «de cuando es este dato»**.*
