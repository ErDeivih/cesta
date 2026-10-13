# B02 · **La segunda correccion, y esta es grande**: Alcampo tiene la distincion que yo dije que faltaba

*(13 de octubre de 2026. **Se leyo `alcampo.py:775-805`, y desmiente las rondas 105 Y 106.**)*

## 1. Lo que hay, literal

```python
except RetoWAF:
    anterior = _filas_ultimo_bronze()
    if (renovaciones >= CORTES_PARA_RENDIRSE and anterior
            and len(filas) < anterior * AVANCE_MINIMO):
        errores += 1
        print(f"  {renovaciones} cortes y solo {len(filas)} productos "
              f"de los {anterior} de la ultima pasada buena: hoy el WAF "
              f"nos tiene fichados. Se deja para manana; lo descargado "
              f"queda en cache y no se volvera a pedir.")
        detener = True
        break
    if renovaciones >= MAX_RENOVACIONES:
        ...
```

> **Y ahi esta todo lo que el plan pide, y mas:**
>
>   - **`except RetoWAF:`** -- *hay una **excepcion dedicada al desafio**. O sea que **el colector SI distingue
>     el reto del catalogo vacio**.*
>   - **`_filas_ultimo_bronze()`** -- *y **compara con la ultima pasada buena**. Que es exactamente «conservar
>     ultimo valido».*
>   - **`AVANCE_MINIMO`** -- *un **avance minimo**: si se ha conseguido muy poco, **no se guarda como si fuera el
>     dia**.*
>   - **`CORTES_PARA_RENDIRSE` y `MAX_RENOVACIONES`** -- *limites con nombre.*
>   - **`detener = True`** -- *el circuit breaker.*
>   - **y el mensaje lo dice**: *«**hoy el WAF nos tiene fichados**. Se deja para manana; lo descargado queda en
>     cache y no se volvera a pedir.»*

## 2. Y entonces las rondas 105 y 106 estaban mal, y hay que decirlo

```
RONDA 105 dijo:  «hoy ningun colector distingue un desafio de un catalogo vacio»    -> FALSO
RONDA 106 dijo:  «lo que falta de verdad es la distincion desafio vs cero valido»   -> FALSO
```

**Y las dos salieron de un `grep` con mis palabras** -- *`desafio`, `429`, `503`, `backoff`, `Retry-After`* --,
**cuando el codigo dice `RetoWAF`, `cortes`, `renovaciones` y `rendirse`.**

> **La 105 busco `desafio` y el codigo escribe `RetoWAF`.** *La 106 corrigio la 105 y **volvio a concluir sin
> leer** -- dijo «falta la distincion» **sin haber abierto el fichero**. Y la distincion estaba **a 20 lineas de
> donde yo habia mirado**.*
>
> *Dos rondas, dos conclusiones, las dos falsas, y **las dos por lo mismo: escribir antes de leer**.* **Que es
> exactamente lo que estas dos rondas decian estar evitando.**

## 3. Lo que esto cambia de B02, que es casi todo

**Antes**: *«construir lo que no hay» -> «igualar Carrefour a Alcampo y anadir la distincion».*

**Y ahora**: *Alcampo **ya tiene la distincion**, y bien hecha.* **Asi que B02 es:**

  1. **medir** *-- las cuatro cosas del plan: requests efectivos, cobertura de ramas, productos unicos, tiempo y
     motivo de cada reintento.* *Y **Alcampo ya cuenta `errores`, `renovaciones`, `truncadas` y `reintentos** --
     o sea que **parte de la medida ya existe**, y lo que falta es **sacarla** a donde se pueda leer.*
  2. **igualar Carrefour** *-- que tiene una linea (`ESTADOS_DE_BLOQUEO = (403, 429)`) y nada mas.* **Y lo que
     hay que llevarle es lo de Alcampo.**
  3. **y los fixtures** *-- desafio, esquema cambiado, pagina vacia, corte a mitad, reanudar, publicacion final.*
     *Que es donde se prueba todo lo de arriba sin red.*

> **O sea: B02 es, en buena parte, LEER LO QUE ALCAMPO YA HACE Y LLEVARLO A DONDE NO ESTA.** *Que es mucho mas
> pequeño que lo que dije en la 105, y **mucho mas pequeño que lo que dije en la 106**.*

## 4. Y la leccion, que ya es la tercera vez en tres rondas

```
ronda 68   una medida con un caso, y un nombre puesto sin contrastar
ronda 105  un grep con las palabras equivocadas
ronda 106  y una correccion de la 105 HECHA SIN LEER EL FICHERO
```

> **Las tres son la misma cosa: escribir antes de leer.** *Y las tres tenian la misma forma de arreglo: **abrir
> el fichero**.*
>
> **Y hay una cuarta, que es la que mas importa:** *la ronda 106 **se corrigio a si misma con otra suposicion**.
> Corregir no es leer. **Una correccion hecha sin mirar es una suposicion con mejor reputacion.***

## 5. Y el siguiente comando, que no se escribe hasta haberlo leido

```
  alcampo.py:  leer 700-830 ENTERO   -> RetoWAF, AVANCE_MINIMO, CORTES_PARA_RENDIRSE,
                                        MAX_RENOVACIONES, TOPE_API, truncadas, reintentos
  carrefour.py: leer 60-80 y quien use ESTADOS_DE_BLOQUEO
  y despues: los ensayos de colectores que ya existan
```

*Y **no se concluye nada de B02 hasta haber leido esos tres sitios enteros.*** **Dos rondas de conclusiones falsas
son suficiente aviso.**
