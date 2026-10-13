# B10 (y B11) · **El mapa** -- y B11 trae la doctrina aplicada a las graficas

*(13 de octubre de 2026. **Lo siguiente por el plan. Y el paquete de graficas dice lo mismo que B06.**)*

## 1. El criterio de B10, literal

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:312`:

> **B10 · Compra profesional para familias**
>
> *«Favoritos/necesito/en carrito/comprado **distinguidos**, **listas de casa y personales**, **texto libre**, **orden
> por pasillos**, **busqueda con marca/formato/EAN y filtros utiles**. **Paginacion fijada a version/cursor** y
> **feedback sobre cambios del catalogo**. **Historico de gasto pagado, ahorro demostrable frente a referencia
> elegible** y **estimaciones parciales con lineas que faltan**. **Presupuesto opcional y coste de viajes
> separados**. **Reintento/offline/concurrencia no pierden cantidades ni revocaciones**.»*

## 2. Y desglosado, son seis cosas

```
1) LOS ESTADOS, DISTINGUIDOS   -- favoritos / necesito / en carrito / comprado
2) LAS LISTAS Y EL ORDEN       -- listas de casa Y personales · texto libre · ORDEN POR PASILLOS
3) BUSCAR Y FILTRAR            -- con marca/formato/EAN, y filtros utiles
4) LA PAGINACION               -- *** «fijada a version/cursor» *** -- *no por numero de pagina*
                                 y **feedback sobre cambios del catalogo**
5) EL GASTO Y EL AHORRO        -- historico de gasto PAGADO · *** ahorro DEMOSTRABLE frente a referencia
                                 ELEGIBLE *** · y *** «estimaciones parciales CON LINEAS QUE FALTAN» ***
                                 · presupuesto OPCIONAL · *** y «coste de viajes SEPARADOS» ***
6) Y LA DUREZA                 -- *** «reintento/offline/concurrencia NO PIERDEN cantidades ni
                                 revocaciones» ***
```

> *** Y la (5) y la (6) son **las dos que ya tienen respuesta en el proyecto**, por lo que se ha leido: ***
>
>   - **«estimaciones parciales con lineas que faltan»** *-- *es **`cobertura`**: *el proyecto **ya dice cuantas
>     lineas faltan** en vez de dar un total incompleto como bueno (B06, `cobertura_sobre_comida`);*
>   - **«no pierden cantidades ni revocaciones»** *-- *es **`ON CONFLICT (id) DO UPDATE` + `borrado_en` + 
>     `COALESCE`** (B05): *la cantidad **no se pierde** porque **el conflicto pisa con contenido**, y **la
>     revocacion no se pierde** porque **el borrado es un `borrado_en`, no un `DELETE`**.*
>
> *** Y **«coste de viajes separados»** conecta con el encargo: *** *«no inventes ... **costes de viajes**» -- *y el
> plan **separa** el coste del viaje del coste de la compra **en vez de sumarlo**.* ***

## 3. Y de propina, el criterio de B11 -- **que es B06 aplicado a las graficas**

`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:321`:

> **B11 · Graficas utiles, no decorativas**
>
> *«Gasto pagado semanal/mensual por tienda y categoria; precios del mismo articulo; distribucion y comparacion de
> coste de cesta cubierta; plan y consumo por comida; nutrientes con cobertura; sobrantes y despensa **solo con
> movimientos conocidos**. *** **Cada grafica declara medida, unidad, universo, periodo, fuente y version.** ***
> Huecos [...]»*

> *** Y esa ultima frase es **la respuesta al encargo entero**, aplicada a un dibujo: ***
>
> ```
> «Cada grafica declara MEDIDA, UNIDAD, UNIVERSO, PERIODO, FUENTE y VERSION»
>   -> MEDIDA y UNIDAD     = lo que B06 llama «unidad_canon» («no es opcional»)
>   -> UNIVERSO            = *** lo que `alimentos.py` dice: «decir un porcentaje sin haber mirado el universo
>                             es inventarlo» ***
>   -> PERIODO             = la ventana (`DIAS_DE_VENTANA`, y `rango(desde, hasta)`)
>   -> FUENTE              = *** `fuente_dato` ***
>   -> Y VERSION           = *** la version de la receta y la del dato ***
> ```
>
> *** O sea: **una grafica que no dice esas seis cosas es una grafica que no se puede leer** *** -- *y **el plan lo
> pone como criterio de aceptacion de la pantalla**: **«utiles, no decorativas»**.*
>
> *** Y es **la decimoctava vez** que aparece la doctrina -- *y **la primera en que se exige en la SALIDA** (una
> grafica) **y no en la entrada** (un dato). ***

## 4. Y el orden de trabajo, el mismo, ya probado cuatro veces

```
  1) ls de la zona                        -- `core/almacen*`, `plataforma/api/almacen.py` (leido: 1230 lineas),
                                            `plataforma/web/app/src/paginas/`, `core/pasillos*` si existe
  2) LEER el fichero que el TITULO nombra: *** el titulo es «Compra profesional para familias» *** --
     *y **lo mas parecido a un nombre es `almacen`** (que ya se leyo **su `anade_linea`** en B05, y **no sus
     otras funciones**)*
  3) LOS NOMBRES DE LOS ENSAYOS            -- `test_almacen*`, `test_listas*`, `test_pasillos*`, `test_g05*`
  4) COMPARAR los que hacen lo mismo
  5) y grep al final, con las palabras del codigo

  Y NO DECIR NUNCA: «no existe», «y nada mas», «hay que construirlo», «ya esta» sin su cita
```

> *** Y el paso (2) tiene **una ventaja y una advertencia**: ***
>
>   - **ventaja**: *`almacen.py` **ya se abrio** en B05 -- *pero **solo `anade_linea`**;*
>   - **advertencia**: *«compra profesional para familias» **tiene seis cosas**, y **`almacen.py` es solo
>     una de las zonas** -- *las listas, las busquedas, los pasillos y el gasto **pueden estar en otros
>     ficheros**, y **no se supone cuales**.*
