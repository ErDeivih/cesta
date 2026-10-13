# B03 · **Lidl esta en gold con 77** -- y `/api/estado` no lo ve. Lo medido, y lo que falta comprobar

*(13 de octubre de 2026. **Corrige lo que escribi en la ronda anterior.**)*

## 1. La correccion, primero

*En la ronda 33 escribi:*

> *«`/api/estado` informa por `CADENAS` -- las comparables --, y Lidl no esta en esa lista, con su motivo.»*

**Y eso era una suposicion mia, y es falsa.** *Se leyo la consulta del endpoint, y **no filtra por `CADENAS`**:*

```python
filas = con.execute("""
    WITH ultimas AS (SELECT fuente, max(fecha) AS fecha FROM diario GROUP BY fuente)
    SELECT d.fuente, count(DISTINCT d.id_fuente) AS productos, u.fecha::VARCHAR AS ultimo_dia
      FROM diario d JOIN ultimas u ON d.fuente = u.fuente AND d.fecha = u.fecha
     GROUP BY d.fuente, u.fecha ORDER BY d.fuente
""").fetchall()
```

> **No hay `WHERE fuente IN (...)`. Consulta `diario` entero.** *Asi que si Lidl esta en `diario`, **sale**.* **Y mi explicacion de por que no salia era inventada.**

## 2. Y Lidl **esta** en `diario`

*Consultado en el host, con `catalogo.conexion()`:*

```
  --- fuentes en diario (gold) ---
    alcampo       44001  2026-10-13
    aldi           3312  2026-10-13
    carrefour     17402  2026-10-13
    dia            6346  2026-10-13
    lidl             77  2026-10-13     <- ESTA
    mercadona      4496  2026-10-13
```

> **Seis fuentes, y `lidl` con 77 productos.** *Asi que el pipeline si lo llevo hasta gold.*

## 3. Y el endpoint sigue devolviendo cinco, con la version NUEVA

```
version: 20261013-132451 · fecha_datos: 2026-10-13
cadenas AHORA: ['alcampo', 'aldi', 'carrefour', 'dia', 'mercadona']
campos de una cadena: ['al_dia', 'cadena', 'productos', 'ultimo_dia']
```

**Y `20261013-132451` es la version que acabo de publicar** -- *o sea que el endpoint si esta leyendo datos de hoy.* **Pero no ve `lidl`.**

## 4. Y las dos cosas que se descartaron, medidas

  - **No es el montaje.** `docker inspect cesta-api-1` dice: **`F:\aprendizaje\scrap\data => /datos`** --
    *el contenedor lee el `data` del host.* **Asi que no es que tenga otra copia.**
  - **No es un filtro por `CADENAS`.** *Ya visto arriba: la consulta no lo tiene.*

**Y lo que queda, sin comprobar**: *que el proceso de la API tenga la conexion o la respuesta en cache.*
*Lleva corriendo desde antes de que el pipeline escribiera el gold de Lidl* -- *asi que es lo mas probable,
**y no esta comprobado**.*

> **Asi que esto queda como lo que es: dos hechos medidos y una hipotesis dicha como tal.** *Se midio que Lidl
> esta en `diario`; se midio que el endpoint no lo devuelve; y **`catalogo.conexion()` cachea** es lo que hay
> que comprobar -- **reiniciando el contenedor de la API, que es la prueba y no una suposicion.***

## 5. Y lo que esto cambia del plan

**El trabajo que queda ya no es «que la consulta incluya a Lidl»** -- *la consulta ya lo incluiria.* **Es:**

  1. **Comprobar si es cache** *reiniciando `cesta-api-1` y volviendo a preguntar.* *Si Lidl aparece, el
     endpoint no habia que tocarlo.*
  2. **Y entonces la pregunta que si queda**: *`productos: 77` al lado de `22816` de Alcampo*, **sin nada que
     diga que 77 son fichas de una campana semanal y 22 816 un catalogo.** *Eso si es trabajo, y es el que B03
     pide: **una forma de aparecer que diga que el catalogo es parcial.***

> **Y decirlo asi importa**: *me habia inventado una causa, y la causa era otra.* **La vigesimoprimera.**
