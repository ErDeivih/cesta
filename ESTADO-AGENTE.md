titulo: Cesta — superapp de compra, recetas y calorias
resumen: Sesión del 11/11: **portada del caso y criterios rematados**. `docs/CASO-CESTA.md` abre con una portada recalculable a mano: café, pack de 500 g a 8,19 € (16,38 €/kg), 1 kg → 2 packs; Mercadona 8,80 €, Alcampo 14,56 €, Carrefour/DIA 16,38 €, Aldi sin equivalente; variación 7,58 €. La cesta óptima ya muestra el ahorro frente a una sola tienda (Alcampo 17,46 € vs Alcampo+Aldi 15,00 € → 2,46 €) y los totales separan «Subtotal · faltan N» de «Cesta completa», con «la más barata» solo entre cadenas completas (7 de 8 no gana a 8 de 8; prueba existente). Capturas de comparativa, totales y óptima a 390/1280. Web 286 vitest, 404 node, tipos/lint y build limpios; suite Python 1.505 verdes / 813 saltadas / 0 rojos (3 min 16 s).
estado: en-curso
tarea: portada recalculable en el informe; cesta óptima y subtotales verificados y capturados
nivel: 2
siguiente: David decide las tres de `docs/decisiones-interfaz-2026-11-09.md` (duplicado de Carrefour con el mismo EAN, base de los porcentajes, contador vs lista en la receta), las de despliegue de §8 (móvil M1/M2/M3, respaldo programado, CESTA_REGISTRO, poda de gold) y la vara de Alcampo. Para el portfolio: decidir si se comparte el repositorio con un invitado o se publica una demo más allá de la tailnet.
bloqueado: las decisiones de interfaz, despliegue y vara de Alcampo; el mapeo automático de supers sigue en espera de decisión y de una exportación RGPD real.
fecha: 2026-11-11
