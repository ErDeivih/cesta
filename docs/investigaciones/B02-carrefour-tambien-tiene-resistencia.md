# B02 · **Carrefour tambien tiene resistencia** -- y con esto se caen mis cinco conclusiones

*(13 de octubre de 2026. **La ultima pieza que faltaba leer. Y desmiente todo lo que dije de B02.**)*

## 1. Lo que hay, literal

`projects/cesta/collectors/carrefour.py:518-537`:

```python
fallidas = recorre(cats)
vueltas_dadas = 0
# Segunda y tercera oportunidad. Un bloqueo por sospecha de bot se levanta
# solo, y lo que hace falta es estar ahi cuando se levante. Cada vuelta
# espera mas y va mas despacio, porque insistir al mismo ritmo es lo que nos
# tenia fichados.
for vuelta in range(1, VUELTAS_DE_RESCATE + 1):
    if not fallidas:
        break
    bloqueadas = sum(1 for c, _ in fallidas
                     if ultimo_fallo.get(c) in ESTADOS_DE_BLOQUEO)
    if bloqueadas:
        espera = ESPERA_ENTRE_VUELTAS * 2 ** (vuelta - 1)
        print(f"  {len(fallidas)} categorias quedaron sin recoger "
              f"({bloqueadas} por bloqueo); se espera {espera}s y se "
              f"reintentan a ritmo mas lento (vuelta {vuelta})", flush=True)
    elif vuelta > VUELTAS_SIN_BLOQUEO:
        print(f"  quedan {len(fallidas)} categorias y ninguna esta "
              f"bloqueada: {_por_que_fallan(fallidas, ultimo_fallo)}. Eso no "
              f"se arregla esperando, asi que no se espera mas y se cuentan "
```

> **Y esta TODO lo que el plan pide, y bien:**
>
>   - **`VUELTAS_DE_RESCATE`** -- *vueltas de rescate: lo que el plan llama **reintentos con limite**.*
>   - **`ESPERA_ENTRE_VUELTAS * 2 ** (vuelta - 1)`** -- ***backoff exponencial**, literal.*
>   - **`ESTADOS_DE_BLOQUEO`** *-- **usado**, y para **contar cuantas estan bloqueadas** y decirlo.*
>   - **`VUELTAS_SIN_BLOQUEO`** *-- y **distingue «bloqueada» de «falla por otra cosa»***: *«quedan N categorias y
>     **ninguna esta bloqueada**… **Eso no se arregla esperando**».*
>   - **y `_por_que_fallan(...)`** *-- **una funcion que dice POR QUE fallan**.* *Que es exactamente la medida que
>     el plan pide: «tiempo y **motivo** de cada reintento».*
>   - **y el comentario lo explica**: *«insistir al mismo ritmo es lo que **nos tenia fichados**»* -- *o sea que
>     **el backoff esta puesto porque se midio que hacía falta**.*

## 2. Y con esto se caen las cinco conclusiones, todas

```
105  «hoy ningun colector distingue un desafio de un catalogo vacio»        FALSO
     -> Alcampo tiene `RetoWAF` (13 usos) y Carrefour distingue bloqueo de otra causa
106  «lo que falta es la distincion desafio vs cero valido»                 FALSO
     -> esta en los dos
107  «Carrefour tiene una linea y nada mas»                                 FALSO
     -> tiene backoff exponencial, vueltas de rescate y `_por_que_fallan`
108  «no se sabe si hay fixtures»                                           FALSO
     -> la carpeta existe (vacia) y hay 11 ensayos de colectores
109  «B02 es completar, no construir»                                       ...  y ni eso
```

> **Y todas tenian el mismo origen: **concluir antes de leer**.** *Cada ronda leyo un poco mas y bajo un escalon:
> `grep` -> correccion sin abrir -> veinte lineas -> un `ls` -> **y por fin, el bloque entero**.*
>
> ***Cinco rondas para recorrer cinco pasos que se podian haber dado en una: abrir los dos ficheros.***

## 3. Y entonces, ¿que es B02 de verdad?

**Con los dos colectores leidos, la respuesta cambia por ultima vez, y ahora si se sostiene:**

```
LO QUE LOS DOS YA TIENEN:
  ALCAMPO    RetoWAF (13 usos, dice DONDE le cortaron) · AVANCE_MINIMO
             · CORTES_PARA_RENDIRSE · MAX_RENOVACIONES · `detener`
             · y abre un navegador para el reto cuando hace falta
  CARREFOUR  VUELTAS_DE_RESCATE · ESPERA_ENTRE_VUELTAS * 2**(vuelta-1)
             · VUELTAS_SIN_BLOQUEO · `_por_que_fallan`
             · y distingue «bloqueada» de «falla por otra cosa»
  LOS DOS    no inventan catalogo cuando no pueden leer

LO QUE FALTA, CON LO LEIDO:
  1) MEDIR -- «requests efectivos, cobertura de ramas, productos unicos, tiempo y motivo
     de cada reintento». Y AQUI ESTA LO POCO QUE FALTA DE VERDAD: los dos colectores
     CUENTAN Y DICEN (reintentos, bloqueadas, por que fallan) -- pero se dice POR PANTALLA,
     no en un sitio que se pueda leer despues. ESO es lo que falta.
  2) FIXTURES -- la carpeta `tests/fixtures/` esta y vacia. Y el plan pide seis casos.
  3) LA DECISION DEL NAVEGADOR -- que es del propietario y ya se le pregunto.
  4) Y UNA CAPTURA ACOTADA REAL -- la segunda mitad de la aceptacion.
```

> **O sea: B02 es, sobre todo, SACAR A DONDE SE PUEDA LEER lo que los dos colectores ya cuentan.** *Que es
> pequeño, concreto, y **nada parecido a «construir lo que no hay»**.*
>
> *Y esa conclusion **solo se podia escribir despues de leer los dos ficheros enteros** -- que es lo que estas
> cinco rondas hicieron **a trozos, y en el orden equivocado**.*

## 4. Y la leccion, que ya esta dicha cinco veces y hay que decirla una mas

**Estas cinco rondas son el mismo error repetido, y cada repeticion costo una ronda.** *La primera fue la peor
-- «no existe nada» -- porque **habria justificado escribir un colector de cero al lado de dos que funcionan**.*

> **Y el arreglo era, las cinco veces, el mismo: abrir el fichero y leerlo entero.** *No un `grep`, no veinte
> lineas, no un `ls`.*
>
> **Lo unico que estas rondas han comprado es que el error no llego al codigo.** *Que, visto lo que habria
> costado, no es poco -- **pero es lo minimo que se puede decir de cinco rondas**.*
