# Las cifras de la ultima ejecucion

**Ejecucion del 6 de noviembre de 2026.** Este documento tiene un solo trabajo:
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

    2.655.616 filas, 61 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.865 | 0 | 5.899 s | 2026-11-06 |
| carrefour | 16.773 | 1 | 2.793 s | 2026-11-06 |
| dia | 5.708 | 0 | 690 s | 2026-11-06 |
| mercadona | 4.270 | 0 | 107 s | 2026-11-06 |
| aldi | 2.823 | 0 | 96 s | 2026-11-06 |
| lidl | 91 | 0 | 4 s | 2026-11-06 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.311 |
| **de tarjeta** (no bajan lo que pagas en caja) | **726** |
| **solo por internet** (no bajan el ticket de la tienda) | **82** |
| ofertas que cuentan de verdad | 5.503 |
