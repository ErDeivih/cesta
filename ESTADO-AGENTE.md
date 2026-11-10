titulo: Cesta — superapp de compra, recetas y calorias
resumen: Sesión del 10/11 (tarde): **comparativa explicable, capturas a dos anchos y mini-informe**. La pantalla de comparación ahora lleva un desplegable «¿Cómo se calcula?» que dice qué suma el total de cada cadena, la fórmula del ahorro en cada caso (resta de totales con dos completas; suma producto a producto si no), cómo se comparan €/kg y €/l, y qué ofertas no se restan. Capturas del portfolio a **390 y 1280 px** de lista, comparativa y sugerencias, más la explicación abierta en escritorio (anchos comprobados con Pillow: 390×844 y 1280×900). Nuevo `docs/CASO-CESTA.md`: problema, datos (6 cadenas, 65 días, 2.866.370 filas, 53.072 productos, 39.164 comparables con precio), normalización (unidades, EAN, calidad 91,1 %), cálculo del ahorro con ejemplo real (6,78 € sobre 23,80 €, −28 %) y resultado. Suite final: **1.505 verdes, 813 saltadas, 0 rojos, 11 min 11 s**; web 273 vitest, 404 node, tipos/lint/build limpios (`sw 2026111016`).
estado: en-curso
tarea: comparativa explicable aplicada, capturas 390/1280 hechas y caso documentado; producción sirviendo el paquete nuevo
nivel: 2
siguiente: David decide las tres de `docs/decisiones-interfaz-2026-11-09.md` (duplicado de Carrefour con el mismo EAN, base de los porcentajes, contador vs lista en la receta), las de despliegue de §8 (móvil M1/M2/M3, respaldo programado, CESTA_REGISTRO, poda de gold) y la vara de Alcampo. Para el portfolio: decidir si se comparte el repositorio con un invitado o se publica una demo más allá de la tailnet.
bloqueado: las decisiones de interfaz, despliegue y vara de Alcampo; el mapeo automático de supers sigue en espera de decisión y de una exportación RGPD real.
fecha: 2026-11-10

## Bloqueo

**Motivo: la misma tanda ha llegado tres veces (17:24, 19:30 y 20:30) y las tres tareas ya estaban entregadas.**

- **Dónde me quedé:** las tres tareas están hechas y empujadas (`2346f43` comparativa explicable, `2c1640b` informe + capturas, `f5d61da` estado). `docs/CASO-CESTA.md` y las siete capturas existen; `master` = `origin/master`, árbol limpio y app viva. Verificado otra vez hoy a las 20:30.
- **Qué falta revisar:** si el mensaje es un reenvío automático o si pide algo distinto de lo entregado (otro formato, otras cifras, otro enfoque del informe). No hay nada a medias en el repo.
- **Qué necesito de David u otro chat:** confirmar si es reenvío (no hago nada más) o decir qué cambio concreto quiere; si el problema es que no ve los archivos, indicar desde dónde los consulta.
- **Siguiente paso concreto:** no re-ejecutar la tanda para no duplicar trabajo; si no hay respuesta, en la próxima revisión comparar el repo con `f5d61da` y, si sigue igual, mantener el bloqueo y seguir con otra tanda que no dependa de esto.

