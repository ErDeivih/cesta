# Las cifras de la ultima ejecucion

**Ejecucion del 29 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.348** |
| grupos comparables | **8.737** |
| productos comparables por kg/l/m | **42.175** |
| productos con codigo de barras | **25.423** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.694** |
| productos con certificado | **723** |
| productos con Nutri-Score | **8.398** |
| productos con tabla nutricional | **3.818** |
| productos con envase | **9.074** |

## Historico

    1.135.124 filas, 24 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.635 | 0 | 6.379 s | 2026-09-29 |
| carrefour | 16.529 | 4 | 5.631 s | 2026-09-29 |
| dia | 5.723 | 0 | 652 s | 2026-09-29 |
| mercadona | 4.335 | 0 | 99 s | 2026-09-29 |
| aldi | 2.126 | 0 | 89 s | 2026-09-29 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.830 |
| **de tarjeta** (no bajan lo que pagas en caja) | **581** |
| **solo por internet** (no bajan el ticket de la tienda) | **326** |
| ofertas que cuentan de verdad | 6.923 |
