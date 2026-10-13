# B03 · Lidl — **lo que dice `docs/LIDL.md`, y que no es lo que yo estaba citando**

*(13 de octubre de 2026. **B03 empieza por leer, y lo primero que se lee corrige una creencia mia.**)*

## 1. El hallazgo, y me corrige a mi

`docs/LIDL.md` **empieza asi**:

> ## Actualizacion verificada el 6 de octubre de 2026
>
> La conclusion de septiembre que sigue abajo **no debe usarse para descartar Lidl**. La pagina publica de
> ofertas semanales entrega **JSON en `data-grid-data`**: se han extraido **76 fichas/variantes (70
> productos padre)**, **con precios regionales y condiciones de club**. Existe un **piloto probado**,
> `projects/cesta/sondear_lidl.py`, **aun sin integracion en la ingesta**.

*Y debajo, marcado como historico:*

> ## Reconocimiento del 7 de septiembre de 2026 (conservado como historico)
>
> Resumen en una linea: **lidl.es no publica precios de alimentacion**, asi que un scraper de su web no
> serviria para lo que queremos.

### Y lo que yo estaba citando era **lo segundo**

**`docs/MATRIZ-DE-ACEPTACION.md`, seccion 8, decia:**

> *«`docs/LIDL.md` dice en una linea que **«lidl.es no publica precios de alimentacion»**»*

**Es la conclusion de septiembre, y el propio documento dice que no debe usarse para descartar Lidl.** ✗

> **Y la diferencia no es de matiz**: *«no publica precios» y «publica ofertas semanales parciales con
> precios regionales» son dos afirmaciones contrarias.* **La primera descarta Lidl; la segunda dice que hay
> algo que integrar.**
>
> **Y lo que el plan pide en B03 es exactamente lo segundo**: *«Eliminar veto global a precios validos de
> Lidl: permitir candidatos observados, vigentes y de identidad acreditada.»* **Un veto global sobre una
> fuente que si publica algo es lo que hay que quitar.**

### Y lo que si estaba bien en mis textos

*Los documentos que escribi en A05 y despues dicen:*

> *«Lidl publica **ofertas semanales parciales**, y meterlo en las comparaciones haria que pareciera tener
> precio para cosas que no cataloga.»*

**Eso es correcto, y coincide con `LIDL.md`.** *Lo que estaba mal era la celda de la matriz*, que citaba la
frase de septiembre -- **y la matriz es un documento de aceptacion, que es donde mas caro sale citar mal.**

## 2. Lo corregido

**La celda 8 de la matriz**, con la correccion dicha dentro: *que citaba la conclusion de septiembre, que el
propio `LIDL.md` dice que no debe usarse, y lo que dice la actualizacion del 6 de octubre.*

> **Y la frase que resume el cambio**: *Lidl **no esta descartado: esta sin integrar** -- que son dos cosas
> distintas, y la celda decia la primera.*

## 3. Y lo que esto deja para B03, que ahora tiene una forma distinta

*Con la correccion delante, B03 no es «ver si Lidl se puede capturar»* -- **eso ya se sabe que si, y hay un
piloto** --, **sino cuatro cosas concretas:**

  1. **Integrar el piloto en la ingesta diaria** -- *«ejecucion desde el mismo runner diario»* --, que es
     lo que falta desde el 6 de octubre.
  2. **El ambito regional, acreditado.** *«validar tienda/region y **no convertir CP en id de region sin
     correspondencia**»* -- *y el piloto ya trae **precios regionales**, asi que la pregunta es de donde
     salen.* **Es el dato que hay que pedirle al propietario si no consta**, *y solo ese.*
  3. **El veto global, quitado.** *«permitir candidatos observados, vigentes y de identidad acreditada, y
     **marcar los no observados como desconocidos**»* -- *no como ausentes.*
  4. **Y la cesta**: *«Lidl no gana una cesta completa si faltan lineas; si puede ofrecer **una linea exacta
     con precio valido** o una alternativa que la persona acepte».*

## 4. Lo que falta leer, y sigue faltando

*De los siete ficheros, se ha leido **uno** -- `docs/LIDL.md`, 3 KB -- y es el que ha corregido la
creencia.* **Quedan seis, y son el codigo:**

```
collectors/lidl.py   11,7 KB     descubrir_lidl.py   9,9 KB     fichas_lidl.py  6,7 KB
ficha_lidl.py         7,7 KB     sondear_lidl.py     3,8 KB     run.py
```

*Y `sondear_lidl.py` es el piloto probado, asi que es el primero de los seis.*
