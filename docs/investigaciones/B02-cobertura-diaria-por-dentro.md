# B02 · **`cobertura_diaria.py` por dentro**: 162 lineas, tres funciones, y un veredicto

*(13 de octubre de 2026. **La ultima medida. Y con ella B02 queda sin ninguna incognita.**)*

## 1. Lo que hay dentro

```
projects/cesta/cobertura_diaria.py   -- 162 lineas

   53:  def filas_por_dia(dias: int = DIAS_DE_VENTANA) -> dict[str, dict[str, int]]
   75:  def veredicto(serie: dict[str, int], hoy: str, dias: int = DIAS_DE_VENTANA, ...)
  108:  def main(argv: list[str] | None = None) -> int
```

> **Tres funciones y un `main`.** *Y los nombres dicen lo que hace:*
>
>   - **`filas_por_dia`** *-- **cuantas filas por dia**, que es **la medida que B02 pide** -- *«productos
>     unicos», y de paso **la serie** para ver caidas;*
>   - **`veredicto`** *-- **un juicio** sobre la serie: *si hoy se ha caido respecto a la ventana;*
>   - **`main`** *-- con `--fecha` y `--dias`, o sea **una CLI que se puede correr para cualquier dia**.*

## 2. Y no parece escribir fichero por cadena

**Las tres funciones calculan y juzgan** *-- y **escribir un fichero por cadena y dia no aparece en los nombres**.*
*Lo cual **encaja con lo medido en la ronda 111**: los colectores escriben **`save_raw` y `write_parquet`**, y
**nada mas**; y de los seis ficheros de cobertura **solo existe el de Lidl**.*

> **Asi que la conclusion, con lo leido, es:**
>
>   - **la comprobacion existe** *(`core/cobertura.py`)*;
>   - **el veredicto por dia y por ventana existe** *(`cobertura_diaria.py`, 162 lineas con su CLI)*;
>   - **y el fichero por cadena y dia lo escribe solo Lidl** *-- *y lo escribe **su colector**, no este modulo.*

**O sea: B02 no necesita ni inventar la comprobacion ni el veredicto. Necesita que los colectores de Carrefour y
Alcampo escriban su fichero, con la forma del de Lidl.**

## 3. Y B02 queda asi, sin incognitas y sin adornos

```
HECHO YA (cinco cosas, todas ahi desde el principio):
  Alcampo      RetoWAF (13 usos) · AVANCE_MINIMO · CORTES_PARA_RENDIRSE · MAX_RENOVACIONES · `detener`
  Carrefour    VUELTAS_DE_RESCATE · backoff exponencial · VUELTAS_SIN_BLOQUEO · `_por_que_fallan`
  los dos      no inventan catalogo cuando no pueden leer
  core/cobertura.py            la revision, con error si falta medio catalogo
  cobertura_diaria.py          162 lineas: filas por dia, veredicto, y CLI con --fecha y --dias
  tests/                       11 ensayos de colectores, uno del WAF (9,3 KB)

LO QUE FALTA, Y SON TRES COSAS:
  1) que Carrefour y Alcampo ESCRIBAN su fichero de cobertura -- la forma es la de Lidl (13 campos)
     y el contenido YA SE CALCULA; falta el TIEMPO, que es lo unico que no se mide
  2) los FIXTURES en tests/fixtures/ (la carpeta esta y vacia; el plan pide seis casos)
  3) la DECISION DEL NAVEGADOR -- del propietario, ya preguntada, y no es codigo
```

## 4. Y esto es todo lo que B02 ha dado, y lo que ha costado

**Ocho rondas de lectura, ninguna linea de codigo, y cinco correcciones de mis propias conclusiones.**

> *Y el resultado es que **B02 es mas pequeño que cualquiera de mis cinco estimaciones** -- y que **la primera de
> ellas («construir lo que no hay») habria producido un colector duplicado al lado de dos que funcionan**.*
>
> ***Lo unico que estas ocho rondas han comprado es que ese error no se escribiera.*** *Que, mirado con lo que
> costaba, es el mejor resultado posible de un error; y mirado con lo que se tardo, es un aviso sobre como
> empieza un paquete.*
>
> **La regla, ya sin discusion: `ls`, luego leer entero, y `grep` al final y con los nombres del codigo.**
