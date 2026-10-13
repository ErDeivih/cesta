# B03 · **Dónde se escribe `grupos.parquet`**: el emparejador, y lo que queda por medir

*(13 de octubre de 2026. **El ultimo eslabon que faltaba localizar, y el relevo exacto de B03.**)*

## 1. Lo que se ha localizado

**`grupos.parquet` no lo escribe el pipeline:**

```
projects/cesta/pipeline.py:837
    # antes deja fuera `grupos.parquet` y `enlaces.parquet`.
```

> **«Antes deja fuera»**: *o sea que **los escribe otra cosa**, y el pipeline los respeta.* *Es el
> **emparejador** -- el paso que `run.py:300` describe como «aqui se acaba todo lo que escribe gold -- el
> emparejador».*

*Y esta declarado como fichero publicado:*

```
core/publicacion.py:42    FICHEROS = ["grupos.parquet", "enlaces.parquet", ...]
core/manifiesto.py:47     PUBLICADOS = ["grupos.parquet", ...]
```

*Y se lee en tres sitios mas: `core/embeddings.py:323`, `plataforma/api/catalogo.py:98` (la vista) y `:58` (el
sello de version).*

## 2. Asi que la cadena entera, para quien retome

```
la web de Lidl        79 fichas con precio regional
bronze                region 79/79      HECHO
silver                region 79/79      HECHO (ya estaba: with_columns es aditivo)
gold/precio_diario    region 77/77      HECHO (historico rehecho)
vista `diario`        region 77/77      HECHO
-------------------------------------------------------------------------------------------
EL EMPAREJADOR  ->  gold/grupos.parquet        <- AQUI HAY QUE ANADIR `region`
vista `grupos`        (SELECT *, la expone sola)
donde_comprar         (lee grupos; la columna va AL FINAL del SELECT)
```

**Y lo que falta esta en **una** casilla: el emparejador.**

## 3. Y las cuatro cosas que ya estan medidas, para que esa casilla no se aborde a ciegas

  1. **La decision de identidad: LA ZONA ENTRA EN EL `grupo_id`.** *Medido: **8746 grupos ya cruzan fuentes**
     (135 abarcan cinco), asi que cruzar zonas es la misma forma un paso mas alla.* **Anadir la columna sin
     cambiar la identidad daria grupos con dos zonas y el mismo id -- peor que no tenerla, porque pareceria
     resuelto.**
  2. **La forma de la columna en el `SELECT`: AL FINAL.** *Probado en la ronda 55: **el error no fue de
     indices**.*
  3. **Por que fallo el intento de la ronda 55: porque empece por `donde_comprar`.** *`donde_comprar` lee
     `grupos`, no `diario`, y `grupos` no tiene la columna.*
  4. **Y que hoy NO hay ningun grupo con dos zonas** *-- solo Lidl declara zona, y sus 77 filas son la `28` --*,
     **asi que el cambio se puede hacer sin migrar nada**: *cuando se anada, no habra ni una fila que
     reinterpretar.*

> **Esa cuarta es la que hace que este sea el momento barato.** *Manana, con dos fuentes declarando zona, el
> mismo cambio obligaria a **decidir que hacer con los grupos ya mezclados**.*

## 4. Y lo que **no** se ha hecho, y por que

**No se ha tocado el emparejador.** *Y no por prudencia: por **falta de la ultima medida**.*

> *Lo que hay que mirar antes de escribir una linea es*: **como calcula el emparejador el `grupo_id` hoy.**
> *Si es un `hash` o un contador por raiz de nombre, **meter la zona dentro es una linea**; si es el resultado
> de `agrupar_enlaces` (`core/matching`, citado en `catalogo.py:782`), **hay que decidir donde entra**.*
>
> **Y eso no se puede suponer**: *es exactamente el error que se ha cometido cuatro veces en este paquete.*

## 5. Estado de B03, con el relevo en una linea

```
TODO HECHO:  captura · bronze con zona (79/79) · cobertura y contador · silver · gold (historico rehecho)
             · la vista diario · /api/estado · la pantalla · Y CORRE EN LA PASADA DIARIA
             · club, fechas, nutricion y ausencias probados
PENDIENTE:   LA ZONA EN LA COMPARACION
             -> el fichero: el emparejador, que escribe gold/grupos.parquet
             -> la identidad: la zona entra en el grupo_id
             -> y la ultima medida antes de escribir: como calcula hoy el grupo_id
```

*Cinco documentos de esta serie -- `B03-estado-y-la-zona-en-la-comparacion`, `...intentado-y-revertido`,
`...la-comparacion-lee-grupos-no-diario`, `...grupos-medido-la-cadena-hasta-la-comparacion` y
`...la-zona-entra-en-la-identidad-del-grupo` -- son, juntos, el camino hasta aqui **con sus intentos fallidos
incluidos**, que es lo que impide repetirlos.*
