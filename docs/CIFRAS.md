# Las cifras de la ultima ejecucion

**Ejecucion del 7 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.530** |
| grupos comparables | **8.852** |
| productos comparables por kg/l/m | **42.959** |
| productos con codigo de barras | **25.646** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.425** |
| productos con certificado | **1.046** |
| productos con Nutri-Score | **8.519** |
| productos con tabla nutricional | **3.912** |
| productos con envase | **8.981** |

## Historico

    2.685.077 filas, 62 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.897 | 1 | 6.327 s | 2026-11-07 |
| carrefour | 16.811 | 1 | 2.830 s | 2026-11-07 |
| dia | 5.704 | 0 | 713 s | 2026-11-07 |
| mercadona | 4.280 | 0 | 115 s | 2026-11-07 |
| aldi | 2.826 | 0 | 100 s | 2026-11-07 |
| lidl | 91 | 0 | 5 s | 2026-11-07 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.311 |
| **de tarjeta** (no bajan lo que pagas en caja) | **726** |
| **solo por internet** (no bajan el ticket de la tienda) | **82** |
| ofertas que cuentan de verdad | 5.503 |
