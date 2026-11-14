# Las cifras de la ultima ejecucion

**Ejecucion del 13 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **58.449** |
| grupos comparables | **9.457** |
| productos comparables por kg/l/m | **47.236** |
| productos con codigo de barras | **25.594** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **12.786** |
| productos con certificado | **1.139** |
| productos con Nutri-Score | **8.487** |
| productos con tabla nutricional | **3.904** |
| productos con envase | **8.977** |

## Historico

    3.034.799 filas, 68 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 28.639 | 0 | 9.829 s | 2026-11-13 |
| carrefour | 16.708 | 1 | 3.257 s | 2026-11-13 |
| dia | 5.703 | 0 | 1.021 s | 2026-11-13 |
| mercadona | 4.278 | 0 | 434 s | 2026-11-13 |
| aldi | 3.039 | 0 | 445 s | 2026-11-13 |
| lidl | 82 | 0 | 5 s | 2026-11-13 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 5.676 |
| **de tarjeta** (no bajan lo que pagas en caja) | **1.621** |
| **solo por internet** (no bajan el ticket de la tienda) | **88** |
| ofertas que cuentan de verdad | 3.967 |
