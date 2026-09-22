# Probar de verdad lo arreglado el 18 de septiembre

Sesion limpia, tarde del 18. El encargo era sencillo: coger todo lo cambiado en
los ultimos dias y **ejecutarlo**, no releerlo. Lo que sigue es lo que aparecio
al hacerlo, en el orden en que aparecio.

Resumen: las 323 pruebas pasan y el linter esta limpio, pero la tanda destapo
**tres cosas nuevas**, una de ellas estructural.

---

## 0. Como se prueba sin tocar los datos de casa

El repositorio vive en `F:\aprendizaje\scrap` y ahi estan los datos buenos. Todo
lo de abajo se ejecuta contra **copias**:

```
SCRAP_DATA=<carpeta aparte> python -m projects.cesta.pipeline
```

`core/config.py` ya respeta `SCRAP_DATA`, asi que la cadena entera se puede
correr sobre un bronze copiado sin rozar `data/gold`. Merece la pena dejarlo
escrito porque es la unica forma honesta de probar el pipeline: sobre los datos
reales, un fallo de la prueba te deja sin catalogo.

Aviso practico: no se copia `data/externo/` entera. `food.parquet` son **7,85 GB**
(el volcado mundial de Open Food Facts) y llena el disco de la copia antes de
empezar. Solo hace falta `off_es.parquet`, 25 MB.

---

## 1. GRAVE — el historico de precios no se podia reconstruir

Se copio el bronze completo -- **575.000 filas, trece dias, cinco cadenas** -- a
una carpeta limpia y se lanzo la cadena entera desde cero. El resultado:

```
  silver: 52575 filas de 5 cadenas
  gold:   52359 filas de historico, 2 dias acumulados
```

**Dos dias.** Con trece dias de bronze en disco.

No es un bug del pipeline: es como esta escrito. `pipeline.main()` se queda a
proposito con la instantanea **mas reciente** de cada cadena, y `a_gold()` la
**anade** a `gold/precio_diario.parquet`. El historico, por tanto, no se calcula
nunca: se acumula. Solo existe en ese fichero.

Eso rompe la promesa de la arquitectura medallion, que es justamente que las
capas de abajo se puedan tirar y recalcular. Aqui el crudo y el bronze guardaban
todos los dias y **nadie los volvia a leer jamas**. Si ese parquet se corrompe,
se borra o se queda a medias, se pierde la serie de precios entera aunque el
bronze este intacto. Y el problema crece solo: dentro de un ano son 365 dias en
un unico ejemplar.

### Arreglo

`projects/cesta/pipeline.py` gana `rehacer_historico()`, con su entrada por
linea de ordenes:

```
uv run python -m projects.cesta.pipeline --rehacer-historico
```

Recorre bronze por pareja (cadena, dia), pasa cada instantanea por `a_silver` y
concatena. Un dia ilegible se salta con un aviso en vez de llevarse por delante
a los otros doce. Medido sobre el bronze real:

```
historico rehecho: 572202 filas, 13 dias, 5 cadenas
```

Trece dias, los mismos que hay en disco.

### Lo que enseno la comparacion

Contrastar el historico acumulado (593.509 filas) con el rehecho (572.202) no da
cero, y la diferencia es interesante:

| dia | cadena | acumulado | rehecho | dif |
|---|---|---:|---:|---:|
| 2026-09-17 | *las cinco* | = | = | **0** |
| 2026-09-16 | dia | 5.412 | 5.362 | −50 |
| 2026-09-16 | mercadona | 4.320 | 4.308 | −12 |
| 2026-09-16 | aldi | 1.924 | 1.914 | −10 |
| … | … | … | … | … |
| 2026-09-18 | alcampo | 20.559 | **0** | −20.559 |

No hay filas duplicadas en el historico (se comprobo: cero duplicados por
cadena+producto+dia). Las diferencias pequenas y constantes son otra cosa: el
dia mas reciente cuadra **exacto** y los anteriores no. La razon es que cada dia
del historico lo escribio **la version del codigo que habia ese dia**. Trece
dias de historico son trece versiones de la transformacion. Hoy el codigo es
algo mas estricto decidiendo que precio es comparable, y por eso deja fuera unas
pocas decenas de filas por cadena y dia que en su momento entraron.

Es un buen argumento a favor de poder rehacer el historico: una serie temporal
cocinada por trece recetas distintas no es del todo una serie temporal.

---

## 2. 20.559 filas de alcampo sin bronze en su sitio

En `gold` hay **20.559 filas de alcampo fechadas el 18 de septiembre** y en
`data/bronze/fuente=alcampo/` la ultima carpeta es la del **17**.

Reconstruccion de lo que paso, por marcas de tiempo:

| hora (UTC) | que |
|---|---|
| 08:26 | el colector de alcampo termina bien: 20.571 productos, 0 errores (`runs.csv`) |
| ~08:30 | el pipeline de la ejecucion diaria escribe silver y gold con fecha 18 |
| **08:52** | se **aparta** el bronze del 18 a `data/debug/descartados/alcampo-2026-09-18-sin-frescos`, siguiendo `OPERACION.md`, por venir sin la rama Frescos |
| 09:02 | un segundo pipeline relee bronze, ya sin el 18, y rehace silver desde el 17 |

