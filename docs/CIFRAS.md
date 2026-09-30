# Las cifras de la ultima ejecucion

**Ejecucion del 30 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.467** |
| grupos comparables | **8.751** |
| productos comparables por kg/l/m | **42.319** |
| productos con codigo de barras | **25.399** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.747** |
| productos con certificado | **705** |
| productos con Nutri-Score | **8.406** |
| productos con tabla nutricional | **3.803** |
| productos con envase | **9.050** |

## Historico

    1.187.367 filas, 25 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.859 | 0 | 6.382 s | 2026-09-30 |
| carrefour | 16.522 | 4 | 3.358 s | 2026-09-30 |
| dia | 5.702 | 0 | 624 s | 2026-09-30 |
| mercadona | 4.325 | 0 | 95 s | 2026-09-30 |
| aldi | 2.059 | 0 | 63 s | 2026-09-30 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.815 |
| **de tarjeta** (no bajan lo que pagas en caja) | **571** |
| **solo por internet** (no bajan el ticket de la tienda) | **326** |
| ofertas que cuentan de verdad | 6.918 |
