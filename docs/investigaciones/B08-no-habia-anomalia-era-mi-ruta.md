# B08 · **NO habia anomalia: era mi llamada a la ruta equivocada** -- y el objetivo funciona entero

*(13 de octubre de 2026. **Y es la decimocuarta correccion, y es el mismo error de B02: concluir antes de leer.**)*

## 1. La anomalia que yo declare, y lo que era

> *** Lo que escribi hace una ronda: ***
> > *** «sale una anomalia, y se dice sin disfrazarla: *** *** `PUT /api/preferencias` guarda, y
> > `GET /api/estado` da `preferencias: null`» *** *
>
> *** Y **lo que pasaba**: *** *** **la ruta que devuelve las preferencias es `/api/yo`, y yo llame a
> `/api/estado`.** *Y **`/api/estado` no tiene ese campo** *-- *asi que **lei `null` de un campo que no
> existia.** *
>
> *** Y **el codigo estaba bien, y se ve en su linea**: ***
> ```python
> l158  @app.get("/api/yo")
> l160      return {"usuario": usuario, "preferencias":
> l161              almacen.preferencias_de(usuario["id"]) *** if usuario else {} ***}
>      *** -> y devuelve `{}` cuando no hay usuario, *** *** y NO `null`. *** *
> ```

## 2. *** Y con la ruta correcta, el objetivo funciona ENTERO ***

```
$ `PUT /api/preferencias`  {"clave": "objetivo:2026-10-14", "valor": {"kcal": 2000}}
  -> *** {"hecho": true} ***

$ `GET /api/yo`
  usuario: *** b13-recorrido-2301 ***
  *** PREFERENCIAS -> {"objetivo:2026-10-14": {"kcal": 2000}} *** *
```

> *** O sea: *** *** **se guarda Y se lee, con la clave `objetivo:<fecha>` y el valor `jsonb`, y sin
> escribir una linea de codigo.** *
>
> *** Y **la clave se puede partir para sacar la fecha**, *y **el valor trae el numero que puso la persona.** *
>
> *** -> y **con eso, la tercera pieza de B08 esta CERRADA**, y **no habia nada que arreglar.** *

## 3. *** Y el error es el de B02, otra vez, y hay que decirlo con su nombre ***

```
*** B02: ***  *«no existe nada»* -- *y **el WAF estaba delante*
*** B02: ***  *«y nada mas»* -- *y **`runlog` estaba*
*** B08: ***  *** «hay una anomalia en la lectura» *** *** -- y **era mi ruta.** *
```

> *** Y **las tres veces el patron es el mismo**: *** *** **vi un resultado que no cuadraba, y lo
> atribui al codigo antes de leer la linea que lo produce.** *
>
> *** Y **las tres veces la salvaguarda fue la misma, y esta vez funciono**: *** *«**no se declara cual es la
> causa**, *y **se dice por que**: *la forma exacta de esa respuesta **no se ha leido entera** -- *y **concluir
> «esta roto» sin leerla seria el error de B02.» *
>
> *** -> o sea: *** *** **la disciplina de no concluir sin leer acaba de evitar un falso positivo**, *
> *y **por eso se escribe: no para lucirse, sino porque es lo que impide el error siguiente.** *

## 4. Y **B08 queda con TRES de sus cuatro piezas cerradas, y la cuarta con patron**

```
*** 1. LA VISTA DE PREVISTOS ***  -> *** HECHA *** *(`GET /api/recetas/plan/prevision`, 200;
                                     `kcal` null y no cero, `motivo` por linea, cobertura por nutriente)*
*** 2. SU ENSAYO ***               -> *** HECHO *** *(8 ensayos: 2025 -> 2033)*
*** 3. EL OBJETIVO ***             -> *** CERRADO, y funciona hoy ***:
                                     `PUT /api/preferencias` + `GET /api/yo`, con `{"objetivo:<fecha>": {"kcal": N}}`
*** 4. *** LAS GRAFICAS DE LOS TRES *** *** -> *y `logica/chispa.ts` **ya tiene sus tres reglas**:
                                     «lo que no se observo **no se puede dibujar como si se hubiera observado**»*
```

> *** Y **de las cuatro, tres estan cerradas y la cuarta tiene su patron y su regla.** *
> *** Y **ninguna exigio inventar un dato**, *ni una migracion, *ni una tabla nueva, *ni una ruta nueva.** *

## 5. Y **la cuenta de las cuatro vias** de la ausencia, que sigue en pie

```
*** la VISTA no existia, *** *y **eso se midio por cuatro vias**: *
  *los siete nombres · el frontend (73) · `plataforma/api`+`core` (CERO) · y los ensayos (el criterio sin ensayo)*
  *** -> y esa parte sigue siendo verdad: *** *** la vista NO estaba, *** *** y ahora SI esta. *** *
```
