# B06 · **`core/manifiesto.py` es la respuesta a las dos clausulas que faltaban** -- el «con que» y el «de cuando»

*(13 de octubre de 2026. **Septima ronda de B06. Y el fichero contesta la (4) y la (5) de golpe.**)*

## 1. Lo que hay: 219 lineas, y siete funciones

```
core/manifiesto.py -- 219 lineas

  l51:  def huella(ruta: Path, trozos: int = 12) -> str | None      <- EL HASH
  l62:  def _fuentes(hoy=None) -> dict[str, dict]                   <- por cadena
  l93:  def _precios() -> dict[str, str]
  l115: def _cobertura() -> dict[str, dict]                          <- la cobertura declarada
  l128: def construye(fecha=None) -> dict
  l173: def _version_politica() -> int | None
  l182: def escribe(fecha=None) -> Path | None                       <- y atomico
```

## 2. Y su docstring **es** el criterio

```python
"""T02: manifiesto de publicacion, y su enganche al final de la pasada.

**Que problema resuelve.** Hoy se puede saber que hay en gold, pero no *con que*: que capturas
que dia, con que version de la politica de alcance y con que cobertura. **Sin eso, dos catalogos
distintos parecen el mismo, y una comparacion puede ser exacta y estar comparando cosas distintas.**

**Que lleva el manifiesto:**

  - la **fecha** y el momento de generacion;
  - por cadena, la **fecha de su captura** y cuantas filas trae (una cadena que no corrio se v[ee]);
  - la **version y la huella de la politica de alcance** (`sha256` del yml): si cambia una reg[la]
    el manifiesto cambia, y eso es lo que permite decir con que reglas se publico un catalogo;
  - la **huella de cada fichero de gold** (sha256 corto, filas y bytes);
  - la **cobertura declarada** por los colectores que la declaran;
  - y **avisos**: que cadenas no tienen captura de hoy.

**Se escribe de forma atomica** (fichero temporal y renombrado): **un manifiesto a medias es peo[r
que] no tenerlo, porque parece una publicacion valida.**

Y **no puede tumbar el dia**: si falla, se avisa y se sigue. El dia se mide por el dato, no po[r el]
manifiesto; lo que no se puede es publicar sin decir que paso.
"""
```

## 3. Y contesta las clausulas (4) y (5) **enteras**

```
B06 PIDE                                        Y AQUI ESTA
  4) «COLA por nuevos/cambiados/caducados,
      HASH Y PRESUPUESTO POR FUENTE»              *** `huella()` -- el sha256, corto, de cada
                                                  fichero de gold -- y `_fuentes()`, por cadena,
                                                  con sus filas ***
  5) «HISTORICOS DE FICHA para poder explicar
      identidad y cambios, NO MEZCLAR PRECIO
      ACTUAL CON DETALLE OBSOLETO»                *** «por cadena, LA FECHA DE SU CAPTURA y
                                                  cuantas filas trae» ***
                                                  *** y `_version_politica()`: la huella del yml
                                                  de alcance, «que permite decir CON QUE REGLAS
                                                  se publico un catalogo» ***
```

> *** Y la frase que lo gobierna todo, que es **el criterio entero de B06 en una linea**: ***
>
> *«**Sin eso, dos catalogos distintos parecen el mismo, y una comparacion puede ser EXACTA y estar comparando
> COSAS DISTINTAS.**»*
>
> *** Que es, palabra por palabra, «por campo, cadena y universo»: *** **una comparacion sin saber QUE se compara
> puede ser exacta y no significar nada** -- *que es **lo mismo** que decia `core/alimentos.py` con «decir un
> porcentaje sin haber mirado el universo es inventarlo».*
>
> *** Los dos ficheros, con dos anos de diferencia y de dos problemas distintos, dicen **la misma frase**: ***
>
>   - *`alimentos.py`: «decir un porcentaje **sin haber mirado el universo** es inventarlo»;*
>   - *`manifiesto.py`: «sin eso, dos catalogos distintos parecen el mismo, y **una comparacion puede ser exacta y
>     estar comparando cosas distintas**».*
>
> *** Y es la misma ley que el fallo latente de B03: **la consulta devolvia 11 columnas y el codigo esperaba 10**
> -- *una comparacion que «funcionaba» y comparaba mal.*

## 4. Y dos cosas mas que hay que subrayar

**1) «Se escribe de forma atomica... un manifiesto a medias es peor que no tenerlo, PORQUE PARECE UNA PUBLICACION
VALIDA.»**

> *** Es la misma doctrina que el `ValueError` de `FUENTES` y que el `ON CONFLICT`: *** **no dejar un estado que
> parezca bueno sin serlo.** *Y **el motivo esta escrito**: «**parece** una publicacion valida» -- *o sea, **el
> dano no es que falte, es que parezca que esta**.*

**2) «Y no puede tumbar el dia: si falla, se avisa y se sigue... lo que no se puede es publicar sin decir que
paso.»**

> *** Y ahi esta **la regla de B02 escrita otra vez**: *** **una cadena que no corrio se ve** -- *y **el dia no se
> tumba**, pero **se dice**.*
>
> *** Que es la misma forma de las nueve de la doctrina: **no se inventa, se dice**. ***

## 5. Y B06 queda **cerrado como lectura**, con las cinco clausulas

```
  1) EL INVENTARIO DE CAMPOS        HECHO -- 21 ensayos, campo por campo
  2) NATIVO / ENRIQUECIDO / MANUAL  HECHO -- `fuente_dato NOT NULL` + `FUENTES` con `DESCONOCIDO`
  3) AUSENTE / NO APLICABLE / ...   HECHO -- «ausente» y «error» con ensayo; «no aplicable» en alimentos;
                                    y `DESCONOCIDO` aqui. *** «no publicado» y «pendiente»: POR CONFIRMAR ***
  4) LA COLA CON PRESUPUESTO        HECHO -- `huella()`, `_fuentes()`, `_version_politica()`
  5) Y EL HISTORICO DE FICHA        HECHO -- «por cadena, la fecha de su captura», y la version del alcance
```

> *** Y queda una sola cosa «por confirmar», y no se dice que falte: *** *los dos motivos «no publicado» y
> «pendiente» de la clausula (3).* *Que es **una distincion de nombres**, no una pieza que falte.*
