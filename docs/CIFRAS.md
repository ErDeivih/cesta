# Las cifras de la ultima ejecucion

**Ejecucion del 8 de octubre de 2026.** Este documento tiene un solo trabajo:
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
| productos del catalogo | **51.661** |
| grupos comparables | **8.725** |
| productos comparables por kg/l/m | **42.559** |
| productos con codigo de barras | **25.126** |

## Etiquetado y composicion

| | |
|---|---:|
| productos con algun sello | **11.761** |
| productos con certificado | **988** |
| productos con Nutri-Score | **8.478** |
| productos con tabla nutricional | **3.955** |
| productos con envase | **9.052** |

## Historico

    1.445.154 filas, 33 dias acumulados

## Por cadena, la ultima captura de cada una

| cadena | productos | errores | tiempo | fecha |
|---|---:|---:|---:|---|
| alcampo | 22.860 | 0 | 6.703 s | 2026-10-08 |
| carrefour | 16.175 | 1 | 5.608 s | 2026-10-08 |
| dia | 5.800 | 0 | 779 s | 2026-10-08 |
| mercadona | 4.208 | 0 | 103 s | 2026-10-08 |
| aldi | 2.618 | 0 | 88 s | 2026-10-08 |

## Promociones

| | |
|---|---:|
| productos con texto de promocion | 13.951 |
| **de tarjeta** (no bajan lo que pagas en caja) | **9.261** |
| **solo por internet** (no bajan el ticket de la tienda) | **166** |
| ofertas que cuentan de verdad | 4.524 |
