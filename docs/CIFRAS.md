# Las cifras de la ultima ejecucion

**Ejecucion del 13 de octubre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **51.725** |
| grupos comparables | **8.763** |
| productos comparables por kg/l/m | **42.550** |
| productos con codigo de barras | **25.081** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.701** |
| productos con certificado | **999** |
| productos con Nutri-Score | **8.437** |
| productos con tabla nutricional | **3.942** |
| productos con envase | **9.030** |

## Historico

    1.643.898 filas, 38 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.828 | 0 | 6.732 s | 2026-10-13 |
| carrefour | 16.149 | 1 | 5.713 s | 2026-10-13 |
| dia | 5.773 | 0 | 721 s | 2026-10-13 |
| mercadona | 4.213 | 0 | 114 s | 2026-10-13 |
| aldi | 2.683 | 0 | 97 s | 2026-10-13 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 5.732 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.083** |
| **solo por internet** (no bajan el ticket de la tienda) | **165** |
| ofertas que cuentan de verdad | 4.484 |
