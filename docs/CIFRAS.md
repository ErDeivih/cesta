# Las cifras de la ultima ejecucion

**Ejecucion del 28 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.699** |
| grupos comparables | **8.785** |
| productos comparables por kg/l/m | **42.454** |
| productos con codigo de barras | **25.482** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.787** |
| productos con certificado | **723** |
| productos con Nutri-Score | **8.426** |
| productos con tabla nutricional | **3.831** |
| productos con envase | **9.093** |

## Historico

    1.083.003 filas, 23 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.929 | 0 | 6.363 s | 2026-09-28 |
| carrefour | 16.560 | 4 | 3.680 s | 2026-09-28 |
| dia | 5.748 | 0 | 622 s | 2026-09-28 |
| mercadona | 4.332 | 0 | 120 s | 2026-09-28 |
| aldi | 2.130 | 0 | 115 s | 2026-09-28 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.908 |
| **de tarjeta** (no bajan lo que pagas en caja) | **586** |
| **solo por internet** (no bajan el ticket de la tienda) | **327** |
| ofertas que cuentan de verdad | 6.995 |
