# B08 · **«Objetivo» en la pantalla es una etiqueta de interfaz** -- y la clausula (4) queda **sin encontrar, dicha como tal**

*(13 de octubre de 2026. **Novena ronda de B08. Y la segunda clausula que no aparece.**)*

## 1. Lo que se encontro

```
plataforma/web/app/src/paginas/Cocina.tsx

  ... <button onClick={() => descargar('comidas-cesta.json', ...)} ...
  ... <p className="text-sm text-tinta-suave">Calculos orientativos a partir de lo que int[roduces]...</p>
```

> *** O sea: en `Cocina.tsx`, lo que aparece alrededor de «objetivo» **es interfaz**: *** *un boton de descarga de
> `comidas-cesta.json`, y una **nota al pie** que dice que **los calculos son orientativos**.*
>
> *** Y eso, **por si solo, no es el objetivo de calorias**: *** *no hay `objetivo_kcal`, ni una meta, ni una fecha.*
> **Hay una etiqueta y un aviso.***

## 2. Y el aviso **si** dice algo que importa

> *** «Calculos ORIENTATIVOS a partir de lo que introduces» ***
>
> *Que es **la misma familia** que «ni colorear diagnosticos medicos» -- *y que la doctrina: **el numero es
> orientativo, y se dice.***
>
> *** Y `orientativo` es, probablemente, **la palabra que el proyecto usa** *** *-- *y **no se ha probado**.*

## 3. Y entonces B08 tiene **dos clausulas sin encontrar**, y las dos dichas

```
  1) PREVISTO != REGISTRADO     *** el proyecto SEPARA, y empieza por el COSTE (`_con_precios`, G12/222);
                                el eje de la NUTRICION esta NOMBRADO ahi ***
  4) EL OBJETIVO Y LAS GRAFICAS *** NO ENCONTRADO. `objetivo` esta en cinco ficheros del frontend y en
                                ninguno de la API, y en `Cocina.tsx` es una ETIQUETA DE INTERFAZ ***
```

> *** Y lo que queda por probar, **dicho**: *** **`orientativo`**, *que **acaba de aparecer** en ese mismo texto, y
> que **es la palabra con la que el proyecto se protege de las cifras que no puede garantizar**.*
>
> *** Y `objetivo` en los otros cuatro ficheros del frontend -- `Cabecera.tsx`, `Grupo.tsx`, `Producto.tsx` y
> `estilos.css` -- **no se ha mirado**: *** *y **`Cabecera.tsx` es una barra de navegacion**, que es donde vive un
> texto legal o un aviso, mas que una meta.*

## 4. Y esto cierra el mapa de B08, con **lo que hay y lo que no se ha encontrado**

```
HECHO, con nombre y linea:
  2) EL SNAPSHOT Y LA COBERTURA  -- `de_ficha(producto, gramos)` · `_cobertura(filas, columna, total)`
                                    · `_trae_dato(fila)`
  3) EL RECIBO Y SU DESHACER     -- `apunta(...)` (rechaza `compra`) · `borrar(con, propietario, entrada_id)`
                                    · y LAS DOS IDEMPOTENCIAS (`clave_operacion` + `_el_mismo_reintento`)
  5) Y LA ACEPTACION             -- 15 ensayos en `test_g01_diario_aceptacion.py` y 6 en `test_procedencia_diario.py`

EXPLICADO, con su docstring:
  1) LA SEPARACION               -- existe, y **empieza por el coste**: `_con_precios`, G12/222.
                                    *El eje de la nutricion esta nombrado en el mismo sitio.*

NO ENCONTRADO, y dicho como tal:
  4) EL OBJETIVO Y LAS GRAFICAS  -- `objetivo` es una etiqueta de interfaz en `Cocina.tsx`;
                                    *** no aparece en la API, y no se ha encontrado como meta por persona y fecha ***
```

> *** Y las nueve rondas de B08 dejan, ademas de las respuestas, **el mapa de palabras mas completo de la
> sesion**: *** *siete candidatas, **seis descartadas midiendo**, y **una septima que acaba de aparecer**
> (`orientativo`).*
>
> *** Y es un mapa **util para lo que queda**: *** *`B09` va de **identidad**, y ya se sabe que en este proyecto
> **la misma palabra significa cosas distintas en sitios distintos** -- *`previa`, `fuente`, `manual`, `necesidad`,
> `objetivo`, `calculad`.*
>
> *** Que es, contado seis veces, **una sola advertencia**: *** **no buscar con la palabra del plan; buscar con la
> del codigo.** *** Y cuando no aparece, **leer el fichero que el titulo nombra.** ***
