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
| productos del catalogo | **52.546** |
| grupos comparables | **8.853** |
| productos comparables por kg/l/m | **42.985** |
| productos con codigo de barras | **25.691** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.425** |
| productos con certificado | **1.046** |
| productos con Nutri-Score | **8.526** |
| productos con tabla nutricional | **3.911** |
| productos con envase | **8.975** |

## Historico

    2.707.900 filas, 62 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.834 | 0 | 271 s | 2026-11-07 |
| carrefour | 16.811 | 1 | 416 s | 2026-11-07 |
| dia | 5.704 | 0 | 81 s | 2026-11-07 |
| mercadona | 4.280 | 0 | 106 s | 2026-11-07 |
| aldi | 2.826 | 0 | 15 s | 2026-11-07 |
| lidl | 91 | 0 | 3 s | 2026-11-07 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.309 |
| **de tarjeta** (no bajan lo que pagas en caja) | **727** |
| **solo por internet** (no bajan el ticket de la tienda) | **80** |
| ofertas que cuentan de verdad | 5.502 |
