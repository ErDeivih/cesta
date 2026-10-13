# B03 · **Correccion: la region YA estaba en silver.** El corte esta solo en gold

*(13 de octubre de 2026. **Cuarta correccion mia sobre Lidl, y la mas rapida de comprobar: bastaba mirar.**)*

## 1. Lo que dije, y lo que hay

*En la ronda 43 quedo escrito, como paso 1 de tres:*

> *«**`a_silver` tiene que llevarse `region` de bronze.** Hoy selecciona columnas y la deja caer.»*

**Y es falso, y se comprueba en una linea:**

```
lidl     silver: region=True · con valor=79 · distintas=1
alcampo  silver: region=True · con valor=0  · distintas=0
```

> **La region **ya estaba** en silver, con sus 79 valores.** *Y no hubo que tocar nada.*
>
> **Y el motivo, que es lo que yo habia supuesto mal**: *`a_silver` **no selecciona columnas: hace
> `df.with_columns([...])`**, que es **aditivo**.* *Anade las columnas que calcula y **deja todas las que
> venian de bronze** -- *incluida `region`, que es nueva y por eso viaja sola.*
>
> **Asi que «selecciona las columnas que le interesan» era una suposicion, y era la contraria.**

## 2. Y entonces el corte esta **solo** en gold

```
bronze:  region, 79 de 79      <- escrita (ronda 42)
silver:  region, 79 de 79      <- Y YA ESTABA, sin tocar nada
gold:    NO TIENE region       <- AQUI se corta
```

*Y ahi la causa **si** es una seleccion de columnas: el gold se construye con un `SELECT` explicito sobre
silver (`pipeline.py:706`), **y `region` no esta en esa lista**.*

> **Asi que de tres pasos queda uno.** *Y el que queda es justo **el que tiene la decision** -- reconstruir 37
> dias o no --, **que es lo que la ronda 43 decia que era el dificil**.*
>
> *O sea que la ronda 43 acerto en donde estaba el trabajo y fallo en el paso facil.* **Y el facil ni
> existia.**

## 3. Y la leccion, que ya es un patron de este paquete

**Cuatro correcciones sobre Lidl, y las cuatro por lo mismo:**

  1. *«`CADENAS` sigue teniendo cinco»* -- **tenia seis.**
  2. *«La integracion no existe»* -- **estaba en `ORDEN` desde antes.**
  3. *«`/api/estado` filtra por `CADENAS`»* -- **la consulta no filtraba.**
  4. *«`a_silver` deja caer la region»* -- **es aditivo, y ya la llevaba.**

> **Y las cuatro se comprobaron en menos de lo que costo escribirlas.** *`grep` de una linea, `DESCRIBE` de
> una consulta, un `docker inspect`.* **El error no fue de analisis: fue de no mirar antes de afirmar.**
>
> *Y es la vigesimocuarta de la misma familia, con la misma forma: **yo supuse, y el codigo tenia razon.***

## 4. Lo que queda, entonces, exacto

```
bronze   region, 79 de 79      HECHO
silver   region, 79 de 79      HECHO (sin tocar nada)
gold     region                PENDIENTE -- y es el paso con decision
vista    region                PENDIENTE (depende de gold)
API      region                PENDIENTE
pantalla region                PENDIENTE
```

*Y la decision del paso de gold sigue siendo la de la ronda 43, **con los mismos dos argumentos**:*
*reconstruir los **37 dias** -- porque `region` para Lidl **depende de la zona que se acredito cada dia**, y
dejarlo a medias daria un historico donde unas filas la dicen y otras no **sin poder saber por que** --, o
**no tocar el historico de las seis cadenas**, que es lo que B03 no pide.*
