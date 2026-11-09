# Las cifras de la ultima ejecucion

**Ejecucion del 9 de noviembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **53.182** |
| grupos comparables | **8.927** |
| productos comparables por kg/l/m | **43.394** |
| productos con codigo de barras | **25.631** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.560** |
| productos con certificado | **1.025** |
| productos con Nutri-Score | **8.505** |
| productos con tabla nutricional | **3.903** |
| productos con envase | **8.971** |

## Historico

    2.813.570 filas, 64 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.562 | 0 | 5.877 s | 2026-11-09 |
| carrefour | 16.794 | 1 | 3.041 s | 2026-11-09 |
| dia | 5.693 | 0 | 699 s | 2026-11-09 |
| mercadona | 4.290 | 0 | 105 s | 2026-11-09 |
| aldi | 2.761 | 0 | 96 s | 2026-11-09 |
| lidl | 82 | 0 | 5 s | 2026-11-09 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 6.226 |
| **de tarjeta** (no bajan lo que pagas en caja) | **729** |
| **solo por internet** (no bajan el ticket de la tienda) | **82** |
| ofertas que cuentan de verdad | 5.415 |