**Nadie borro nada.** Durante un dia entero se dio por perdida esa particion y se
estuvo conjeturando quien la habria borrado; estaba enterita en descartados
-- 20.571 filas, comprobado --, apartada esa misma manana a proposito y bien, que
es exactamente lo que manda el procedimiento. **Bronze no se borra nunca: si no
esta en su sitio, es que lo apartaron.**

Lo que si es verdad, y es lo que importa: **nada en el sistema se entero de que la
carpeta ya no estaba**, ni para bien ni para mal. El resumen del dia dijo "13 dias
acumulados" tan tranquilo, con veinte mil filas de una captura que se acababa de
rechazar. Un procedimiento de recuperacion que aparta el bronze y el silver pero
deja las filas en gold es un procedimiento incompleto, y no habia nada que lo
dijera.

### Arreglo

`projects/cesta/resumen.py` gana `dias_huerfanos()`, que cruza los pares
(cadena, fecha) del historico con las carpetas de bronze **y con las de
descartados**, porque las dos situaciones se parecen y no son la misma:

```
  historico: 593509 filas, 13 dias acumulados
  nota: 20559 filas de alcampo del 2026-09-18 vienen de una captura apartada
        (sin frescos); el bronze esta en data/debug/descartados
```

Si no aparece ni en bronze ni en descartados, entonces si es un AVISO en
mayusculas: esas filas no se pueden recalcular desde nada.

Con una salvaguarda: si no hay bronze **ninguno** no se dice nada. La plataforma
monta `gold` sin `bronze`, y un aviso que acusa de huerfano a todo el historico
cada vez que alguien abre una copia de solo-lectura es un aviso que se aprende a
ignorar en dos dias.

### Y el cinturon que faltaba

La conjetura duro un dia porque **nada en el codigo decia que borrar bronze no
fuera posible**. Ahora lo dice:

- `storage.CAPAS_INTOCABLES = ("bronze", "gold")` y `storage.comprueba_borrable()`,
  que revienta con `BorradoProhibido` si una ruta cae dentro de esas capas.
  `limpiar.py` -- la unica funcion del proyecto que llama a `rmtree` -- lo llama
  antes de cada borrado, aunque por su cuenta solo mire dentro de `raw`.
- `storage.aparta(carpeta, motivo)`, que es la forma correcta: mueve la particion
  a `data/debug/descartados/<cadena>-<fecha>-<motivo>` y deja el motivo escrito
  donde los controles lo leen de vuelta.

---

## 3. Menor — `ruff` se quejaba del arreglo de esta manana

El control de version minima de PostgreSQL anadido esta manana en
`plataforma/api/almacen.py` disparaba `RUF015` (`list(...)[0]` donde va
`next(iter(...))`). Corregido, y de paso con un comentario que explica por que
hay dos caminos: psycopg devuelve la fila como diccionario o como tupla segun la
fabrica de filas que este puesta.

---

## 4. Lo que si funciono a la primera

Vale la pena dejar constancia, porque no todo fueron sustos:

- **323 pruebas en verde** y `ruff check` limpio tras los arreglos.
- La cadena entera sobre la copia limpia -- bronze, silver, gold, emparejador,
  resumen -- **termina sin errores**: 52.575 productos, 17.979 enlaces, 6.449
  grupos comparables, 98 s el emparejador.
- El arreglo de `FACTOR_INCREIBLE = 30` se nota en el resumen. Antes:
  *"aviso: 340 grupos con diferencias imposibles (>200%)"*. Ahora:
  *"349 grupos con diferencias grandes pero creibles (entre 200% y 2900%)"* y
  solo **5** imposibles de verdad. Trescientas cuarenta alarmas se han
  convertido en cinco, y las cinco hay que mirarlas (la peor sigue siendo el
  azafran: 6,67 → 6.875 EUR/kg, que es un formato mal leido).

---

## 5. Segunda tanda: dejar manana blindado

Con los tres hallazgos de arriba en la mano, la pregunta pasa a ser otra: **que
hace falta para que manana la ejecucion no repita nada de esto**. Salieron dos
cosas mas.

### 5.1 Una cadena que dice "bien" y no deja bronze ya no cuela

Lo del apartado 2 se vio *a posteriori*, comparando ficheros. El sitio donde
habria servido de algo es la propia ejecucion, justo despues de los colectores:
ahi el crudo del dia sigue en disco y `reprocesar` lo arregla en un minuto.

`core/cobertura.py` gana dos funciones -- `particiones_bronze()`, que es ahora el
unico sitio que sabe como esta puesto bronze en disco, y `sin_bronze()` --, y
`run.py` las usa antes del pipeline:

```
[alcampo] TERMINO BIEN PERO NO HAY BRONZE DE HOY (2026-09-18). Algo lo borro despues de escribirlo.
[alcampo]   arreglo:  uv run python -m projects.cesta.reprocesar --fuente alcampo --fecha 2026-09-18
=== cadenas: 121s en total (alcampo 0s, carrefour 121s) ===
...
=== fallaron: alcampo ===
```

