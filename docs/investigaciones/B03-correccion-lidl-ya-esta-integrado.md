# B03 · **Correccion**: Lidl esta MUCHO mas integrado de lo que escribi

*(13 de octubre de 2026. **Tercera correccion mia en dos rondas, y la mas grande: dos documentos que escribi
en esta misma sesion dicen lo contrario de lo que hay.**)*

## 1. Lo que yo escribi, y lo que hay

**En `docs/investigaciones/B03-y-la-aceptacion-que-faltaba-de-B04.md` y en `B03-el-piloto-leido.md` escreibi:**

| lo que dije | lo que hay |
|---|---|
| *«`CADENAS` sigue teniendo cinco»* | **`CADENAS_QUE_SE_CAPTURAN` tiene SEIS, y `lidl` es la sexta** |
| *«Lidl no aparece como sexta fuente»* | **esta en `CADENAS_QUE_SE_CAPTURAN` (`cesta.py:47`) y en `ORDEN` (`run.py:40`)** |
| *«bronze: no escribe nada, imprime un resumen»* | **eso es el PILOTO (`sondear_lidl.py`); `collectors/lidl.py` existe, tiene 11,7 KB y escribe** |
| *«lo que falta es la integracion»* | **la integracion esta casi entera; lo que falta es UNA COSA, y esta dicha por el propio codigo** |

**Y el error de metodo es el mismo de la ronda 18**: *lei `docs/LIDL.md`, vi que hablaba de un piloto «aun sin
integracion en la ingesta», **y di por hecho que la integracion no existia** -- **sin mirar `run.py` ni
`cesta.py`, que es donde estaria escrita.***

> **«Un documento se lee como un relato y se comprueba como un inventario.»** *`LIDL.md` es del 6 de octubre;
> la integracion es posterior. **Y yo cite el documento en vez de mirar el codigo.***

## 2. Lo que hay de verdad, medido

### La lista de fuentes, en la API

`plataforma/api/cesta.py:47`:

```python
CADENAS_QUE_SE_CAPTURAN = ("carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl")
```

*Y la linea 34 lo dice con la palabra: **«Seis.»***

### El runner diario

`projects/cesta/run.py:40`:

```python
ORDEN = ["carrefour", "dia", "mercadona", "aldi", "alcampo", "lidl"]
```

*Y el comentario de encima explica **por que** y **hasta donde**:*

> *«**Lidl entra aqui, y por eso**: tiene colector (`collectors/lidl.py`), descubrimiento
> (`descubrir_lidl.py`), cola de fichas y parser, y `ORDEN` no lo incluia -- **que es la primera mitad del
> punto 189 de G09**.»*

> **«La primera mitad.»** *O sea: **el propio codigo dice que hay una segunda.***

### Y el colector, que es el que dice que falta

`projects/cesta/collectors/lidl.py`, en su docstring:

> *«**No esta en la tarea de las 06:00, a proposito.** La ampliacion lo pide asi: **"pasar una captura
> acotada antes de anadirlo a la tarea diaria"**. Se ejecuta a mano y **no puede romper la pasada diaria**.»*

## 3. Asi que **lo que falta es una cosa, y esta escrita**

**No es «integrar Lidl».** *Es:*

  1. **UNA CAPTURA ACOTADA** -- *«pasar una captura acotada antes de anadirlo a la tarea diaria».* **Ya se
     sabe pedirla** (`sondear_lidl.py --web`, una sola pagina, con `robots.txt` delante).
  2. **Y DESPUES anadirlo a la tarea de las 06:00**, que es **la segunda mitad del punto 189 de G09**.

*Y la aceptacion de B03 pide justo eso, mas lo que rodea:* **bronze -> silver -> gold -> API -> UI; region/
club/fechas/nutricion/ausencias probadas, captura acotada y contador visible.**

> **Y el orden importa**: *el colector dice «no puede romper la pasada diaria», y eso es una precaucion, no
> una excusa.* **Primero la captura acotada -- que se puede mirar --, y despues el horario.**

## 4. Y el colector ya hace bien las cinco cosas que el plan pide

*De su docstring, y son los cinco criterios de B03, uno por uno:*

  - **«no declara a Lidl ganador de una cesta si le faltan productos»** -> *«Lidl no gana una cesta completa
    si faltan lineas.»*
  - **«la ausencia de un producto en la campana NO es que se haya retirado»** -> *«marcar los no observados
    como desconocidos.»*
  - **«El EAN no se inventa. La ficha trae `ians` e identificadores internos; ninguno es un EAN comprobado,
    asi que `ean` va vacio. Un codigo inventado envenena las comparaciones (T03).»** -> *«no confundir IAN
    con EAN.»*
  - **«La region se resuelve antes de mirar el precio (`regionsV2[region].regionPriceId`)»** -> *«no
    convertir CP en id de region sin correspondencia.»*
  - **«El precio tachado no es el precio. Lo que se cobra va en `precio_cent` y el anterior en
    `precio_anterior_nativo_cent`: confundirlos seria anunciar una bajada que no existe.»** -> *y esto **no
    estaba en el plan**, y es una distincion que el colector hace por su cuenta.*

**Y una mas, que tampoco estaba en el plan**: *«el precio del club de Lidl se conserva como lo que es: una
condicion, no el precio general.»* **Que es exactamente lo que `sondear_lidl.py` documentaba como «no un
precio elegible».**

> **Asi que B03 no hay que disenarlo: hay que **acabarlo**.** *Y lo que queda son dos pasos, dichos por el
> propio codigo.*

## 5. Lo que queda por leer, y sigue faltando

```
descubrir_lidl.py 9,9 KB   fichas_lidl.py 6,7 KB   ficha_lidl.py 7,7 KB
```

*Tres ficheros.* **Y `run.py` ya se ha leido** -- *que es el que contesta «como se engancha al ciclo
diario»: ya esta enganchado en `ORDEN`, y lo que falta es el horario.*
