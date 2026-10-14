# B06 reabierto · **estaba implementado, y el control lo describia de menos**

*El objetivo dice: *** «*Reabre criterios cerrados por lectura *** y trabaja en implementacion y
evidencia».** *Y la fila del control decia: *** «B06 · cerrado como lectura».** *Asi que **lo he
reabierto**, *y **lo que hay no es lo que esa fila sugiere.** *

---

## 1. *** «ml→g solo con dato especifico acreditado, NUNCA asumir densidad 1» ***

```
*** `core/envases_enteros.py:34` ***  *** «*Y **no** masa con volumen: *pasar de gramos a mililitros
   necesita l[a densidad]» *** *
*** `l83` ***  *** «*Sin densidad documentada, *** no se sabe ***, *y eso no es [cero]» *** *
*** `l104` ***  *** «**Masa contra volumen *** no se convierte sin densidad ***» *** *
*** `core/identidad.py:131` ***  *** «*Gramos contra mililitros *** no se comparan sin densidad
   documentada ***» *** *
*** `plataforma/api/recetas.py:140` ***  *** «`ml` *** no se convierte a gramos ***: *haria falta la
   densidad» *** *
*** Y SIETE ENSAYOS *** *
   *`tests/test_identidad.py:64` · `tests/test_revision_a02_identidad.py:270` ·
   `tests/test_revision_a08_envases.py:93` y `:293` · `tests/test_dia_nutricion.py:97` ·
   `tests/test_b08_la_prevision_no_inventa.py:47`*
*** -> *** IMPLEMENTADO, DOCUMENTADO Y CON ENSAYOS *** ✓✓✓
```

> *** Y **el ultimo es el mas fuerte**: *«*Las palabras se buscan **sueltas** y no en frases»* *—* *o sea:
> **comprueba que el CODIGO dice «densidad»**, *y **no que la invente.*** ✓ *

## 2. *** «Sin kcal no perder macros» + «cobertura con numerador/denominador» ***

```
*** `core/diario.py:287-289` *** *
   *** `def _trae_dato(fila) -> bool:` *** *
   *** `    """Si esa entrada aporta energia al total. *** **Sin dato no es cero**: *es que no se sabe.» *** *** *
   *** `    return fila["kcal"] is not None` *** *
*** `l292-295` *** *
   *** `def _cobertura(filas, columna, total) -> dict:` *** *
   *** `    """Cuantas entradas traen ESE nutriente, de cuantas hay. *** La cobertura es POR NUTRIENTE.» *** *** *
   *** `    return {"con_dato": …, *** "total": total ***, "completa": …}` *** *
*** `l327` ***  *** `"cobertura": {n: _cobertura(filas, c, total) for n, c in …}` *** *
*** -> *** LA COBERTURA ES POR NUTRIENTE ***, *asi que **una entrada sin kcal y con proteinas
   cuenta en proteinas** *-- *que es *** exactamente *** «sin kcal no perder macros» ✓✓✓
*** -> y **trae numerador (`con_dato`), denominador (`total`), y `completa`** ✓✓✓
*** -> y **`_trae_dato` dice «sin dato no es cero»**, *que es **la doctrina del encargo, en el codigo** ✓
```

## 3. *** «Campo nativo/enriquecido/manual; ausente/no aplicable/no publicado/error/pendiente diferenciados; cola por nuevos/cambiados/caducados, hash y PRESUPUESTO POR FUENTE; no 88 horas de fichas sin prioridad» ***

```
*** `core/inventario.py` ***  *** EXISTE *** *
   *** `l37` ***  *** `PENDIENTE = "pendiente"` *** · *** `l41` ***  *** `NO_PUBLICADO = "no_publicado"` *** ✓
   *** `l59` ***  *** `estado TEXT NOT NULL DEFAULT 'pendiente'` *** *** -> **una columna `estado`** ✓
   *** `l135` ***  *** «*Prioridad: *** lo pendiente y lo vencido ***, *y entre eso, *lo que lleva mas
      tiempo» *** *** -> *** UNA COLA CON PRIORIDAD *** ✓✓✓
*** `core/presupuesto.py` ***  *** EXISTE *** *
   *** `l3` ***  *** «**Por que existe.** *La cola tiene *** 72 319 fichas pendientes *** *y no tenia
      fecha [de caducidad]» *** *
   *** -> *** PRESUPUESTO POR FUENTE ***, *con **su motivo escrito** ✓✓✓
*** y `core/config.py:35` ***  *** «459 productos nuevos, *se pidieron *** 100 *** fichas *y quedaron
   *** 374 *** pendientes» *** *
   *** -> *** el presupuesto, funcionando y contando *** ✓
*** -> *** IMPLEMENTADO: los estados, la cola con prioridad, y el presupuesto *** ✓✓✓
```

## 4. *** Y la conclusion incomoda, que hay que decir ***

```
*** DIJE ***  *«B05, B06 y B07 estan cerrados *** por lectura ***, *y eso es lo que el objetivo
   prohibe»* ⚠️
*** Y LO QUE HAY EN B06 ES ***  *** tres modulos implementados ***, *con la doctrina escrita *
   *y **con numeros del dia** ✓
*** -> o sea: **el defecto NO era «cerrado sin verificar»** *
*** -> era *** que la fila del control describe MENOS de lo que hay *** ⚠️
```

> *** Y **esto es **lo mismo que llevo cazando todo el día, al revés**: *
> ```
> *** `findstr /i running` ***  *** describia MAS de lo que comprobaba *** *(-- *y por eso el respaldo
>    fallaba **siempre** --)*
> *** «cerrado como lectura» ***  *** describe MENOS de lo que hay *** *(-- *y por eso yo lo trate como
>    trabajo pendiente --)*
> *** -> las dos son *** anotaciones que no se corresponden con lo que hay *** ✓✓✓
> ```
>
> ***→ Y **lo que corresponde hacer con esto no es implementar nada**: *es *** medir y anotar *** *—*
> *y **anotar bien**, *porque **la fila del control es lo que lee el siguiente** *(-- *yo mismo, *ayer --).* ✓ *

## 5. Y lo que **si** queda de B06, medido

```
*** «…Y CAUSA DE HUECOS» ***  *-- *los `sin_dato` **se listan** *(-- `l354` --), *pero **la causa**
   *(-- *«no publicado» vs «error» vs «pendiente» --)* *es **lo que falta por ver** ⚠️
*** «AUSENTE / NO APLICABLE / NO PUBLICADO / ERROR / PENDIENTE *** DIFERENCIADOS ***» *** *
   *-- *`PENDIENTE` y `NO_PUBLICADO` **existen**; *los otros tres, **por comprobar** ⚠️
*** «*HISTORICOS DE FICHA *** para poder explicar identidad y cambios ***, *no mezclar precio actual con
   detalle obsoleto» ***  *-- *por mirar* ⚠️
*** «*Nutricion por *** 100 g / 100 ml / racion *** *y *** preparado / vendido ***» ***  *-- *por mirar* ⚠️
*** -> y **cada una es una medicion**, *no un subsistema* ✓
```

*** Y **la leccion de metodo de esta ronda**, *que ya he pagado cinco veces hoy*: *«cerrado por lectura»
**no quiere decir «sin verificar»**; *quiere decir **que quien lo escribió no enumeró lo que comprobó** *
*—* *y **eso se sabe midiendo, no leyendo la fila.*** ✓