La cadena deja de contar como buena, asi que sale en `fallaron:` y en el
veredicto del dia. `resumen.dias_huerfanos()` pasa a usar la misma
`particiones_bronze()`: la misma regla escrita en dos sitios acaba siendo dos
reglas distintas.

Probado de las dos maneras: reproduciendo el incidente (un envoltorio que borra
la carpeta justo despues de que el colector termine bien) y con todo en su sitio,
donde no dice nada.

### 5.2 `verificar_docs` aprobaba sin haber comparado nada

En el ensayo con un catalogo de mentira de 123 productos, las **nueve**
comprobaciones salieron en verde y el control termino diciendo *"los numeros de
los documentos cuadran con los datos de hoy"*. No cuadraba ninguno.

La cifra se buscaba con `in` a secas. "123" esta dentro de "1.234" y dentro de
cualquier fecha con hora; "0" -- el valor de todas las capas que no habian
corrido -- esta en todas partes. Un control que aprueba cuando no tiene con que
comparar es peor que no tenerlo, porque se confia en el.

Ahora la cifra se busca con limites: ni digito ni separador de miles ni guion
pegados delante, ni digito pegado detras (el punto final de una frase si vale). Y
nada por debajo de cien cuenta como citado.

Al arreglarlo salio un falso positivo que llevaba ahi desde que se escribio el
control: **"productos con certificado 761"** aprobaba porque "761" estaba dentro
del "10.761" de `PARIDAD-CAMPOS.md`. La cifra no estaba en ningun documento.
Ahora si, en `CERTIFICADOS.md`, y el control la vigila de verdad.

### 5.3 El ensayo completo de la ejecucion de manana

Se monto un ensayo que corre `run.py` entero -- colectores, control de bronze,
pipeline, emparejador, limpieza, resumen y verificacion de documentos -- contra
**dos supermercados de mentira** levantados en local, con `SCRAP_DATA` apuntando
a una carpeta aparte. Ni red ni datos de casa.

Resultado, por los dos caminos (en fila y en paralelo, que es el de manana):

```
[carrefour]   12 categorias quedaron sin recoger; se espera 120s y se reintentan (vuelta 1)
[carrefour]   rescatadas 12 de 12
[carrefour] carrefour: 60 productos, 0 errores, 121s
=== cadenas: 121s en total (alcampo 0s, carrefour 121s) ===
pipeline: hecho
emparejar: hecho en 0s
=== todo correcto ===
=== run.main() devolvio 0 ===
```

Las 12 categorias bloqueadas cuestan **121 s**, no 45 s cada una: el reintento
del 403 que se quito esta manana era, medido, lo que habria dejado la ejecucion
sin terminar nunca.

### 5.4 Por que NO se devuelve a su sitio el bronze apartado

`reprocesar --fuente alcampo --fecha 2026-09-18` lo rehace desde el crudo
(probado en una copia: 20.571 productos, el numero exacto de `runs.csv`), y el
propio apartado sigue en `data/debug/descartados`, asi que devolverlo es un `mv`.

Y aun asi **no se hace**, por dos razones. La primera es obvia en cuanto se dice:
esa captura se aparto porque **estaba mal**, le faltaba la seccion de frescos
entera. La segunda solo se ve mirando el control de cobertura: su linea base es el
**ultimo** bronze de la cadena (`_ultimo_bronze`). Hoy esa linea base es la captura
del **17**, que tiene Frescos con 2.646 productos. Si manana Alcampo vuelve a
entregar Frescos vacia, el control compara 2.646 contra 91 y **se niega a
escribir**. Devolver la del 18 pondria como linea base una rama Frescos de **91
productos** y dejaria ciego al control justo para el fallo que se escribio para
cazar.

Las 20.559 filas si se quedan en gold, y eso tambien es a proposito: son precios
reales de ese dia para 20.571 productos que si se capturaron. Tirarlas abriria un
hueco de un dia para todo el catalogo de Alcampo en vez de solo para los frescos,
que es lo que realmente falto. El resumen lo explica cada dia en una linea.

---

## 6. Lo que queda apuntado

- El historico se rehace si se pide, pero **no se comprueba solo**. Un control
  que compare a diario el historico con lo que saldria de bronze avisaria de la
  deriva entre versiones del codigo. Aun no esta.
- `.prueba`, en la raiz del repositorio, eran **64 MB de ceros** del 6 de
  septiembre, restos de una prueba de espacio en disco. Vaciado a 0 bytes (esta
  en `.gitignore`; borrar el fichero en si es cosa de un `del .prueba`).
- La linea base del control de cobertura es el **ultimo** bronze de la cadena.
  Si un dia malo llegara a escribirse, el control del dia siguiente se compararia
  contra el. Cambiarlo tiene su propia trampa -- con el mayor de los ultimos N,
  una tienda que encoge de verdad daria alarma para siempre --, asi que de
  momento queda escrito y no tocado.
- `data/externo/food.parquet`, **7,85 GB**, solo hace falta para regenerar
  `off_es.parquet`. Ya estaba apuntado en `AUDITORIA.md`; sigue ahi.
