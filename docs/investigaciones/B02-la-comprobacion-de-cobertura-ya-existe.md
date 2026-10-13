# B02 · **La comprobacion de cobertura YA EXISTE** (`core/cobertura.py`) -- y eso deja B02 en casi nada

*(13 de octubre de 2026. **La ultima medida, y la que deja el paquete reducido a su tamano real.**)*

## 1. Lo que hay

```
core/cobertura.py:29:   caidas = cobertura.revisa(df, "alcampo")
core/cobertura.py:194:  cobertura vio media tienda desaparecida -- ya devuelve error, asi que no llega
```

**Y el fichero de cobertura de Lidl, con sus trece campos:**

```
fuente · cobertura · url · region · fecha
fichas_leidas · productos_padre · guardados · fuera_de_alcance · en_revision
con_precio · precios_con_vigencia_comprobada · aviso
```

> **O sea que hay **dos** piezas, y las dos existen:**
>
>   - **`core/cobertura.py`** *-- **revisa** la cobertura, **y para las otras cadenas tambien** (`"alcampo"`), y
>     **«ya devuelve error»** si ve media tienda desaparecida*;
>   - **y el fichero `data/cobertura/<fuente>-<dia>.json`** *-- con sus trece campos -- **que hoy solo lo escribe
>     Lidl**.*

## 2. Y entonces B02 queda en esto, que es todo lo que falta

```
HECHO YA:
  core/cobertura.py        revisa la cobertura de las cadenas, y devuelve error si falta medio catalogo
  data/cobertura/lidl-*.json   el fichero, con trece campos, escrito por Lidl
  Alcampo y Carrefour      cuentan reintentos, bloqueadas, vueltas, y POR QUE fallan (_por_que_fallan)
  los dos                  no inventan catalogo cuando no pueden leer

FALTA:
  1) QUE LOS OTROS ESCRIBAN SU FICHERO -- reusando la forma del de Lidl,
     con lo que ya cuentan, mas el TIEMPO (lo unico que no se mide)
  2) LOS FIXTURES en tests/fixtures/ (la carpeta esta y vacia; el plan pide seis casos)
  3) Y LA DECISION DEL NAVEGADOR -- del propietario, ya preguntada
```

> **Tres cosas, y dos son de escribir poco.** *Y la tercera no es codigo.*
>
> ***O sea que B02 -- que en la ronda 105 parecia «construir un sistema de resistencia entero» -- es: reusar una
> forma que existe, rellenarla con datos que ya se calculan, y cronometrar.***

## 3. Y el contraste, que es lo unico que vale la pena decir ya

```
RONDA 105 dijo:  «no existe nada»  ->  habria justificado ESCRIBIR UN COLECTOR DE CERO
RONDA 112 dice:  hay la revision, hay el fichero, hay los contadores, hay el motivo,
                 y hay once ensayos de colectores incluido uno del WAF
```

> **Y entre las dos hay siete rondas, y **ninguna de las siete encontro nada que no estuviera ahi desde el
> principio**.** *Lo unico que cambio fue **cuanto se leyo antes de hablar**.*
>
> *La ronda 105 miro **un `grep`**. La 112 miro **`core/cobertura.py` y el fichero entero** -- y las dos cosas
> llevaban ahi todo el tiempo.*

## 4. Y la regla, que ya no hace falta repetir mas

**En un paquete nuevo:**

```
1) ls        -- que hay
2) leer los ficheros que salgan, ENTEROS
3) y solo despues, grep -- y con los nombres del codigo, no con los mios
```

*Las siete rondas de B02 son la demostracion, con el coste incluido: **siete rondas para recorrer esas tres
lineas**.*

> *Y el unico consuelo, que ya esta escrito y sigue siendo cierto:* **el error no llego al codigo.** *Y en la
> ronda 105, con la conclusion que habia, **habria llegado**.*
