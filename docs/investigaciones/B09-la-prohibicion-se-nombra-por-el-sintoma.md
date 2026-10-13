# B09 · **La prohibicion se nombra por el SINTOMA y se prueba por la PROPIEDAD**

*(13 de octubre de 2026. **Sexta ronda de B09. Y la busqueda de la clausula (5) ensena una regla nueva.**)*

## 1. Lo que se busco, y lo que salio

```
BUSQUEDA:  «ordinal» en los nombres de los ensayos   ->  NADA
```

> *** El plan dice: *** *«**No modificar grupos de listas historicas por ordinal**» -- *y **la palabra «ordinal» no
> aparece en ningun ensayo**.*
>
> *** Pero **la propiedad que la prohibicion protege si aparece, y con cuatro nombres**: ***
>
> ```
> tests/test_banco_verdad.py       test_el_id_es_ESTABLE_y_distingue_fichas
> tests/test_catalogo.py           test_el_historico_dice_de_que_producto_es_ca[da uno]
> tests/test_alertas.py            test_sin_historico_no_se_inventa_un_minimo
> tests/test_aislamiento.py        test_la_migracion_del_diario_conserva_lo_his[torico]
>                                  test_la_migracion_de_recetas_conserva_lo_his[torico]
>                                  test_migrar_tres_veces_no_cambia_nada_en_nin[guno]
> *** tests/test_b03_herencia_con_dos_zonas.py   test_lo_que_no_cambia_CONSERVA_SU_NUMERO ***
> ```

## 2. Y el ultimo es **de esta misma sesion**

**`test_lo_que_no_cambia_conserva_su_numero`, en `tests/test_b03_herencia_con_dos_zonas.py`** -- *un ensayo
**escrito en B03**, por mi, en este mismo encargo.*

> *** Y dice, literalmente, **lo que la clausula (5) pide**: *** *que **lo que no cambia conserve su numero** -- *o
> sea: **que un identificador no se reasigne por posicion.** *
>
> *** O sea: **la prohibicion del plan y la propiedad que yo probe son la misma cosa**, *dicha **al reves**:*
>
> ```
> EL PLAN:    «no modificar grupos historicos POR ORDINAL»   <- el SINTOMA (lo que NO hay que hacer)
> EL ENSAYO:  «lo que no cambia CONSERVA SU NUMERO»           <- la PROPIEDAD (lo que SI tiene que pasar)
> ```
>
> *** Y son equivalentes: **si un id es estable, es que nadie lo esta reasignando por posicion.** ***
>
> *** Y conviene decir **por que el plan lo nombra por el sintoma**: *** *porque **el sintoma es el fallo que ya
> ocurrio** -- *el de B03: «**la consulta devolvia 11 columnas y el codigo esperaba 10**».* **El plan no prohibe una
> idea: prohibe un accidente concreto.** *

## 3. Y la regla nueva, que vale para lo que queda de encargo

```
EL PLAN NOMBRA LAS PROHIBICIONES POR SU SINTOMA  -- «por ordinal», «no neutraliza formato incompatible»
EL CODIGO LAS PRUEBA POR SU PROPIEDAD            -- «el id es estable», «es alternativa, no identidad»
```

> *** Y por eso, cuando una clausula no aparece por su palabra, hay que buscar **la propiedad que protege**: ***
>
>   - **«por ordinal»** *-> **estable · conserva · no cambia**;*
>   - **«no neutraliza formato incompatible»** *-> **`ABSTIENE`** (y **asi se encontro**, en la ronda 162);*
>   - **«distinto no acredita mismo articulo»** *-> **`probable y nunca exacto`** (ronda 162);*
>   - **y «separar lo previsto de lo real»** *-> **`_con_precios`: «separar coste de lo usado del desembolso por
>     envases»** (ronda 156).*
>
> *** Las cuatro veces, **la palabra del plan no estaba y la propiedad si**. *** *Y **las cuatro** se encontraron
> **leyendo**, no buscando la palabra.*

## 4. Y B09 queda con **cuatro de cinco, y la quinta con sustituto**

```
  1) REUTILIZAR (Y SER INDEPENDIENTE)  HECHO
  2) EL BANCO DE PARES                 HECHO -- siete ensayos, con pos/neg, mezcla, precision a dos lados, gold
  3) LOS VEREDICTOS                    LOCALIZADOS -- y son CINCO (con `ABSTIENE`)
  4) LAS DOS REGLAS DEL EAN            `ABSTIENE` es su forma; y las fronteras, en tres ensayos
  5) LA PROHIBICION DEL ORDINAL        *** no esta por «ordinal»; la PROPIEDAD si: «el id es ESTABLE»,
                                       «lo que no cambia CONSERVA SU NUMERO» ***
```

> *** Y B09 **no tiene ninguna ausencia**: *** *las cinco clausulas tienen respuesta, **y la quinta la tiene por su
> propiedad** -- *que es **distinto de no tenerla**, y **es lo que distingue B09 de B08**.*
>
> *** En B08 se busco **siete palabras y dos pistas**, y **no estaba**. En B09 se busco **una palabra**, no estaba, y
> **se encontro la propiedad en cuatro ensayos.** ***
>
> *** La diferencia no es suerte: es **saber que buscar cuando la palabra falla**. Y eso es lo que esta ronda deja
> escrito. ***
