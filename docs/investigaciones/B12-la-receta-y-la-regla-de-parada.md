# B12 · **§4**: la receta de una investigacion que produce una mejora -- y su **regla de parada**

*(13 de octubre de 2026. **Tercera ronda de B12. Y el documento que B12 pide ya esta escrito, con ocho reglas.**)*

## 1. Lo que B12 pide, y donde esta

```
B12 (plan:331):  «Ver seccion 8: *** una funcion por investigacion ***. ... Aplicar ideas con codigo
                 propio y diseñar la prueba equivalente en Cesta.»

   -> *** `docs/SUPERAPP-COMPETENCIA-Y-REA.md` §4 «Investigacion minima que produce una mejora» ***
```

## 2. Y §4 tiene **ocho reglas, y tres son las del encargo**

```
- Usuario y tarea de Cesta; *** caso de exito MEDIBLE ***.
- Fuente, fecha, version o hash cuando exista artefacto. *** En una web sin version, URL/fecha y evi[dencia]. ***
- Observaciones de entrada->interaccion->salida->FALLO->persistencia, con estados NORMAL, VACIO y ERROR.
- *** Demostrado documental / demostrado por ejecucion / HIPOTESIS / DESCONOCIDO. ***
- *** Idea que se adapta, EXPRESION QUE SE DESCARTA, diseño propio y por que beneficia a una familia. ***
- Ficheros y contratos de Cesta afectados; *** riesgo de privacidad, identidad, unidades y costes. ***
- *** La misma matriz de casos para referencia y Cesta. ***
- Prueba de Cesta, capturas antes/despues, commit y limitaciones.

*** No extraer catalogos de recetas, marcas, ilustraciones, textos largos ni codigo privado de competidores. ***

*** Regla de parada: *** cuando se puede especificar una mejora comprobable con las fuentes suficientes.
```

## 3. Y contesta **el encargo, palabra por palabra**

```
EL ENCARGO PIDE:  «Una funcion por investigacion, EVIDENCIA, DEMOSTRADO/HIPOTESIS/DESCONOCIDO,
                   codigo y diseño propios. Aplica la mejora a Cesta con PRUEBA EQUIVALENTE,
                   NO COPIES SOFTWARE AJENO.»
```

> *** Y §4 lo tiene **todo, y en orden**: ***
>
> | el encargo | §4 |
> |---|---|
> | «una función por investigación» | *«Cada informe trata **una capacidad**, no una app entera»* |
> | «evidencia» | *«Fuente, fecha, versión o hash… En una web sin versión, **URL/fecha y evidencia**»* |
> | «demostrado/hipótesis/desconocido» | *** «Demostrado documental / demostrado por ejecución / hipótesis / desconocido» *** |
> | «código y diseño propios» | *** «Idea que se adapta, **expresión que se descarta**, diseño propio» *** |
> | «no copies software ajeno» | *** «No extraer catálogos de recetas, marcas, ilustraciones, textos largos ni código privado de competidores» *** |
>
> *** Y las cuatro categorias de prueba son **las del encargo, con los mismos nombres** *** -- *o sea: **el encargo y el documento son el mismo texto, y el segundo es mas preciso.** *

## 4. Y hay **dos reglas que valen mas que las otras seis**

### a) «La misma matriz de casos para referencia y Cesta»

> *** Es **el oraculo de B09, aplicado a la investigacion**: *** *la referencia y Cesta **se prueban con los mismos
> casos**, y **se comparan** -- *no se describe la referencia y se supone que Cesta hace lo mismo.*
>
> *** Y su consecuencia esta escrita: *** *** «Si no se pudo ejecutar la referencia, **escribi[rlo]**» *** -- *o sea:
> **si no se pudo probar, se dice**, *y **no se presenta como observado.** *
>
> *** Que es **el principio de B11** («lo que no se observo no se puede dibujar como si se hubiera observado»),
> aplicado **a un informe sobre una app ajena.** * **Decimonovena vez**, y **la primera vez que se aplica a la
> propia investigacion.** *

### b) «Regla de parada: cuando se puede especificar una mejora comprobable con las fuentes suficientes»

> *** Y esto **es lo que B12 necesita**, porque **el encargo pide «no estudiar un binario enorme»** *** -- *y §4 da **el
> criterio para parar**: *
>
> ```
> SE PARA CUANDO:  1) hay una mejora  *** COMPROBABLE ***  (o sea: con prueba)
>                  2) las fuentes son *** SUFICIENTES ***  (no todas)
> ```
>
> *** O sea: **no hay que agotar la referencia: hay que poder escribir su prueba** *** -- *y **cuando se puede, se
> para.** *
>
> *** Y es **la misma forma que el oraculo** («prefiere estar incompleto antes que mentir») y que `FUENTES` vacia
> (B07): *** *** el limite se declara, y no se rellena. ***

## 5. Y B12 queda **contestado, y sin abrir un binario**

```
1) UNA FUNCION POR INVESTIGACION    *** §4: «cada informe trata UNA CAPACIDAD» ***
2) LAS TRES PRIORIDADES             menu · porciones/diario · flujos de lista -- las tres YA LEIDAS en el codigo
3) NO ESTUDIAR UN BINARIO ENORME    *** y §4 da LA REGLA DE PARADA ***
4) CODIGO PROPIO + PRUEBA EQUIV.    *** §4: «la misma matriz para referencia y Cesta» + «prueba de Cesta» ***
5) Y LA REGLA                       «lo anunciado no acredita el mecanismo», dicha DOS VECES en el plan
6) Y LA FORMA DEL INFORME           *** ocho reglas, con las CUATRO categorias del encargo ***
7) Y LO QUE NO SE HACE              *** «no extraer catalogos, marcas, ilustraciones, textos largos ni
                                    codigo privado» ***
```

> *** Y B12 **no pide ejecutar nada**: *** *pide **un informe por capacidad**, con **la forma de §4**, *y **la regla de
> parada esta escrita** -- *que es **lo que faltaba** para no estudiar un binario enorme.*
>
> *** Y lo que queda de B12 es **elegir la capacidad y escribir el informe** *** -- *y **la capacidad la elige el
> plan**: **«consolidar el menú, porciones/diario y flujos de lista»**, *que son **las tres que esta sesion ya ha
> leido a fondo.** *
