# B13 · **`prueba-navegador` se llama «Madre»** -- y esto es lo que B13 avisa de las capturas

*(13 de octubre de 2026. **Quinta ronda de B13. Y el paso 1, mirado mas a fondo, da un aviso.**)*

## 1. Lo que hay, medido

```
$ docker exec cesta-db-1 psql -U cesta -d cesta -tAc \
    "SELECT usuario, nombre, length(clave_hash) FROM usuario \
     WHERE usuario IN ('prueba','prueba-navegador','prueba-invitada') ORDER BY usuario;"

  prueba           | Prueba   | 97
  prueba-invitada  | Invitada | 97
  *** prueba-navegador | Madre | 97 ***
```

> *** Los tres **tienen el hash de 97 caracteres** *** -- *o sea: **argon2, y las claves estan derivadas.** *
> *Eso esta bien.*
>
> *** Y **dos de los tres se llaman como una prueba** ***: *«Prueba» e «Invitada».*
>
> *** Pero el tercero **se llama «Madre»** *** -- *y **«Madre» no es un nombre de prueba: es **un nombre de casa.** *

## 2. Y eso es **exactamente** lo que B13 avisa, dos veces

```
B13 (plan:341):  «Recorrer cinco recetas, compra y diario con *** USUARIOS DE PRUEBA, NO CUENTAS REALES ***.»
B13 (plan:344):  «Guardar evidencia referenciable *** SIN COMMITEAR NUTRICION PERSONAL ***.»
```

> *** Y `prueba-navegador | Madre` es **la frontera entre las dos cosas**: ***
>
>   - **el `usuario` es de prueba** *(`prueba-navegador`) -- *o sea: **la cuenta se creo para recorrer la app**;*
>   - *** pero el `nombre` es de una persona de la casa *** -- *y **es el que se pinta en la pantalla.** *
>
> *** O sea: **si se hace una captura de esa sesion, se ve «Madre»** *** -- *y **«Madre» es un dato de la casa, no de
> la prueba.** *
>
> *** Y B13 pide **capturas** (clausula 5) **y prohíbe commitear nutricion personal** *** -- *o sea: **el aviso del
> plan y esta medicion son la misma cosa**, *y **el plan ya sabia que pasaria.** *

## 3. Y por eso **el paso 4 tiene una guarda mas, que no estaba escrita**

```
PASO 4 (los cinco recorridos) tiene que usar:
  *** `prueba` (nombre «Prueba») o `prueba-invitada` («Invitada») ***
  *** y NO `prueba-navegador`, porque su nombre es «Madre» ***
     -- *y si el recorrido necesita una segunda persona, **crear una** (`crea_usuario` es inofensivo,
     y `UsuarioRepetido` impide duplicar) **con un nombre de prueba**, no reutilizar esa.*
```

> *** Y **no se dice que «Madre» sea un problema** ***: *se dice que **es un nombre de casa**, *y que **las capturas
> que B13 pide no deben llevarselo.** *
>
> *** Y es **la misma disciplina de la columna `nombre`**: *** *`crea_usuario(usuario, nombre, clave)` separa **el
> identificador** del **nombre visible** -- *o sea: **el proyecto ya distingue las dos cosas**, y **la distincion
> sirve justo para esto**: **la cuenta puede ser de prueba y el nombre de casa, o al reves.** *
>
> *** Y esa separacion es **un acierto del diseño** que aqui se ve en su consecuencia practica. ***

## 4. Y el estado de B13, con los dos pasos previos hechos

```
  1) RUTAS Y COMPONENTES MONTADOS  *** HECHO *** -- `Suite` se sirve, `Nav` no · `/compra`·`/recetas`·`/calorias`
  PASO 1 (ver usuarios)            *** HECHO *** -- 38 usuarios, convencion `<prefijo>-<caso>-<timestamp>`
                                   *** y un aviso: `prueba-navegador` se llama «Madre» ***
  PASO 2 (leer `crea_usuario`)      *** HECHO Y CONCLUYENTE *** -- un solo `INSERT` en `usuario`;
                                   nombre normalizado; clave derivada; y `UsuarioRepetido` si ya esta
  PASO 3 (elegir usuarios)          *** RESUELTO: *** `prueba` / `prueba-invitada` -- **y NO `prueba-navegador`**
  PASO 4 (los cinco recorridos)     *lo siguiente*
  PASO 5 (capturas + manifiesto)    *y con la guarda nueva: **sin el nombre «Madre»***
```

> *** Y los tres pasos previos **han cambiado el paso 4 dos veces**: ***
>
>   1. *el **paso 1** evito **crear usuarios que ya estaban** (38, con convencion);*
>   2. *y **mirandolo mas a fondo**, el mismo paso 1 **evito llevarse un nombre de casa a una captura.** *
>
> *** Que es **exactamente** lo que el plan pide cuando pone **«inventariar»** como primera palabra de B13. ***
