# WALL — cesta (superapp de compra)

Copiado del bloque 7 de `F:\EspacioCodigo\_flujo-dsh\MAPA-DE-OBJETIVOS.md` el **2026-11-05**.
Esta es la lista de casillas de la app de consumo. Se marca aquí al terminar, y no se para
hasta agotar el bloque.

**Objetivo final**: comparar precios de verdad entre cadenas y ayudar a comprar mejor.

**Terminado cuando**: digo mi compra habitual y me dice dónde comprar y qué me ahorro.

## Casillas

- [x] Ficha de producto (precio, €/kg, historial, alternativas). **Hecho 5/11** (ruta `/compra/productos/:fuente/:idFuente`; `logica/juicio.ts` con la ventana real y pruebas rojo→verde).
- [x] Comparar mi cesta. **Hecho 5/11** (`/compra/listas/:listaId/comparar`; corona solo la cadena que cuenta todas las líneas y no resta ofertas condicionadas).
- [ ] Favoritos, lista de la compra.
- [ ] Calculadora de calorías con pautas de salud.
- [ ] Recetas (establecidas y de usuario).
- [ ] Ofertas con su tipo y si exigen club del súper.
- [ ] Integración con las apps de los supermercados.
- [ ] Aprender de las listas: rellenar sola, recomendar, sugerir otro sitio.

## Hecho antes de esta lista (no estaba en el bloque, pero sostiene las casillas)

- [x] Sistema de diseño «Cesta App» aprobado por David (2026-11-05) e implementado en la app:
      38 colores en claro/oscuro, tipografía, espaciado, radios, sombras y movimiento 120/220 ms.
- [x] Portada nueva en `/` con esos tokens (buscador, «Mi cesta», «Se han movido», pasillos y
      barra Compra/Recetas/Calorías), con sus cuatro estados y sin textos de desarrollador (§8).
- [x] Ingesta del 5/11 cerrada sola y vigilada: 6 cadenas, gold `20261105-123941`, y
      `scripts/vigilar_ingesta.py` enganchado a `ejecutar.bat` (avisa solo si hay fallo).

## Notas de trabajo

- Orden acordado por David (2026-11-05): ficha de producto → comparar mi cesta → favoritos y
  lista → calculadora de calorías → recetas → ofertas con tipo/club → apps de supers →
  aprender de las listas.
- Lo que se puede enseñar ya: portada en `http://127.0.0.1:8080/`.
- Reglas: `DOCTRINA-CALIDAD.md` §8 en todas las pantallas, sin GitHub Actions, push selectivo,
  `data/` fuera de git y `resumen:` en `ESTADO-AGENTE.md`.
