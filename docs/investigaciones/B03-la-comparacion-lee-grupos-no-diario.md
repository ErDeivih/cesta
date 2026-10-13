# B03 · **La causa de los seis fallos**: la comparacion no lee `diario`, lee `grupos`

*(13 de octubre de 2026. **El diagnostico, en una linea de DuckDB.**)*

## 1. El error, tal cual

*Se reaplico el cambio y se corrio **un solo** test, para ver el error en vez de suponerlo:*

```
E  _duckdb.BinderException: Binder Error: Referenced column "region" not found in FROM clause!
E  Candidate bindings: "precio_cent", "seccion", "nutricion", "precio_unidad_cent", "origen"

E  LINE 3: ..._cent, precio_unidad_cent, comparacion_fiable, ean, marca, region
E                                                                        ^
```

> **`Referenced column "region" not found in FROM clause`.** *No es un indice desplazado, ni un `zip`, ni un
> contrato de forma.* **Es que la tabla sobre la que se consulta no tiene esa columna.**

## 2. Y la suposicion que fallaba, que era mia

*En la ronda 47 quedo escrito, y era el punto de partida de todo el intento:*

> *«La region esta en la vista `diario` y la API no la expone en ningun sitio... **el sitio donde importa es la
> comparacion** (`donde_comprar`).»*

**Y eso da por hecho que `donde_comprar` lee `diario`.** *Y **no lo lee**:* **lee `grupos`.**

```
FROM grupos          <- y no: FROM diario
```

*Y `grupos` es la tabla del **modelo de emparejamiento** (`data/gold/matching/`, «el modelo versionado de la
Fase 1»), **no la serie de precios**.* **Son dos cosas distintas, y yo las trate como la misma.**

> *Asi que «la region esta en la vista, luego la comparacion puede usarla» era **un salto de dos tablas**.*
> **La vigesimoquinta, y con la misma forma que las otras: yo supuse, y el codigo tenia razon.**

## 3. Y lo que esto cambia del plan, que es bastante

**Llevar la zona a la comparacion NO es «anadir una columna al `SELECT`».** *Es:*

  1. **que `grupos` tenga `region`** -- *y `grupos` sale de `matching`, que es **otro modelo con su propio
     contrato***, no de la serie de precios;
  2. **y decidir que hace `matching` con la zona**: *si un producto puede tener precios de dos zonas
     emparejados en el mismo grupo, **el grupo deja de ser «un producto» y pasa a ser «un producto en una
     zona»*** -- *que es la misma pregunta del grano de `diario`, una capa mas arriba*;
  3. **y solo despues** el `SELECT` de `donde_comprar`.

> **O sea que el paso que quedaba en B03 no era el ultimo: era el penultimo de una cadena que empieza en
> `matching`.** *Y decirlo asi es lo que evita que alguien lo intente otra vez por donde yo lo intente.*

## 4. Y las tres cosas que se ganaron con el intento fallido

  - **La causa, medida.** *`grupos` no tiene `region`, y ahora se sabe por que y donde mirar.*
  - **La forma de anadirlo cuando toque**: **al final del `SELECT`**, *que **si** es lo correcto para no mover
    indices* -- *y eso se comprobo: el error no fue de indices.*
  - **Y la refutacion de una hipotesis que llevaba tres rondas aparcando el cambio.** *Aparcarlo estaba bien
    mientras la razon fuera la duda; **ahora la razon es mejor: falta una columna dos capas mas abajo.***

## 5. Estado de B03, y lo que queda exacto

```
captura acotada · bronze con zona (79/79) · cobertura y contador
silver (79/79) · gold (77/77, historico rehecho) · la vista (77/77) · /api/estado
la pantalla ensena la cobertura · Y CORRE EN LA PASADA DIARIA
club, fechas, nutricion y ausencias   PROBADOS
LA ZONA EN LA COMPARACION             PENDIENTE -- y ahora se sabe DONDE:
                                        empieza en `grupos` / `matching`, no en `donde_comprar`
```

*Y el arbol quedo limpio: el cambio se deshizo y la suite vuelve a `2019 pasan, 0 fallan`.*
