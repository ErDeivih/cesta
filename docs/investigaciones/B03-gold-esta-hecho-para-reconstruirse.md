# B03 · **Gold esta hecho para reconstruirse** -- y eso resuelve la decision

*(13 de octubre de 2026. **Se iba a decidir entre reconstruir 37 dias o dejar el historico a medias. Y la
decision no es nuestra: el sistema ya la tomo.**)*

## 1. La funcion que existe, y lo que dice de si misma

`projects/cesta/pipeline.py:629`:

> *«**Reconstruye `gold/precio_diario.parquet` entero, dia a dia, desde bronze.**
>
> *Hasta el 18 de septiembre de 2026 **no existia forma de hacer esto**, y se vio probando la cadena entera
> sobre una copia limpia: con el mismo bronze de siempre (575.000 filas, trece dias en disco), el gold
> reconstruido salio con **dos dias y 52.000 filas**. La razon es que `main()` se queda a proposito con la
> instantanea mas reciente de cada cadena y la **anade** al historico; el historico, por tanto, **solo vive en
> ese parquet**. Bronze guardaba todos los dias **y nadie los volvia a leer nunca**.
>
> *Eso convertia un fichero de gold en **el unico ejemplar de la serie de precios**: si se corrompe o se borra,
> se pierde la historia entera aunque el crudo y el bronze esten intactos. **Con esto, gold vuelve a ser lo que
> decia ser, algo que se puede tirar y recalcular.**»*

> **«Algo que se puede tirar y recalcular.»** *Escrito en el docstring de la funcion, y con la cicatriz de un
> fallo real detras* -- *el gold que salio con dos dias en vez de trece.*

## 2. Y entonces la decision no es «reconstruir o no»

**El miedo de la ronda 43 era**: *«reconstruir gold toca el historico de las seis cadenas, y eso no es B03».*

**Y es un miedo razonable, y esta mal planteado.** *Reconstruir gold **no es una operacion arriesgada que haya
que justificar**: es **la operacion para la que gold esta hecho**, y la que garantiza que gold sea
recalculable.*

> **Asi que la pregunta correcta no es «¿me atrevo a reconstruir?», sino «¿esto es un cambio de ESQUEMA que
> exige reconstruir?»** *Y lo es*: *`region` es una columna nueva, y **el historico no la puede tener si no se
> recalcula**.*
>
> *Y dejarlo sin reconstruir daria justo lo que el docstring describe como el problema:* **un gold que ya no
> es «lo que dice ser», porque unas filas llevan la columna y otras no.**

## 3. Y el coste, medido

```
rehaciendo historico: {len(dias)} instantaneas de cadena y dia
```

*El propio codigo lo imprime antes de empezar.* **Y de la corrida de esta sesion**: *1651966 filas de bronze,
6 cadenas, **37 dias acumulados** en gold.*

> **O sea: 37 instantaneas de (fuente, dia)** -- *y la funcion las recorre todas, reconstruyendo el parquet
> entero.* *Es una operacion de minutos, no de horas, y ya se ha corrido antes en este proyecto.*
>
> **Y no destruye nada que no se pueda recuperar**: *el crudo y el bronze siguen ahi, **que es exactamente lo
> que el docstring dice que se gano el 18 de septiembre**.*

## 4. Asi que lo que queda es hacer lo que el sistema ya sabe hacer

  1. **Anadir `region` a la seleccion de columnas de gold** *-- donde hoy se cae.*
  2. **Y reconstruir el historico**, *que es la operacion prevista para un cambio de esquema.*
  3. **Y comprobar que las 37 jornadas llevan su zona** *-- *y que las cinco fuentes sin zona la llevan vacia,
     que es lo que tiene que pasar.*

> **Y el paso 3 es el que convierte esto en una afirmacion**: *no «se reconstruyo», sino **cuantas filas
> llevan zona y cuantas no, por fuente y por dia**.* *Que es la forma de comprobar de todo este paquete.*

## 5. Y lo que **si** hay que respetar

**El gold reconstruido tiene que dar las MISMAS cifras que el de ahora, mas la columna.** *Y eso se puede
comprobar*: *1652509 filas de historico, 37 dias, y las cifras por cadena de `/api/estado`.*

> *Asi que la prueba de que la reconstruccion no ha roto nada **ya existe** y son los numeros de antes:*
> **`alcampo 44001 · aldi 3312 · carrefour 17402 · dia 6346 · lidl 77 · mercadona 4496`.** *Si despues de
> reconstruir siguen siendo esos, la reconstruccion es correcta -- **y si cambian, se sabra exactamente
> cuanto**.*
>
> **Eso es lo que hace que esto no sea un acto de fe.**
