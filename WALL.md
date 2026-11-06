# WALL — cesta (superapp de compra)

Copiado del bloque 7 de `F:\EspacioCodigo\_flujo-dsh\MAPA-DE-OBJETIVOS.md` el **2026-11-05**.
Esta es la lista de casillas de la app de consumo. Se marca aquí al terminar, y no se para
hasta agotar el bloque.

**Objetivo final**: comparar precios de verdad entre cadenas y ayudar a comprar mejor.

**Terminado cuando**: digo mi compra habitual y me dice dónde comprar y qué me ahorro.

## Casillas

- [x] Ficha de producto (precio, €/kg, historial, alternativas). **Hecho 5/11** (ruta `/compra/productos/:fuente/:idFuente`; `logica/juicio.ts` con la ventana real y pruebas rojo→verde).
- [x] Comparar mi cesta. **Hecho 5/11** (`/compra/listas/:listaId/comparar`; corona solo la cadena que cuenta todas las líneas y no resta ofertas condicionadas).
- [x] Favoritos, lista de la compra. **Hecho 5/11** (vista de lista con precio estimado y precio por línea; favoritos con rango real de historial).
- [x] Calculadora de calorías con pautas de salud. **Hecho 6/11** (pantalla de objetivo/comidas + `/calorias/pautas`: Mifflin + actividad, objetivo mantener/perder/ganar con su por qué, macros con rangos y pautas de fibra, azúcar, sal, agua, fruta/verdura y alcohol con fuente y enlace; suelo de seguridad y aviso médico; sin prescribir).
- [x] Recetas (establecidas y de usuario). **Hecho 5/11** (listado con recetario/archivadas y detalle con coste por ingrediente cuando hay precios; no hay semilla de recetas «establecidas» en la API).
- [x] Ofertas con su tipo y si exigen club del súper. **Hecho 6/11** (`/compra/ofertas` + `GET /api/ofertas`: tipo, condición y club; sin precio final inventado).
- [x] Integración con las apps de los supermercados. **Hecho 6/11, con límites**: no hay API de consumidor en las seis cadenas; la vía lícita es la importación manual (pegar lista/ticket) que ya existe, y la exportación RGPD la pide la persona. Sin credenciales ni login automatizado (`docs/INTEGRACION-APPS-SUPERS-2026-11-06.md`).
- [x] Aprender de las listas: rellenar sola, recomendar, sugerir otro sitio. **Hecho 6/11** («Rellenar de una vez» con previa y confirmación, «la siguiente» por el orden de la API, y comparar al lado; sin inventar frecuencias).

## Hecho antes de esta lista (no estaba en el bloque, pero sostiene las casillas)

- [x] Sistema de diseño «Cesta App» aprobado por David (2026-11-05) e implementado en la app:
      38 colores en claro/oscuro, tipografía, espaciado, radios, sombras y movimiento 120/220 ms.
- [x] Portada nueva en `/` con esos tokens (buscador, «Mi cesta», «Se han movido», pasillos y
      barra Compra/Recetas/Calorías), con sus cuatro estados y sin textos de desarrollador (§8).
- [x] Ingesta del 5/11 cerrada sola y vigilada: 6 cadenas, gold `20261105-123941`, y
      `scripts/vigilar_ingesta.py` enganchado a `ejecutar.bat` (avisa solo si hay fallo).

## Artboards **aprobados** por David (2026-11-05, 20:16)

Añadidos al canvas `designs/cesta-app` (10 tableros en total). David los valida **antes** de
implementar cada pantalla:

- [x] Lista de la compra (`Lista.dc.html`): productos con cantidad, precio estimado 10,70 €.
- [x] Favoritos (`Favoritos.dc.html`): 3 guardados, rango de su historial de 60/59 días.
- [x] Comparar mi cesta (`Comparar.dc.html`): Alcampo 7,19 € gana con 3 de 3; DIA 10,16 y
      Carrefour 10,97; Mercadona/Aldi/Lidl incompletos.
- [x] Recetas, listado (`Recetas.dc.html`): recetario y «mis recetas».
- [x] Receta y coste (`Receta.dc.html`): tortilla, 5,32 € (1,33 €/ración) con ingredientes.
- [x] Calorías (`Calorias.dc.html`): 1.075 de 2.200 kcal y las tres comidas del día.
- [x] Ofertas (`Ofertas.dc.html`): tipo y condición de club en 5 ofertas reales.
- [x] Tu perfil (`Perfil.dc.html`): cadena habitual, dieta, alérgenos, objetivo y avisos.

## Notas de trabajo

- Orden acordado por David (2026-11-05): ficha → comparar mi cesta → lista → favoritos →
  recetas → calorías → ofertas → perfil → apps de supers → aprender de las listas.
- Lo que se puede enseñar ya: portada en `http://127.0.0.1:8080/`.
- Reglas: `DOCTRINA-CALIDAD.md` §8 en todas las pantallas, sin GitHub Actions, push selectivo,
  `data/` fuera de git y `resumen:` en `ESTADO-AGENTE.md`.

## Verificación de ingesta del 06/11/2026

- [x] La tarea de Windows «Cesta diaria» está habilitada y su último resultado fue 0. Publicación de la pasada: `20261106-123403` (commit `d885a7f`).
- [x] La verificación y el vigilante pasaron 31 pruebas con datos sintéticos. Ante fallo, el vigilante genera el parte local y devuelve un código distinto de cero.
- [ ] Queda una comprobación independiente para detectar que el Programador de tareas nunca llegó a lanzar la ingesta. El vigilante actual corre al final de la propia tarea.
