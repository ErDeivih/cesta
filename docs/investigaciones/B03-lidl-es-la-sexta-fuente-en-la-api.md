# B03 · **Lidl es la sexta fuente en la API.** Era la cache, y ahora esta medido

*(13 de octubre de 2026. **La hipotesis de la ronda anterior, comprobada con la prueba que se dijo.**)*

## 1. La prueba, y el resultado

*Se dijo: «la prueba es reiniciar el contenedor de la API, no suponer». Se reinicio.*

```
$ docker restart cesta-api-1
    sana en el intento 2

$ /api/estado
  version: 20261013-132451 · fecha: 2026-10-13
  cadenas: ['alcampo', 'aldi', 'carrefour', 'dia', 'LIDL', 'mercadona']

    alcampo    22816  2026-10-13  al_dia=True
    aldi        2476  2026-10-13  al_dia=True
    carrefour  16149  2026-10-13  al_dia=True
    dia         5760  2026-10-13  al_dia=True
    LIDL          77  2026-10-13  al_dia=True
    mercadona   4168  2026-10-13  al_dia=True
```

> **Seis cadenas, y `lidl` con 77.** *Asi que era la cache -- el proceso de la API llevaba corriendo desde
> antes de que el pipeline escribiera el gold de Lidl, y `catalogo.conexion()` no volvio a leer.*
>
> **Y el endpoint NO habia que tocarlo.** *La consulta ya lo incluia; **el que no lo veia era el proceso**. La
> hipotesis era correcta, y ahora es una medida.*

## 2. Y esto cierra tres cosas que se dieron por supuestas en el camino

  - **«Lidl no aparece porque `/api/estado` filtra por `CADENAS`»** -- *falso, y se dijo en la ronda 34.* **La
    consulta no filtra.**
  - **«El contenedor lee otra copia de los datos»** -- *falso: monta `F:\aprendizaje\scrap\data => /datos`.*
  - **«El pipeline no lleva a Lidl hasta gold»** -- *falso: esta con 77.*

> **Las tres eran causas plausibles, y las tres eran invenciones.** *La causa real era la mas tonta: **un
> proceso que llevaba horas corriendo y no habia vuelto a leer.*** **La vigesimosegunda** -- *y la mas
> instructiva, porque las tres veces la explicacion sonaba mejor que la verdad.*

## 3. Y con esto, el recorrido de Lidl esta HECHO

```
captura acotada (una pagina, robots primero)     HECHO
bronze con la zona acreditada                    HECHO
cobertura por campo y contador visible           HECHO
bronze -> silver -> gold                         HECHO
y en la API como sexta fuente, con su dia        HECHO
```

## 4. Y queda **una** cosa, que ya no es un misterio sino un diseno

**`/api/estado` da, por cadena, `productos` y `ultimo_dia`:**

```
alcampo    22816
lidl          77
```

> **Y esos dos numeros no son la misma clase de numero.** *22 816 es un catalogo; **77 son las fichas de una
> campana semanal**.* **Y el campo `productos` no lo distingue.**

**Y eso es exactamente lo que B03 pide, con estas palabras:**

> *«Permite comparar precios validos de articulos observados **sin presentar ausencias de captura como
> indisponibilidad** ni darle una cesta completa no cubierta.»*

**Asi que el trabajo que queda no es de plomeria: es de **forma de aparecer**. *Lidl necesita, junto a sus 77,
lo que su cobertura ya dice y que ya se escribe en `data/cobertura/lidl-2026-10-13.json`:*

```
cobertura: ofertas_semanales_parcial
con_precio: 77 de 79
aviso: «no certifica stock, ni identidad de producto, ni que un producto ausente se haya retirado»
```

> **Un `77` con eso al lado es un dato; un `77` solo es un catalogo pequeno.** *Y la diferencia es la que B03
> lleva pidiendo desde el principio.*
