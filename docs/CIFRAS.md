# Las cifras de la ultima ejecucion

**Ejecucion del 8 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **53.016** |
| grupos comparables | **8.886** |
| productos comparables por kg/l/m | **43.259** |
| productos con codigo de barras | **25.683** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.522** |
| productos con certificado | **1.046** |
| productos con Nutri-Score | **8.522** |
| productos con tabla nutricional | **3.896** |
| productos con envase | **8.961** |

## Historico

    2.760.653 filas, 63 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.313 | 0 | 6.162 s | 2026-11-08 |
| carrefour | 16.816 | 1 | 2.810 s | 2026-11-08 |
| dia | 5.686 | 0 | 729 s | 2026-11-08 |
| mercadona | 4.286 | 0 | 120 s | 2026-11-08 |
| aldi | 2.824 | 0 | 97 s | 2026-11-08 |
| lidl | 91 | 0 | 5 s | 2026-11-08 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.313 |
| **de tarjeta** (no bajan lo que pagas en caja) | **727** |
| **solo por internet** (no bajan el ticket de la tienda) | **81** |
| ofertas que cuentan de verdad | 5.505 |
