# Las cifras de la ultima ejecucion

**Ejecucion del 25 de septiembre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **52.701** |
| grupos comparables | **8.794** |
| productos comparables por kg/l/m | **42.470** |
| productos con codigo de barras | **25.414** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.805** |
| productos con certificado | **765** |
| productos con Nutri-Score | **8.415** |
| productos con tabla nutricional | **3.842** |
| productos con envase | **9.108** |

## Historico

    925.151 filas, 20 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.924 | 0 | 4.118 s | 2026-09-25 |
| carrefour | 16.473 | 4 | 3.409 s | 2026-09-25 |
| dia | 5.772 | 0 | 633 s | 2026-09-25 |
| mercadona | 4.318 | 0 | 97 s | 2026-09-25 |
| aldi | 2.214 | 0 | 97 s | 2026-09-25 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 7.963 |
| **de tarjeta** (no bajan lo que pagas en caja) | **575** |
| **solo por internet** (no bajan el ticket de la tienda) | **327** |
| ofertas que cuentan de verdad | 7.061 |
