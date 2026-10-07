# Las cifras de la ultima ejecucion

**Ejecucion del 7 de octubre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **51.915** |
| grupos comparables | **8.765** |
| productos comparables por kg/l/m | **42.565** |
| productos con codigo de barras | **25.297** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.851** |
| productos con certificado | **947** |
| productos con Nutri-Score | **8.492** |
| productos con tabla nutricional | **3.940** |
| productos con envase | **9.180** |

## Historico

    1.393.782 filas, 32 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 23.219 | 1 | 35.757 s | 2026-10-07 |
| carrefour | 16.198 | 1 | 32.145 s | 2026-10-07 |
| dia | 5.801 | 4 | 29.546 s | 2026-10-07 |
| mercadona | 4.385 | 4 | 28.983 s | 2026-10-07 |
| aldi | 2.502 | 6 | 28.970 s | 2026-10-07 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 8.107 |
| **de tarjeta** (no bajan lo que pagas en caja) | **567** |
| **solo por internet** (no bajan el ticket de la tienda) | **192** |
| ofertas que cuentan de verdad | 7.348 |
