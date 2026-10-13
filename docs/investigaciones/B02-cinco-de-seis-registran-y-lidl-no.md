# B02/B03 · **La respuesta invierte el cuadro**: cinco de seis registran sus pasadas, y **Lidl no**

*(13 de octubre de 2026. **Y esto corrige MI PROPIO CIERRE de B03, que hice hace veinte rondas.**)*

## 1. La medida

```
alcampo     6 usos de log_run/check_drift
carrefour   4 usos
dia         4 usos
mercadona   4 usos
aldi        4 usos
LIDL        0 USOS        <- *** LIDL ES EL QUE NO LO USA ***
```

> **Cinco de los seis usan `core/runlog`.** *Y **el que no lo usa es Lidl**.*
>
> *O sea: **el colector que esta sesion construyo y declaro cerrado en B03 es el unico de los seis que no registra
> sus pasadas.***

## 2. Y esto invierte las dos cosas que yo habia dicho

```
RONDA 105:  «B02 es construir un sistema de resistencia»      -> CARREFOUR Y ALCAMPO SON LOS QUE MAS TIENEN
RONDA 102:  «B03 cerrado: Lidl corre en la pasada diaria»      -> CORRE, PERO **NO REGISTRA QUE CORRIO**
```

> **El plan pide de B02 «medir requests efectivos, cobertura de ramas, productos unicos, tiempo y motivo de cada
> reintento» -- y resulta que **cinco colectores ya lo hacen y el sexto es el mio**.*
>
> *Y de B03 el plan pide «**contador visible**» y «observabilidad» -- y **`log_run` es exactamente eso**, y **Lidl
> no lo llama**.*

## 3. Y por que mi cierre de B03 no lo caza, que es lo que hay que decir

*Cuando cerre B03 escribi, con la aceptacion delante:*

> *«contador visible -- HECHO -- la cobertura y el contador por campo»*

**Y eso es cierto: la cobertura por campo la escribe.** *Lo que **no** comprobe es si Lidl **registra su pasada**
como los otros cinco -- porque **no sabia que `core/runlog.py` existia**.* *Y no lo sabia **porque no lo busque**:
`runlog`, `log_run`, `check_drift` -- **ninguno de esos nombres estaba en mi lista de palabras**.*

> **Es la misma forma que las siete correcciones de B02, y esta se me escapo en B03 hace veinte rondas.** *Y no la
> habria encontrado con `grep` de mis palabras: **la encontro comparar los seis ficheros entre si**.*
>
> ***«¿Que hacen los otros cinco que este no hace?»*** *-- *que es la pregunta que se puede hacer **cuando ya se
> han leido los seis**, y que no se le ocurre a nadie que va fichero a fichero.*

## 4. Y lo que esto cambia, que no es poco

```
B03 -- MI CIERRE:  «contador visible HECHO»
   Y ES CIERTO A MEDIAS: la cobertura por campo se escribe, PERO Lidl no llama a `log_run`,
   asi que la pasada de Lidl NO queda registrada como la de los otros cinco.
   -> SE SOSTIENE EL CIERRE? La aceptacion de B03 no pide `log_run`. Pero pide «observabilidad»
      y «contador visible», y los otros cinco hacen mas.
   -> Y ES UNA LINEA: `log_run(FUENTE, len(filas), errores, segundos, completa)`.

B02 -- EL ENCARGO:  «mejorar colectores mediante validacion, checkpoints, backoff, limites,
                    observabilidad y recuperacion»
   -> Carrefour y Alcampo YA tienen la observabilidad (4 y 6 usos).
   -> Y LO QUE FALTA ES JUSTO LO CONTRARIO DE LO QUE YO CREIA: **que Lidl la tenga**.
```

## 5. Y la leccion, que ya es la octava vez pero con una forma nueva

**Las siete anteriores eran «afirme sin mirar».** *Esta es distinta:*

> ***Mire, no vi `runlog` porque no lo buscaba, y cerre B03 sin comparar con los otros cinco.***
>
> **Y la herramienta que lo habria cazado no es `ls` ni leer entero: es COMPARAR.** *Poner los seis ficheros uno al
> lado del otro y preguntar **que hace cada uno que los otros no**.*
>
> *Que es, ademas, **exactamente lo que B02 pide de si mismo**: «Carrefour y Alcampo **resistentes**» -- *una
> palabra que solo tiene sentido **comparando**.*
