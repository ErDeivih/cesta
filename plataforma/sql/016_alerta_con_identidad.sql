-- **016 · La alerta guarda de qué producto es, no solo dónde cayó.**
--
-- Hallazgo #9 de la revisión de fase 2: *«resolver cualquier consumidor aún ligado a ordinal»*.
--
-- `alerta.grupo_id` es un ORDINAL que el emparejador **renumera en cada pasada** -- lo dice el propio
-- código, como advertencia, en `api/main.py`, `api/cesta.py` y `api/catalogo.py`. Y `linea` y `favorito`
-- se protegieron de eso dándoles `producto_id`; **`alerta` se quedó con el ordinal y nada más.**
--
-- Medido antes de tocar nada: de las alertas de la base, **una**, creada el 10 de octubre de 2026, con
-- `salto_nombre` = «Leche entera Central Lechera Asturiana brik 1 l.» y `salto_texto` = «…1.24 EUR/l en
-- carrefour». **Y el miembro de carrefour de ese grupo hoy es «Leche entera President brik 1 l.»** -- el
-- grupo ya no es el que la alerta decía.
--
-- *Por eso esta migración NO rellena la fila que existe.* Rellenarla con lo que el grupo contiene hoy
-- escribiría un dato estable **equivocado**, que es peor que uno inestable. Esa fila se queda con `ean`
-- nulo y su `salto_nombre` como única ancla: no se pierde nada de lo que hoy funciona, y se deja de fingir
-- que la clave es estable.
--
-- **Y por qué `ean` y no `producto_id`.** `linea` y `favorito` usan `producto_id` porque fijan **una
-- cadena** («solo si se fijó una cadena», dice el esquema). *Una alerta de grupo no es de una cadena: es de
-- un producto en cualquiera* -- lo que vigila es **la mejor oferta de ese producto, mire donde mire** --.
-- Copiar `producto_id` sería **cambiarle la semántica a la alerta para arreglar el almacenamiento**.
-- El `ean` identifica el producto con independencia de en qué grupo haya caído y de en qué cadena se venda,
-- y el proyecto ya lo usa para eso (hay endpoint propio, `/api/ean/{codigo}`, y un resolutor,
-- `catalogo.por_ean`).

ALTER TABLE alerta ADD COLUMN IF NOT EXISTS ean text;

COMMENT ON COLUMN alerta.ean IS
    'GTIN del producto vigilado. **La identidad estable**, frente a `grupo_id`, que es un ordinal que el '
    'emparejador renumera en cada pasada. Nulo en las alertas creadas antes de la 016: *no se rellenan '
    'hacia atrás porque el grupo que tenían ya no dice con certeza de qué producto eran, y escribir un '
    'dato estable equivocado es peor que no tenerlo.*';

-- **Y no se toca la fila que existe.** Se dice aquí para que quien lea la migración no lo tome por un
-- olvido: es una decisión, y su motivo está medido.
