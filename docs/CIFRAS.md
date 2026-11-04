# Las cifras de la ultima ejecucion

**Ejecucion del 4 de noviembre de 2026.** Este documento tiene un solo trabajo:
llevar los numeros de **hoy**. Lo reescribe entero
`projects/cesta/cifras.py` al final de cada pasada.

Existe porque los demas documentos guardan sus cifras **con la fecha
en que se midieron**, y eso no es una cifra caducada sino un registro:
cambiarla no la actualiza, la falsifica. Asi los numeros de hoy viven
aqui, la historia se queda quieta, y `verificar_docs` encuentra aqui lo
de hoy y deja de avisar sin que nadie tenga que reescribir nada.

    uv run python -m projects.cesta.verificar_docs

---

## Catalogo

| | |
|---|---:|
| productos del catalogo | **52.982** |
| grupos comparables | **8.875** |
| productos comparables por kg/l/m | **43.090** |
| productos con codigo de barras | **25.649** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.672** |
| productos con certificado | **995** |
| productos con Nutri-Score | **8.545** |
| productos con tabla nutricional | **3.907** |
| productos con envase | **8.987** |

## Historico

    2.551.307 filas, 59 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.416 | 0 | 5.903 s | 2026-11-04 |
| carrefour | 16.782 | 1 | 2.735 s | 2026-11-04 |
| dia | 5.712 | 0 | 736 s | 2026-11-04 |
| mercadona | 4.272 | 0 | 102 s | 2026-11-04 |
| aldi | 2.709 | 0 | 88 s | 2026-11-04 |
| lidl | 91 | 0 | 5 s | 2026-11-04 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.047 |
| **de tarjeta** (no bajan lo que pagas en caja) | **765** |
| **solo por internet** (no bajan el ticket de la tienda) | **69** |
| ofertas que cuentan de verdad | 6.213 |
